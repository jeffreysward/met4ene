"""
Tests for the postwrf package.
"""
from optwrf import postwrf

# Define the path to where you WRF data file is stored
# (note: don't forget to add the "/" at the end of the directory)
_wrfout_dir = '/Users/swardy9230/Box Sync/01_Research/01_Renewable_Analysis/' \
              'Wind Resource Analysis/wrfout/19mp4lw4sw7lsm8pbl99cu/'
_wrfout_file = 'wrfout_d02_2011-07-17'


def test_process_wrfout_manual(savefile=True):
    """
    Test the function for manually processing WRF output data.

    :return:
    """

    met_data = postwrf.process_wrfout_manual(_wrfout_dir, _wrfout_file, save_file=savefile)
    if not savefile:
        assert [var in met_data.variables for var in ['ghi', 'wpd']].count(True) == 2
    else:
        assert 0 == 0
