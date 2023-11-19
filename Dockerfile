# Use an official osgeo/gdal image
FROM osgeo/gdal:ubuntu-small-latest

# Set the working directory in the container
WORKDIR /usr/src/app

# Install Python and other necessary system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-dev \
        build-essential

# Install Python packages
RUN pip3 install --no-cache-dir wheel \
    && pip3 install --no-cache-dir geopandas matplotlib matplotlib_scalebar mapclassify requests

# Run python script when the container launches
CMD ["python3", "./bs.py"]
