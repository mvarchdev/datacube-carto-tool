# first line: 30
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
            'sql': f"SELECT * from \"15262453-4a0f-4cce-a9e4-7709e135e4b8\" WHERE \"countyIdentifier\"='{district_id}'"}
        response = requests.get(CKAN_MUNICIPALITY_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data['result']['records'])
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError:
        print("Invalid JSON response")
