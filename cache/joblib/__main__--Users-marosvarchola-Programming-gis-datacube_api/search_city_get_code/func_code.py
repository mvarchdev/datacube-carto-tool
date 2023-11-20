# first line: 102
@memory.cache
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
