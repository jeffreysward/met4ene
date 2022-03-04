#!/bin/tcsh
# Install Anaconda
wget "https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh"
chmod +x Anaconda3-2019.07-Linux-x86_64.sh
./Anaconda3-2019.07-Linux-x86_64.sh
# source ~/.bashrc 

# Initialize anaconda
conda init tcsh
source ~/.tcshrc 

# Create runwrf conda environment
conda env create -f magma_optwrf_env.yml

# Remind myself to install 
echo "Install pvlib-python by cloning the repository and running (pip install -e .) in the directory with setup.py"
echo "Install optwrf by cloning the met4ene repository and running (pip install -e .) in the met4ene/optwrf/ directory"
echo "Navigate to ~/conda/envs/optwrf/bin and run 'rm mpi*' (if you fail to do this, WRF will not work properly as it was compiled with executables on the HPC system rather than the one's installed by conda.)"