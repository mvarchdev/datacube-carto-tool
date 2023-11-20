import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np
import requests
import zipfile
import io
import ckan_api
import shp_api
import datacube_api

# Constants and Configurations
CSV_FILE_PATH = 'data.csv'
SHP_FILE_PATH = 'shp/obec_0.shp'
COLUMN_NAME = 'Podiel poľnohosp. pôdy z celkovej plochy (%)'
NUM_CLASSES = 5
COLOR_MAP = plt.colormaps['viridis']
OUTPUT_FILE = 'mapa.png'
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

def load_data_from_api(municipality_name, municipality_code=None):
    """
    Loads data for a given municipality using the API.

    Args:
        municipality_name (str): Name of the municipality.

    Returns:
        DataFrame: DataFrame containing the data for the municipality.
    """
    api_data = datacube_api.get_land_data(municipality_name, municipality_code)
    if api_data is not None:
        calc_data = {'Podiel poľnohosp. pôdy z celkovej plochy (%)': (
            (api_data['Agricultural land in total in m2'] / api_data['Total area of land of municipality-town in m2']) * 100
        )}
        calculated_data_df = pd.DataFrame(data=calc_data, index=[municipality_name])
        return calculated_data_df
    return None

def validate_data(merged_data, csv_data):
    """
    Validates that all entries in the CSV are present in the merged data.

    Args:
        merged_data (GeoDataFrame): Merged data of shapefile and CSV.
        csv_data (DataFrame): Original CSV data.

    Raises:
        ValueError: If there are missing municipalities in the merged data.
    """
    missing_data = set(csv_data.index) - set(merged_data['NM4'])
    if missing_data:
        raise ValueError(f"Missing data for municipalities: {missing_data}")


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
    merged_data = pd.merge(filtered_data, csv_data, left_on='NM4', right_index=True)
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
    quantile_labels = [f'{quantiles.iloc[i]:.1f}% - {quantiles.iloc[i + 1]:.1f}' for i in range(num_classes)]
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

def plot_map(merged_data, classified_data, quantiles, district_name):
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
    ax.legend(handles=create_legend_elements(NUM_CLASSES, quantiles, cmap), title=LEGEND_TITLE, loc='upper left')
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', pad_inches=0.1)

def add_map_features(merged_data, ax):
    """
    Adds additional features to the map, such as municipality names and district boundary.

    Args:
        merged_data (GeoDataFrame): Merged shapefile and CSV data.
        ax (matplotlib.axes.Axes): Matplotlib axes object to plot on.
    """
    text_properties = {
        'fontsize': 9, 'color': 'white', 'ha': 'center', 'va': 'center', 'weight': 'bold',
        'path_effects': [PathEffects.withStroke(linewidth=1.5, foreground='black')]
    }
    for idx, row in merged_data.iterrows():
        representative_point = row['geometry'].representative_point()
        ax.annotate(text=row['NM4'], xy=(representative_point.x, representative_point.y), **text_properties)
    merged_data.dissolve().boundary.plot(ax=ax, edgecolor='red', linewidth=2)


# Main Execution
districts = ckan_api.fetch_districts()
shp_api.download_and_unzip_shp(SHP_ZIP_URL)
if districts is not None:
    print("Available Districts: \n", districts['countyName'].to_string())
    try:
        district_index = 75#int(input("Enter desired district index: "))
        selected_district = districts.iloc[district_index]
        selected_district_string = selected_district['countyName']
        print("Vybraný okres: ", selected_district_string)

        municipalities = ckan_api.fetch_municipalities(selected_district['objectId'])
        if municipalities is not None:
            print("Obce okresu:\n",municipalities['municipalityName'].to_string())
            municipalities_land_data = pd.DataFrame()
            for index, municipality in municipalities.iterrows():
                municipalityName = municipality['municipalityName']
                municipalityCode = municipality['municipalityCode']
                muni_land_data = load_data_from_api(municipalityName, municipalityCode)
                municipalities_land_data = pd.concat([municipalities_land_data, muni_land_data])

            shp_data = load_data(SHP_FILE_PATH)

            merged_data = merge_datasets(shp_data, municipalities_land_data, selected_district_string)
            classified_data, quantiles = classify_data(merged_data, COLUMN_NAME, NUM_CLASSES)
            plot_map(merged_data, classified_data, quantiles, selected_district_string)

    except ValueError as e:
        print("Invalid input. Please enter a valid integer:", e)
    except IndexError as e:
        print("Index out of range. Please enter a valid district index:", e)
