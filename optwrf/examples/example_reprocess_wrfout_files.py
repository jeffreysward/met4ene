"""
This example shows you how to reprocess the raw wrfout files
 and delete the raw wrfout files.
"""
import os
import fnmatch
import optwrf.postwrf as postwrf


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


# Compile a list of wrfout directories
rootdir = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/optwrf_output/optwrf_ensembles/'
# rootdir = '/Users/jsward/Documents/wrf_output/test/'
for wrfdir in os.scandir(rootdir):
    if wrfdir.is_dir():
        print(wrfdir.path)
        # Determine the name of the wrfout file
        wrffile = find('wrfout_d01*', wrfdir.path)
        if not wrffile:
            continue
        for file in wrffile:
            filestr = str(file.split('/')[-1])
            print(filestr)
            if filestr != 'wrfout_processed_d01.nc':
                try:
                    # Run the process_wrfout_manual() function in each directory
                    postwrf.process_wrfout_manual(wrfdir.path + '/', filestr,
                                                  start=None, end=None, save_file=True)
                    # Delete the old wrfout file(s)
                    if os.path.exists(wrfdir.path + '/' + 'processed_' + filestr):
                        CMD_RM = 'rm %s'
                        os.system(CMD_RM % (wrfdir.path + '/' + 'wrfout_*'))
                except KeyError:
                    pass
