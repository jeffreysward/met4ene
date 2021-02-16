"""
This example shows you how to flexibly process a wrfout file.
For this example, we process the wrfout data for offshore wind.

"""
import optwrf.postwrf as postwrf


# Identify which variables you want to extract from the wrfout file.
query_variables = [
            'U',                # x-wind component
            'V',                # y-wind component
            'W',                # z-wind component
            'height_agl',       # Height above ground level
            'wspd',             # Wind speed
            'wdir',             # Wind direction
            'UST',              # U* IN SIMILARITY THEORY (friction velocity)
            'HFX_FORCE',        # SCM ideal surface sensible heat flux
            'PBLH',             # PBL Height
            'EL_PBL',           # Length scale from PBL
            'theta',            # Potential Temperature
            'theta_e',          # Equivalent Potential Temperature
            'tv',               # Virtual Temperature
        ]

# Specify which directory the wrfout file is located in
# Note that the processed file will automaticlly be saved to this directory.
# Also the directory MUST have a "/" at the end!!!!!
DIR_WRFOUT = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2020-06-05_28mp4lw4sw2lsm5pbl1cu/'

# Identify the WRF output file to be processed
wrfout_file = 'wrfout_d03_2020-06-05_00:00:00'

# Call the function that processes the data
postwrf.process_wrfout_flexible(DIR_WRFOUT, wrfout_file, query_variables,
                                outfile_prefix='ow_buoy_')
