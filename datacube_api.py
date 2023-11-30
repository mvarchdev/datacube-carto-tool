import requests
import pandas as pd
import logging
from joblib import Memory

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set up caching
cache_dir = './cache'
memory = Memory(cache_dir, verbose=0)

class DatacubeAPI:
    BASE_URL = "https://data.statistics.sk/api/v2/"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.session = requests.Session()
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls.__new__(cls)

    @classmethod
    def _make_request(cls, endpoint: str, params: dict = None) -> requests.Response:
        try:
            response = cls.get_instance().session.get(f"{cls.BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response
        except requests.ConnectionError as e:
            logging.error(f"Connection error: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error: {e}")
        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
        return None

    @staticmethod
    def _parse_json_response(response: requests.Response) -> dict:
        try:
            return response.json()
        except ValueError:
            logging.error("Invalid JSON response")
            return None

    def get_table_overview(self, language='en'):
        """
        Retrieves an overview of all tables available in the API.

        :param language: Language code for the API response.
        :return: JSON response containing the overview.
        """
        endpoint = f"collection?lang={language}"
        response = self._make_request(endpoint)
        return response.json() if response else None

    def get_table_dimensions(self, cube_code, dim_code, language='en'):
        """
        Fetches details about specific dimensions of a table.

        :param cube_code: The code of the data cube.
        :param dim_code: The code of the dimension.
        :param language: Language code for the API response.
        :return: JSON response containing the dimension details.
        """
        endpoint = f"dimension/{cube_code}/{dim_code}?lang={language}"
        response = self._make_request(endpoint)
        return response.json() if response else None

    def get_data(self, cube_code, region_code, year, indicator_code, lang='en', file_type='json'):
        endpoint = f"dataset/{cube_code}/{region_code}/{year}/{indicator_code}?lang={lang}&type={file_type}"
        response = self._make_request(endpoint)
        if response:
            if file_type == 'json':
                return self._parse_json_response(response)
            elif file_type == 'csv':
                return pd.read_csv(response.url)
        return None

    def get_dimension_info(self, json_stat, dimension):
        """
        Extracts detailed information about a particular dimension from a dataset.

        :param json_stat: The JSON-stat formatted dataset.
        :param dimension: The dimension for which information is requested.
        :return: A dictionary with details about the dimension.
        """
        if 'dimension' in json_stat and dimension in json_stat['dimension']:
            details = json_stat['dimension'][dimension]
            return {
                'label': details.get('label', ''),
                'note': details.get('note', ''),
                'categories': details['category'].get('label', {})
            }
        return None

@memory.cache
def search_city_get_code(city_name):
    """
    Searches for a city by name and returns its code.

    :param city_name: The name of the city to search for.
    :return: The code of the city or None if not found.
    """
    if not city_name:
        logging.error("City name is required")
        return None
    try:
        api = DatacubeAPI.get_instance()
        nuts15_details = api.get_table_dimensions('pl5001rr', 'nuts15', 'en')
        for code, name in nuts15_details['category']['label'].items():
            if city_name.lower() == name.lower():
                return code
    except Exception as e:
        logging.error(f"Error searching city code: {e}")
    return None


@memory.cache
def get_latest_year():
    """
    Retrieves the most recent year available in the dataset.

    :return: The latest year as a string.
    """
    try:
        api = DatacubeAPI.get_instance()
        year_details = api.get_table_dimensions('pl5001rr', 'pl5001rr_rok', 'en')
        return max(year_details['category']['index'], key=int)
    except Exception as e:
        logging.error(f"Error fetching latest year: {e}")
    return None


@memory.cache
def get_all_indicators():
    """
    Retrieves all available indicators from the dataset.

    :return: A dictionary of indicators.
    """
    try:
        api = DatacubeAPI.get_instance()
        indicators = api.get_table_dimensions('pl5001rr', 'pl5001rr_ukaz', 'en')
        return indicators['category']['label']
    except Exception as e:
        logging.error(f"Error fetching indicators: {e}")
    return {}


@memory.cache
def get_land_data(cities_string, year, indicators):
    data = {}
    api = DatacubeAPI.get_instance()
    indicator_string_list = ','.join(indicators)
    response = api.get_data('pl5001rr', cities_string, year, indicator_string_list)

    if not response or 'value' not in response:
        logging.error("Invalid or empty response in get_land_data")
        return None

    values = response['value']
    dimensions = response['dimension']
    indicator_info = dimensions.get('pl5001rr_ukaz', {})
    city_info = dimensions.get('nuts15', {})

    city_codes = city_info.get('category', {}).get('index', {})
    indicator_codes = indicator_info.get('category', {}).get('index', {})
    city_labels = city_info.get('category', {}).get('label', {})
    indicator_labels = indicator_info.get('category', {}).get('label', {})

    if not city_codes or not indicator_codes:
        logging.error("Missing or empty indicators or city information in the response")
        return None

    for i, val in enumerate(values):
        if val == "None":  # Skip missing values
            continue

        city_index = i // len(indicator_codes)
        indicator_index = i % len(indicator_codes)

        city_code = list(city_codes.keys())[city_index]
        indicator_code = list(indicator_codes.keys())[indicator_index]

        city_name = city_labels.get(city_code, "Unknown City")
        indicator_name = indicator_labels.get(indicator_code, "Unknown Indicator")

        if city_code not in data:
            data[city_code] = {'City Name': city_name}

        data[city_code][indicator_name] = val

    return data

@memory.cache
def get_land_data_cities_code(cities_code_list):
    if not cities_code_list:
        logging.error("City codes are required")
        return None

    if isinstance(cities_code_list, (pd.DataFrame, pd.Series)):
        cities_code_list = cities_code_list.tolist()

    cities_string = ','.join(cities_code_list)
    latest_year = get_latest_year()
    if not latest_year:
        logging.error("Failed to fetch the latest year")
        return None

    indicators = get_all_indicators()
    if not indicators:
        logging.error("Failed to fetch indicators")
        return None

    cities_data = get_land_data(cities_string, latest_year, list(indicators.keys()))
    if not cities_data:
        logging.error("Failed to fetch land data for all cities")
        return None

    df = pd.DataFrame.from_dict(cities_data, orient='index').reset_index().rename(columns={'index': 'City Code'})
    required_columns = ['City Name'] + list(indicators.values())
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"Missing required columns: {missing_columns}")
        return None

    return df.set_index('City Code')

@memory.cache
def get_city_codes(cities_name_list):
    if not cities_name_list:
        logging.error("City names are required")
        return None

    # Convert cities to a list if it's a pandas DataFrame or Series
    if isinstance(cities_name_list, (pd.DataFrame, pd.Series)):
        cities = cities_name_list.tolist()

    all_city_codes = []

    for city_name in cities_name_list:
        city_code = search_city_get_code(city_name)
        if not city_code:
            logging.warning(f"City code for city '{city_name}' not found. Skipping.")
            continue

        all_city_codes.append(city_code)

    if len(all_city_codes) != len(cities_name_list):
        logging.error("Failed to fetch city codes for all cities")
        return None

    return all_city_codes

@memory.cache
def get_land_data_cities_name(cities_name_list):
    city_codes_list = get_city_codes(cities_name_list)
    return get_land_data_cities_code(city_codes_list)
