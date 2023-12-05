import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np
from flask import jsonify

import shp_api
import datacube_api

logging.basicConfig(level=logging.INFO)

# Constants and Configurations
CSV_FILE_PATH = 'data.csv'
SHP_FILE_PATH = 'shp/obec_0.shp'
COLUMN_NAME = 'Podiel poľnohosp. pôdy z celkovej plochy (%)'
NUM_CLASSES = 5
COLOR_MAP = plt.colormaps['viridis']
OUTPUT_DIR = Path('maps')
MAP_TITLE = 'Podiel Poľnohospodárskej Pôdy v Obciach Okresu'
LEGEND_TITLE = 'Legenda'

SHP_ZIP_URL = 'https://www.geoportal.sk/files/zbgis/na_stiahnutie/shp/ah_shp_0.zip'

# Border styles for the map
MUNICIPALITY_BORDER_COLOR = 'black'
MUNICIPALITY_BORDER_WIDTH = 1
DISTRICT_BORDER_COLOR = 'red'
DISTRICT_BORDER_WIDTH = 2

def load_shp_data(shp_file_path):
    try:
        shp_data = gpd.read_file(shp_file_path)
    except Exception as e:
        raise IOError(f"Error loading data: {e}")
    return shp_data

def get_land_data_api(municipalities):
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
    missing_data = set(land_data.index) - set(merged_data['LAU2_CODE'])
    if missing_data:
        raise ValueError(f"Missing SHP data for municipalities: {missing_data}")


def merge_datasets(shp_data, csv_data, district_code):
    filtered_data = shp_data[shp_data['LAU1_CODE'] == district_code]
    merged_data = pd.merge(filtered_data, csv_data, left_on='LAU2_CODE', right_index=True)
    validate_data(merged_data, csv_data)
    return merged_data

def classify_data(merged_data, column_name, num_classes):
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

def plot_map(merged_data, classified_data, quantiles, district_name, num_classes, output_file):
    fig, ax = setup_plot(district_name)
    cmap = COLOR_MAP
    merged_data.assign(cl=classified_data).plot(column='cl', cmap=cmap, linewidth=MUNICIPALITY_BORDER_WIDTH, ax=ax,
                                                edgecolor=MUNICIPALITY_BORDER_COLOR)
    add_map_features(merged_data, ax)
    ax.legend(handles=create_legend_elements(num_classes, quantiles, cmap), title=LEGEND_TITLE, loc='upper left')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()

def add_map_features(merged_data, ax):
    text_properties = {
        'fontsize': 7, 'color': 'white', 'ha': 'center', 'va': 'center', 'weight': 'bold',
        'path_effects': [PathEffects.withStroke(linewidth=1.5, foreground='black')]
    }
    for idx, row in merged_data.iterrows():
        representative_point = row['geometry'].representative_point()
        ax.annotate(text=row['NM4']+' '+f'{row[COLUMN_NAME]:.1f}%', xy=(representative_point.x, representative_point.y), **text_properties)
    merged_data.dissolve().boundary.plot(ax=ax, edgecolor='red', linewidth=2)

def main():
    """
    Main execution function for the script.
    """
    try:
        shp_api.download_and_unzip_shp(SHP_ZIP_URL)
    except Exception as e:
        logging.error(f"Failed to download or unzip shapefile: {e}")
        return

    try:
        shp_data = load_shp_data(SHP_FILE_PATH)
    except IOError as e:
        logging.error(f"Failed to load shapefile data: {e}")
        return

    process_districts(shp_data)

def process_districts(shp_data):
    """
    Processes each district found in the shapefile data.

    Args:
        shp_data (GeoDataFrame): Loaded shapefile data.
    """
    districts = shp_data.drop_duplicates(subset=['LAU1'])[['LAU1', 'LAU1_CODE']]


    OUTPUT_DIR.mkdir(exist_ok=True)

    if districts is not None:
        for _, selected_district in districts.iterrows():
            process_district(selected_district)

def _process_district(shp_data, selected_district):
    """
    Processes a single district.

    Args:
        shp_data (GeoDataFrame): Loaded shapefile data.
        selected_district (pd.Series): Data for the selected district.
    """
    selected_district_name = selected_district['LAU1']
    selected_district_code = selected_district['LAU1_CODE']
    output_file = OUTPUT_DIR / f'map_{selected_district_code}.png'

    if output_file.exists():
        logging.info(f"Map for {selected_district_name} already exists. Skipping.")
        return

    logging.info(f"Processing District: {selected_district_name}")
    municipalities = shp_data[shp_data['LAU1_CODE'] == selected_district_code]

    if municipalities is not None and 'NM4' in municipalities:
        municipalities_land_data = get_land_data_api(municipalities)

        if municipalities_land_data is not None:
            try:
                merged_data = merge_datasets(shp_data, municipalities_land_data, selected_district_code)
                num_classes = min(merged_data.shape[0], NUM_CLASSES)
                classified_data, quantiles = classify_data(merged_data, COLUMN_NAME, num_classes)
                plot_map(merged_data, classified_data, quantiles, selected_district_name, num_classes, output_file)
            except ValueError as e:
                logging.error(f"Data validation error: {e}")

shp_data = load_shp_data(SHP_FILE_PATH)

# Function to get the list of all districts
def get_district_list():
    try:
        districts = shp_data[['LAU1', 'LAU1_CODE']].drop_duplicates()
        return [(row['LAU1'], row['LAU1_CODE']) for index, row in districts.iterrows()]
    except Exception as e:
        logging.error(f"Failed to load shapefile data for district list: {e}")
        return []

# Function to process a specific district
def process_district(district_code):
    try:
        selected_district = shp_data[shp_data['LAU1_CODE'] == district_code].iloc[0]
        _process_district(shp_data, selected_district)
    except Exception as e:
        logging.error(f"Failed to process district {district_code}: {e}")

# Function to get land data for a specific district
def get_land_data(district_code):
    try:
        municipalities = shp_data[shp_data['LAU1_CODE'] == district_code]
        municipalities_land_data = get_land_data_api(municipalities)
        municipalities_land_data = municipalities_land_data.replace({np.nan: None})
        return municipalities_land_data.to_html() if municipalities_land_data is not None else "<p>No data available.</p>"
    except Exception as e:
        error_message = f"Failed to get land data for district {district_code}: {e}"
        logging.error(error_message)
        raise Exception(error_message)  # Raise to send the error back to Flask

if __name__ == '__main__':
    main()

