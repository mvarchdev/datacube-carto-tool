import requests
import pandas as pd
import logging
from joblib import Memory

import common_tools

# Set up caching
cache_dir = './cache'
memory = Memory(cache_dir, verbose=0)


class DatacubeAPI:
    BASE_URL = "https://data.statistics.sk/api/v2/"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatacubeAPI, cls).__new__(cls)
            logging.basicConfig(level=logging.INFO)
            cls._instance.session = requests.Session()
        return cls._instance

    @staticmethod
    def get_instance():
        """
        Static access method.
        """
        if DatacubeAPI._instance is None:
            DatacubeAPI()
        return DatacubeAPI._instance

    @staticmethod
    def _make_request(endpoint, params=None):
        try:
            response = DatacubeAPI._instance.session.get(f"{DatacubeAPI.BASE_URL}{endpoint}", params=params)
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
    def _parse_json_response(response):
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
        print(endpoint)
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
    """
    Fetches data for each indicator for a specified city and year.

    :param city_code: The code of the city.
    :param year: The year for which data is requested.
    :param indicators: A dictionary of indicators to fetch data for.
    :return: A dictionary with indicator names as keys and corresponding data as values.
    """
    data = {}
    api = DatacubeAPI.get_instance()
    indicator_string_list = ','.join(indicators)
    response = api.get_data('pl5001rr', cities_string, year, indicator_string_list)
    print(response)
    exit()
    if not response and 'value' in response:
        return None
    return data

@memory.cache
def get_land_data_cities_code(cities_code_list, city_codes=None):
    if not cities_code_list:
        logging.error("City codes are required")
        return None

    # Convert cities to a list if it's a pandas DataFrame or Series
    if isinstance(cities_code_list, (pd.DataFrame, pd.Series)):
        cities = cities_code_list.tolist()

    cities_string = ','.join(cities_code_list)
    latest_year = get_latest_year()
    if not latest_year:
        logging.error("Failed to fetch the latest year")
        return None

    indicators = get_all_indicators()
    if not indicators:
        logging.error("Failed to fetch indicators")
        return None

    cities_data = get_land_data(cities_string, latest_year, indicators)
    if cities_data:
        required_columns = ['Agricultural land in total in m2', 'Total area of land of municipality-town in m2']
        if not all(column in cities_data for column in required_columns):
            logging.error("Failed to fetch required columns for all cities land data")
            return None
    else:
        logging.error("Failed to fetch land data for all cities")
        return None

    print(cities_data)
    exit()

    return pd.DataFrame(cities_data, index=['City'])


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

test_data = get_land_data_cities_name(['Michalovce','Sobrance'])
print(test_data.to_string())