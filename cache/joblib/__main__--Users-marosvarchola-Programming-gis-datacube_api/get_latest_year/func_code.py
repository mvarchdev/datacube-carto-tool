# first line: 119
@memory.cache
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
