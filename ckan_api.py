import requests
import zipfile
import io
import pandas as pd

CKAN_DISTRICT_URL = 'https://data.gov.sk/api/action/datastore_search?resource_id=1829233e-53f3-4c6a-9ad6-b27f33ec7550'
CKAN_MUNICIPALITY_BASE_URL = 'https://data.gov.sk/api/action/datastore_search_sql'

def fetch_districts():
    """
    Fetch district list from CKAN.

    Returns:
        DataFrame: District data.
    """
    try:
        response = requests.get(CKAN_DISTRICT_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return pd.DataFrame(data['result']['records'])
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError:
        print("Invalid JSON response")


# Function to fetch municipalities for a selected district
def fetch_municipalities(district_id):
    """
    Fetch municipalities for a selected district.

    Args:
        district_id (str): The district identifier.

    Returns:
        DataFrame: Municipality data.
    """
    try:
        params = {
            'sql': f"SELECT * from \"15262453-4a0f-4cce-a9e4-7709e135e4b8\" WHERE \"countyIdentifier\"='{district_id}'"}
        response = requests.get(CKAN_MUNICIPALITY_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data['result']['records'])
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError:
        print("Invalid JSON response")
