import sys

import requests
import zipfile
import io
import os
import logging

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

def download_and_unzip_shp(url, output_dir='shp/'):
    """
    Download and unzip SHP files, with caching and enhanced error handling.

    Args:
        url (str): URL of the zip file.
        output_dir (str): Output directory to store extracted files.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        zip_file_name = url.split('/')[-1]
        local_zip_path = os.path.join(output_dir, zip_file_name)

        # Check if the file already exists
        if not os.path.exists(local_zip_path):
            logger.info(f"Downloading Shapefile from url '{url}'")
            response = requests.get(url)
            response.raise_for_status()
            with open(local_zip_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Shapefile ZIP download completed. Saved to {local_zip_path}")

            with zipfile.ZipFile(local_zip_path) as z:
                z.extractall(path=output_dir)
                logger.info(f"Shapefile extracted to {output_dir}")
        else:
            logger.info(f"Shapefile already downloaded. Using cached version at {output_dir}")

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
    except zipfile.BadZipFile:
        logger.error("Error: Bad ZIP file.")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
