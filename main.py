import os

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np
import shp_api
import datacube_api

# Constants and Configurations
CSV_FILE_PATH = 'data.csv'
SHP_FILE_PATH = 'shp/obec_0.shp'
COLUMN_NAME = 'Podiel poľnohosp. pôdy z celkovej plochy (%)'
NUM_CLASSES = 5
COLOR_MAP = plt.colormaps['viridis']
OUTPUT_FILE = 'mapa'
MAP_TITLE = 'Podiel Poľnohospodárskej Pôdy v Obciach Okresu'
LEGEND_TITLE = 'Legenda'

SHP_ZIP_URL = 'https://www.geoportal.sk/files/zbgis/na_stiahnutie/shp/ah_shp_0.zip'

# Border styles for the map
MUNICIPALITY_BORDER_COLOR = 'black'
MUNICIPALITY_BORDER_WIDTH = 1
DISTRICT_BORDER_COLOR = 'red'
DISTRICT_BORDER_WIDTH = 2

def load_data(shp_file_path):
    """
    Loads shapefile data.

    Args:
        shp_file_path (str): Path to the shapefile.

    Returns:
        GeoDataFrame: Shapefile data as a GeoDataFrame.

    Raises:
        IOError: If there is an error loading the data.
    """
    try:
        shp_data = gpd.read_file(shp_file_path)
    except Exception as e:
        raise IOError(f"Error loading data: {e}")
    return shp_data

def load_data_from_api(municipalities):
    """
    Loads data for given municipalities using the API.

    Args:
        municipalities (DataFrame): DataFrame with municipality names and codes.

    Returns:
        DataFrame: DataFrame containing the data for the municipalities.
    """
    municipalities_codes = municipalities['LAU2_CODE'].tolist()
    latest_year = datacube_api.get_latest_year()
    indicators = datacube_api.get_all_indicators()
    cities_data = datacube_api.get_land_data_cities_code(municipalities_codes)

    if cities_data is not None:
        cities_data[COLUMN_NAME] = (
            cities_data['Agricultural land in total in m2'] / cities_data['Total area of land of municipality-town in m2']) * 100
        return cities_data
    return None

def validate_data(merged_data, land_data):
    """
    Validates that all entries in the CSV are present in the merged data.

    Args:
        merged_data (GeoDataFrame): Merged data of shapefile and CSV.
        land_data (DataFrame): Original CSV data.

    Raises:
        ValueError: If there are missing municipalities in the merged data.
    """
    missing_data = set(land_data.index) - set(merged_data['LAU2_CODE'])
    if missing_data:
        raise ValueError(f"Missing SHP data for municipalities: {missing_data}")


def merge_datasets(shp_data, csv_data, district_name):
    """
    Merges shapefile and CSV data, filtering by the specified district.

    Args:
        shp_data (GeoDataFrame): Shapefile data.
        csv_data (DataFrame): CSV data.
        district_name (str): Name of the district to filter.

    Returns:
        GeoDataFrame: Merged and filtered data.
    """
    filtered_data = shp_data[shp_data['LAU1'] == district_name]
    merged_data = pd.merge(filtered_data, csv_data, left_on='LAU2_CODE', right_index=True)
    validate_data(merged_data, csv_data)
    return merged_data

def classify_data(merged_data, column_name, num_classes):
    """
    Classifies data into quantiles.

    Args:
        merged_data (GeoDataFrame): Data to be classified.
        column_name (str): Column name to classify.
        num_classes (int): Number of classes for classification.

    Returns:
        Series: Classified data.
        Series: Quantile values.
    """
    quantile_list = np.linspace(0, 1, num_classes+1)
    quantiles = merged_data[column_name].quantile(quantile_list)
    classified_data = pd.cut(merged_data[column_name], quantiles, labels=False, include_lowest=True)
    return classified_data, quantiles

def create_legend_elements(num_classes, quantiles, cmap):
    color_samples = np.linspace(0, 1, num_classes)
    colors = [cmap(sample) for sample in color_samples]
    quantile_labels = [f'{quantiles.iloc[i]:.1f} - {quantiles.iloc[i + 1]:.1f}%' for i in range(num_classes)]
    legend_elements = [plt.Rectangle((0, 0), 1, 1, color=c, label=l) for c, l in zip(colors, quantile_labels)]
    legend_elements.append(
        plt.Line2D([0], [0], color=MUNICIPALITY_BORDER_COLOR, lw=MUNICIPALITY_BORDER_WIDTH, label='Hranica obce'))
    legend_elements.append(
        plt.Line2D([0], [0], color=DISTRICT_BORDER_COLOR, lw=DISTRICT_BORDER_WIDTH, label='Hranica okresu'))
    return legend_elements

def setup_plot(district_name):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.set_title(MAP_TITLE+' '+district_name)
    ax.set_axis_off()
    return fig, ax

def plot_map(merged_data, classified_data, quantiles, district_name, num_classes):
    """
    Plots the map with the classified data.

    Args:
        merged_data (GeoDataFrame): Merged shapefile and CSV data.
        classified_data (Series): Classified data.
        quantiles (Series): Quantile values.
    """
    fig, ax = setup_plot(district_name)
    cmap = COLOR_MAP
    merged_data.assign(cl=classified_data).plot(column='cl', cmap=cmap, linewidth=MUNICIPALITY_BORDER_WIDTH, ax=ax,
                                                edgecolor=MUNICIPALITY_BORDER_COLOR)
    add_map_features(merged_data, ax)
    ax.legend(handles=create_legend_elements(num_classes, quantiles, cmap), title=LEGEND_TITLE, loc='upper left')
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()

def add_map_features(merged_data, ax):
    """
    Adds additional features to the map, such as municipality names and district boundary.

    Args:
        merged_data (GeoDataFrame): Merged shapefile and CSV data.
        ax (matplotlib.axes.Axes): Matplotlib axes object to plot on.
    """
    text_properties = {
        'fontsize': 7, 'color': 'white', 'ha': 'center', 'va': 'center', 'weight': 'bold',
        'path_effects': [PathEffects.withStroke(linewidth=1.5, foreground='black')]
    }
    for idx, row in merged_data.iterrows():
        representative_point = row['geometry'].representative_point()
        ax.annotate(text=row['NM4']+' '+f'{row[COLUMN_NAME]:.1f}%', xy=(representative_point.x, representative_point.y), **text_properties)
    merged_data.dissolve().boundary.plot(ax=ax, edgecolor='red', linewidth=2)

# Main Execution
shp_api.download_and_unzip_shp(SHP_ZIP_URL)
shp_data = load_data(SHP_FILE_PATH)

districts = shp_data.drop_duplicates(subset=['LAU1'])[['LAU1', 'LAU1_CODE']]

if districts is not None:
    print("Available Districts: \n", districts['LAU1'].to_string())
    for index_district, selected_district in districts.iterrows():
        selected_district_string = selected_district['LAU1']
        OUTPUT_FILE = 'maps/map_' + selected_district_string + '.png'
        if os.path.exists(OUTPUT_FILE):
            continue
        print("Vybraný okres: ", selected_district_string)
        municipalities = shp_data[shp_data['LAU1_CODE'] == selected_district['LAU1_CODE']]

        if municipalities is not None and 'NM4' in municipalities:
            print("Obce okresu:\n", municipalities['NM4'].to_string())
            municipalities_land_data = load_data_from_api(municipalities)

            if municipalities_land_data is not None:
                merged_data = merge_datasets(shp_data, municipalities_land_data, selected_district_string)

                num_classes = min(merged_data.shape[0], NUM_CLASSES)
                classified_data, quantiles = classify_data(merged_data, COLUMN_NAME, num_classes)

                plot_map(merged_data, classified_data, quantiles, selected_district_string, num_classes)