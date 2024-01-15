import sys
import requests
import zipfile
import io
import os
import logging

SHP_ZIP_URL = 'https://www.geoportal.sk/files/zbgis/na_stiahnutie/shp/ah_shp_0.zip'

# Configure logger for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a console handler and set the level to INFO
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

def download_and_unzip_shp(url=SHP_ZIP_URL, output_dir='shp/'):
    """
    Downloads and unzips a Shapefile (SHP) from a given URL.

    If the Shapefile is already downloaded, it uses the cached version.
    The function handles possible errors during download and extraction.

    Args:
        url (str): URL of the zip file containing the Shapefile.
        output_dir (str): Directory to store the extracted Shapefile.
                          Defaults to 'shp/'.

    Raises:
        requests.RequestException: If there is an issue with the HTTP request.
        zipfile.BadZipFile: If the downloaded file is not a valid ZIP file.
        Exception: For any other issues during download or extraction.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        zip_file_name = os.path.basename(url)
        local_zip_path = os.path.join(output_dir, zip_file_name)

        # Download the file only if it's not already downloaded
        if not os.path.isfile(local_zip_path):
            logger.info(f"Downloading Shapefile from '{url}'")
            response = requests.get(url)
            response.raise_for_status()

            with open(local_zip_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Shapefile ZIP downloaded to {local_zip_path}")

        # Extract the ZIP file
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
            logger.info(f"Shapefile extracted to {output_dir}")

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
    except zipfile.BadZipFile:
        logger.error("Downloaded file is not a valid ZIP file.")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
