import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np

# Constants and configurations
CSV_FILE_PATH = 'data.csv'
SHP_FILE_PATH = 'shp/obec_0.shp'
DISTRICT_NAME = 'Banská Štiavnica'
COLUMN_NAME = 'Podiel poľnohosp. pôdy z celkovej plochy (%)'
NUM_CLASSES = 5
COLOR_MAP = plt.colormaps['viridis']
OUTPUT_FILE = 'mapa.png'

def load_data(csv_file_path, shp_file_path):
    """
    Loads CSV and shapefile data.

    Args:
        csv_file_path (str): Path to the CSV file.
        shp_file_path (str): Path to the shapefile.

    Returns:
        tuple: Tuple containing the CSV data as a pandas DataFrame and shapefile data as a GeoDataFrame.

    Raises:
        IOError: If there is an error loading the data.
    """
    try:
        csv_data = pd.read_csv(csv_file_path)
        shp_data = gpd.read_file(shp_file_path)
    except Exception as e:
        raise IOError(f"Error loading data: {e}")
    return csv_data, shp_data

def validate_data(merged_data, csv_data):
    """
    Validates that all entries in the CSV are present in the merged data.

    Args:
        merged_data (GeoDataFrame): Merged data of shapefile and CSV.
        csv_data (DataFrame): Original CSV data.

    Raises:
        ValueError: If there are missing municipalities in the merged data.
    """
    missing_data = set(csv_data['Obec']) - set(merged_data['NM4'])
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
    merged_data = pd.merge(filtered_data, csv_data, left_on='NM4', right_on='Obec')
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
    """
    Creates legend elements for the map.
    """
    # Use linspace to get evenly spaced values in [0, 1] for color sampling
    color_samples = np.linspace(0, 1, num_classes)

    # Sample colors from the colormap using these normalized values
    colors = [cmap(sample) for sample in color_samples]

    # Create quantile labels
    quantile_labels = [f'{quantiles.iloc[i]:.1f} - {quantiles.iloc[i + 1]:.1f}' for i in range(num_classes)]

    # Create legend elements
    legend_elements = [plt.Rectangle((0, 0), 1, 1, color=c, label=l) for c, l in zip(colors, quantile_labels)]
    legend_elements.extend([
        plt.Line2D([0], [0], color='black', lw=1, label='Hranica obce'),
        plt.Line2D([0], [0], color='red', lw=2, label='Hranica okresu')
    ])
    return legend_elements

def plot_map(merged_data, classified_data, quantiles, num_classes):
    """
    Plots the map with the classified data.

    Args:
        merged_data (GeoDataFrame): Merged shapefile and CSV data.
        classified_data (Series): Classified data.
        quantiles (Series): Quantile values.
        num_classes (Number): Number of classes
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    cmap = COLOR_MAP
    merged_data.assign(cl=classified_data).plot(column='cl', cmap=cmap, linewidth=0.8, ax=ax, edgecolor='0.8')

    add_map_features(merged_data, ax)

    ax.legend(handles=create_legend_elements(num_classes, quantiles, cmap), title="Legenda", loc='upper left')
    ax.set_title('Podiel poľnohospodárskej pôdy v obciach okresu Banská Štiavnica')
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig('mapa.png', dpi=300, bbox_inches='tight', pad_inches=0.1)

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

    district_boundary = merged_data.dissolve().boundary
    district_boundary.plot(ax=ax, edgecolor='red', linewidth=2)

# Main execution
csv_data, shp_data = load_data(CSV_FILE_PATH, SHP_FILE_PATH)
merged_data = merge_datasets(shp_data, csv_data, DISTRICT_NAME)
classified_data, quantiles = classify_data(merged_data, COLUMN_NAME, NUM_CLASSES)
plot_map(merged_data, classified_data, quantiles, NUM_CLASSES)