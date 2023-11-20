# first line: 134
@memory.cache
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
