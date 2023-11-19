import requests
import pandas as pd
import logging
from functools import lru_cache

class DatacubeAPI:
    """
    A Python API wrapper for the Statistical Office of the Slovak Republic's DATAcube database.
    """

    BASE_URL = "https://data.statistics.sk/api/v2/"

    def __init__(self):
        """
        Initializes the DatacubeAPI instance.
        """
        logging.basicConfig(level=logging.INFO)
        self.session = requests.Session()

    @lru_cache(maxsize=128)
    def _make_request(self, endpoint, params=None):
        """
        Makes a cached HTTP GET request to a specified endpoint.

        :param endpoint: The API endpoint to query.
        :param params: Optional parameters for the request.
        :return: The response object or None in case of an error.
        """
        try:
            response = self.session.get(f"{self.BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as err:
            logging.error(f"Request error: {err}")
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
        """
        Queries specific data from the database.

        :param cube_code: The code of the data cube.
        :param region_code: The code of the region.
        :param year: The year for which data is requested.
        :param indicator_code: The code of the indicator.
        :param lang: Language code for the API response.
        :param file_type: The file format of the response.
        :return: The requested data in the specified format.
        """
        endpoint = f"dataset/{cube_code}/{region_code}/{year}/{indicator_code}?lang={lang}&type={file_type}"
        response = self._make_request(endpoint)
        if response:
            if file_type == 'json':
                return response.json()
            elif file_type == 'csv':
                return pd.read_csv(response.url)
            # Add handlers for other file types as needed
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

@lru_cache(maxsize=128)
def search_city_get_code(api, city_name):
    """
    Searches for a city by name and returns its code.

    :param api: The DatacubeAPI instance.
    :param city_name: The name of the city to search for.
    :return: The code of the city or None if not found.
    """
    try:
        nuts15_details = api.get_table_dimensions('pl5001rr', 'nuts15', 'en')
        for code, name in nuts15_details['category']['label'].items():
            if city_name.lower() == name.lower():
                return code
    except Exception as e:
        logging.error(f"Error searching city code: {e}")
    return None

@lru_cache(maxsize=32)
def get_latest_year(api):
    """
    Retrieves the most recent year available in the dataset.

    :param api: The DatacubeAPI instance.
    :return: The latest year as a string.
    """
    try:
        year_details = api.get_table_dimensions('pl5001rr', 'pl5001rr_rok', 'en')
        return max(year_details['category']['index'], key=int)
    except Exception as e:
        logging.error(f"Error fetching latest year: {e}")
    return None

@lru_cache(maxsize=32)
def get_all_indicators(api):
    """
    Retrieves all available indicators from the dataset.

    :param api: The DatacubeAPI instance.
    :return: A dictionary of indicators.
    """
    try:
        indicators = api.get_table_dimensions('pl5001rr', 'pl5001rr_ukaz', 'en')
        return indicators['category']['label']
    except Exception as e:
        logging.error(f"Error fetching indicators: {e}")
    return {}

def get_city_data(api, city_code, year, indicators):
    """
    Fetches data for each indicator for a specified city and year.

    :param api: The DatacubeAPI instance.
    :param city_code: The code of the city.
    :param year: The year for which data is requested.
    :param indicators: A dictionary of indicators to fetch data for.
    :return: A dictionary with indicator names as keys and corresponding data as values.
    """
    data = {}
    for indicator_code, indicator_name in indicators.items():
        response = api.get_data('pl5001rr', city_code, year, indicator_code)
        if response and 'value' in response:
            data[indicator_name] = response['value'][0]
    return data

def get_land_data(city_name):
    """
    The main function to execute the API wrapper functionality.
    """
    # Initialize API
    api = DatacubeAPI()

    # Search for city and get code
    city_code = search_city_get_code(api, city_name)

    if city_code:
        # Get the latest year and all indicators
        latest_year = get_latest_year(api)
        indicators = get_all_indicators(api)

        # Get data for each indicator for the specific city and latest year
        city_data = get_city_data(api, city_code, latest_year, indicators)

        # Convert to Pandas DataFrame
        df = pd.DataFrame([city_data], index=[city_name])
        return df
    else:
        print(f"City '{city_name}' not found.")
        return None

print(get_land_data('Sobrance').iloc[0])