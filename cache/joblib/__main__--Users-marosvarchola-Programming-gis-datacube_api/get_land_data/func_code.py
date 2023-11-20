# first line: 166
@memory.cache
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
