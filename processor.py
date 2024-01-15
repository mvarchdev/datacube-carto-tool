import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np

import shp_api
import datacube_api

logging.basicConfig(level=logging.INFO)

# Constants and Configurations
SHP_FILE_PATH = 'shp/obec_0.shp'
RATIO_COLUMN_LABEL = 'Podiel poľnohosp. pôdy z celkovej plochy (%)'
RATIO_COLUMN_CODE = 'ALRAT'
NUM_CLASSES_DEFAULT = 5
COLOR_MAP_DEFAULT = 'viridis'
OUTPUT_DIR = Path('maps')
MAP_TITLE = 'Podiel Poľnohospodárskej Pôdy v Obciach Okresu'
LEGEND_TITLE = 'Legenda'

# Border styles for the map
MUNICIPALITY_BORDER_COLOR = 'black'
MUNICIPALITY_BORDER_WIDTH = 1
DISTRICT_BORDER_COLOR = 'red'
DISTRICT_BORDER_WIDTH = 2

shp_api.download_and_unzip_shp()


def load_shp_data(shp_file_path=SHP_FILE_PATH):
    try:
        shp_data = gpd.read_file(shp_file_path)
    except Exception as e:
        raise IOError(f"Error loading data: {e}")
    return shp_data


shp_data = load_shp_data()


def get_land_data_api(municipalities):
    municipalities_codes = municipalities['LAU2_CODE'].tolist()
    cities_data = datacube_api.get_land_data_cities_code(municipalities_codes)

    if cities_data is not None:
        cities_data[RATIO_COLUMN_LABEL] = (cities_data['U14020'] / cities_data['U14010']) * 100
        return cities_data
    return None


def validate_data(merged_data, land_data):
    missing_data = set(land_data.index) - set(merged_data['LAU2_CODE'])
    if missing_data:
        raise ValueError(f"Missing SHP data for municipalities: {missing_data}")


def merge_datasets(land_data, district_code):
    filtered_data = shp_data[shp_data['LAU1_CODE'] == district_code]
    merged_data = pd.merge(filtered_data, land_data, left_on='LAU2_CODE', right_index=True)
    validate_data(merged_data, land_data)
    return merged_data


def classify_data(merged_data, column_name, num_classes):
    quantile_list = np.linspace(0, 1, num_classes + 1)
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
    ax.set_title(MAP_TITLE + ' ' + district_name)
    ax.set_axis_off()
    return fig, ax


def plot_map(merged_data, classified_data, quantiles, district_name, num_classes, output_file, color_map):
    fig, ax = setup_plot(district_name)
    merged_data.assign(cl=classified_data).plot(column='cl', cmap=color_map, linewidth=MUNICIPALITY_BORDER_WIDTH, ax=ax,
                                                edgecolor=MUNICIPALITY_BORDER_COLOR)
    add_map_features(merged_data, ax)
    ax.legend(handles=create_legend_elements(num_classes, quantiles, color_map), title=LEGEND_TITLE, loc='upper left')
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
        ax.annotate(text=row['NM4'], xy=(representative_point.x, representative_point.y), **text_properties)
    merged_data.dissolve().boundary.plot(ax=ax, edgecolor='red', linewidth=2)


def _process_district(selected_district, num_classes, color_palette_name):
    """
    Processes a single district.

    Args:
        selected_district (pd.Series): Data for the selected district.
    """
    selected_district_name = selected_district['LAU1']
    selected_district_code = selected_district['LAU1_CODE']
    output_file = OUTPUT_DIR / f'map_{selected_district_code}_{num_classes}_{color_palette_name}.png'

    if output_file.exists():
        logging.info(f"Map for {selected_district_name} already exists. Skipping.")
        return

    logging.info(f"Processing District: {selected_district_name}")
    municipalities = shp_data[shp_data['LAU1_CODE'] == selected_district_code]

    if municipalities is not None and 'NM4' in municipalities:
        municipalities_land_data = get_land_data_api(municipalities)

        if municipalities_land_data is not None:
            try:
                merged_data = merge_datasets(municipalities_land_data, selected_district_code)
                num_classes = min(merged_data.shape[0], num_classes)
                classified_data, quantiles = classify_data(merged_data, RATIO_COLUMN_LABEL, num_classes)
                color_map = plt.colormaps[color_palette_name]
                plot_map(merged_data, classified_data, quantiles, selected_district_name, num_classes, output_file,
                         color_map)
            except ValueError as e:
                logging.error(f"Data validation error: {e}")


# Function to get the list of all districts
def get_district_list():
    try:
        districts = shp_data[['LAU1', 'LAU1_CODE']].drop_duplicates()
        return [(row['LAU1'], row['LAU1_CODE']) for index, row in districts.iterrows()]
    except Exception as e:
        logging.error(f"Failed to load shapefile data for district list: {e}")
        return []


# Function to process a specific district
def process_district(district_code, num_classes=NUM_CLASSES_DEFAULT, color_palette_name=COLOR_MAP_DEFAULT):
    try:
        selected_district = shp_data[shp_data['LAU1_CODE'] == district_code].iloc[0]
        _process_district(selected_district, num_classes, color_palette_name)
    except Exception as e:
        logging.error(f"Failed to process district {district_code}: {e}")


# Function to get land data for a specific district
def get_land_data(district_code):
    try:
        municipalities = shp_data[shp_data['LAU1_CODE'] == district_code]
        municipalities_land_data = get_land_data_api(municipalities)

        # Fetch the indicator labels
        indicators = datacube_api.get_all_indicators()
        # Add custom column's code and label to the indicators dictionary
        indicators[RATIO_COLUMN_CODE] = RATIO_COLUMN_LABEL

        if municipalities_land_data is not None:
            # Rename columns using the format `{indicator_label} ({indicator_code})`
            municipalities_land_data.rename(columns={code: f"{label} ({code})" for code, label in indicators.items()}, inplace=True)

            return municipalities_land_data.to_html()
        else:
            return "<p>No data available.</p>"
    except Exception as e:
        error_message = f"Failed to get land data for district {district_code}: {e}"
        logging.error(error_message)
        raise Exception(error_message)  # Raise to send the error back to Flask
