import requests
import pandas as pd
from joblib import Memory

# Set up caching
cache_dir = './cache'  # You can change this to a different directory if needed
memory = Memory(cache_dir, verbose=0)

CKAN_DISTRICT_URL = 'https://data.gov.sk/api/action/datastore_search?resource_id=1829233e-53f3-4c6a-9ad6-b27f33ec7550'
CKAN_MUNICIPALITY_BASE_URL = 'https://data.gov.sk/api/action/datastore_search_sql'

@memory.cache
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

@memory.cache
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
            'sql': f"""
SELECT 
    Main."municipalityCode", 
    Main."municipalityName", 
    Main."validFrom"
FROM 
    "15262453-4a0f-4cce-a9e4-7709e135e4b8" Main
INNER JOIN 
    (
    SELECT 
        "municipalityCode", 
        MAX("validFrom") AS newest_valid_from
    FROM 
        "15262453-4a0f-4cce-a9e4-7709e135e4b8"
    WHERE 
        "countyIdentifier" = '{district_id}' 
        AND "municipalityCode" LIKE 'SK%'
    GROUP BY 
        "municipalityCode"
    ) AS Latest
ON 
    Main."municipalityCode" = Latest."municipalityCode" 
    AND Main."validFrom" = Latest.newest_valid_from
WHERE 
    Main."countyIdentifier" = '{district_id}'
    AND Main."municipalityCode" LIKE 'SK%'
"""
        }
        response = requests.get(CKAN_MUNICIPALITY_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data['result']['records'])
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError:
        print("Invalid JSON response")
