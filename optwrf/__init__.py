import os
import sys

# Figure out where the module is located
dir_path = os.path.dirname(os.path.realpath(__file__))
# Add the data directory to the python path
sys.path.append(dir_path + '/data')
