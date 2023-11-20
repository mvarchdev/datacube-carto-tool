# first line: 12
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
