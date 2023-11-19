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

    def get_table_dimensions(self, cube_code, dim_code, language='sk'):
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

# Usage Example
api = DatacubeAPI()
table_overview = api.get_table_overview()

# Get dimension details
dimension_info = api.get_table_dimensions('pl5001rr', 'pl5001rr_ukaz')

# Get specific data
data = api.get_data('pl5001rr', 'SK010', '2021', 'U14020')

# Get dimension information from a dataset
dataset_info = api.get_dimension_info(data, 'pl5001rr_ukaz')

# Print or process the data as needed
print(dataset_info)