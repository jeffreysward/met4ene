"""
This example shows you how to flexibly process a wrfout file.
For this example, we process the wrfout data for offshore wind.

"""
import optwrf.postwrf as postwrf


#

# Identify which variables you want to extract from the wrfout file.
query_variables = [
        'POWER',
        'height_agl',
        'wspd',
        'wdir',
    ]

# Specify which directory the wrfout file is located in
# (Note that the processed file will automaticlly be saved to this directory).
DIR_WRFOUT = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2010-07-01_19mp4lw4sw7lsm8pbl99cu/'

# Identify the WRF output file to be processed
wrfout_file = 'wrfout_d03_2010-07-01_00:00:00'

# Call the function that processes the data
postwrf.process_wrfout_flexible(DIR_WRFOUT, wrfout_file, query_variables,
                                outfile_prefix='offshorewind_')
