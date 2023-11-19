import requests
import pandas as pd

class DatacubeAPI:
    BASE_URL = "https://data.statistics.sk/api/v2/"

    def __init__(self):
        pass

    def _make_request(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as err:
            print(f"HTTP Error: {err}")
            return None

    def get_table_overview(self, language='en'):
        endpoint = f"collection?lang={language}"
        response = self._make_request(endpoint)
        return response.json() if response else None

    def get_table_dimensions(self, cube_code, dim_code, language='en'):
        endpoint = f"dimension/{cube_code}/{dim_code}?lang={language}"
        response = self._make_request(endpoint)
        return response.json() if response else None

    def get_data(self, cube_code, region_code, year, indicator_code, lang='en', file_type='json'):
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
        if 'dimension' in json_stat and dimension in json_stat['dimension']:
            details = json_stat['dimension'][dimension]
            return {
                'label': details.get('label', ''),
                'note': details.get('note', ''),
                'categories': details['category'].get('label', {})
            }
        return None

def search_city_get_code(api, city_name):
    nuts15_details = api.get_table_dimensions('pl5001rr', 'nuts15', 'sk')
    for code, name in nuts15_details['category']['label'].items():
        if city_name.lower() in name.lower():
            return code
    return None

def get_latest_year(api):
    year_details = api.get_table_dimensions('pl5001rr', 'pl5001rr_rok', 'en')
    latest_year = max(year_details['category']['index'], key=int)
    return latest_year

def get_all_indicators(api):
    indicators = api.get_table_dimensions('pl5001rr', 'pl5001rr_ukaz', 'en')
    return indicators['category']['label']

def get_city_data(api, city_code, year, indicators):
    data = {}
    for indicator_code, indicator_name in indicators.items():
        response = api.get_data('pl5001rr', city_code, year, indicator_code)
        if response and 'value' in response:
            data[indicator_name] = response['value'][0]
    return data

# Initialize API
api = DatacubeAPI()

# Search for city and get code
city_name = "Sobrance"  # Replace with the city you are searching for
city_code = search_city_get_code(api, city_name)

if city_code:
    # Get the latest year and all indicators
    latest_year = get_latest_year(api)
    indicators = get_all_indicators(api)

    # Get data for each indicator for the specific city and latest year
    city_data = get_city_data(api, city_code, latest_year, indicators)

    # Convert to Pandas DataFrame
    df = pd.DataFrame([city_data], index=[city_name])
    print(df.iloc[0])
else:
    print(f"City '{city_name}' not found.")