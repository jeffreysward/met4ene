#!/bin/tcsh
# This script assumes that you already have Anaconda installed and in your path.

# Remove any potential existing directory
conda env remove --name runwrf

# Create runwrf conda environment
conda create --name runwrf python=3.7

# Install necessary packages
pip install -U pytest
pip install PyYAML
pip install requests
pip install jupyter
conda install -c conda-forge xarray cartopy wrf-python pynio pseudonetcdf
pip install siphon
conda install -c conda-forge nco
conda install -c conda-forge ncl
echo "Install pvlib-python by cloning the repository and running (pip install -e .) in the directory with setup.py"
echo "Install optwrf by cloning the met4ene repository and running (pip install -e .) in the met4ene/optwrf/ directory"