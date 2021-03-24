"""
This example shows you how to reprocess the raw wrfout files
 and delete the raw wrfout files.
"""
import os
import optwrf.postwrf as postwrf

# Compile a list of wrfout directories
rootdir = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/optwrf_output/ow_exp002/'
# for wrfdir in os.scandir(rootdir):
#     if wrfdir.is_dir():
#         print(wrfdir.path)
#         try:
#             # Run the process_wrfout_manual() function in each directory
#             postwrf.process_wrfout_manual(wrfdir.path, 'wrfout_d01.nc', start=None, end=None, save_file=True)
#             # Delete the old wrfout file
#             CMD_RM = 'rm %s'
#             os.system(CMD_RM % (wrfdir.path + 'wrfout_d01.nc'))
#         except:
#             pass

wrfdir = rootdir + '2011-01-01_19mp4lw1sw7lsm8pbl1cu/'
try:
    # Run the process_wrfout_manual() function in each directory
    postwrf.process_wrfout_manual(wrfdir, 'wrfout_d01.nc', start=None, end=None, save_file=True)
    # Delete the old wrfout file
    CMD_RM = 'rm %s'
    # os.system(CMD_RM % (wrfdir + 'wrfout_d01.nc'))
except:
    pass
