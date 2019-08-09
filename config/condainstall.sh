# Install Anaconda
wget "https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh"
chmod +x Anaconda3-2019.07-Linux-x86_64.sh
./Anaconda3-2019.07-Linux-x86_64.sh
source ~/.bashrc 

# Initialize anaconda
conda init tcsh
source ~/.tcshrc 

# Create conda environment 
conda create --name met4ene python=2.7

# Install necessary packages
pip install PyYAML
pip install requests
