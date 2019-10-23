#!/usr/bin/python

from argparse import ArgumentParser
from datetime import datetime
from wrfparams import flexible_generate, write_param_csv
import runwrf as rw
import linuxhelper as lh


# Define command line input options
arg = ArgumentParser()
arg.add_argument('-s', help="Start Date", type=str)
arg.add_argument('-e', help="End Date", type=str)
arg.add_argument('-y', help="Parameterizations Yaml File", type=str)
arg.add_argument('-p', help="Generate Params?", type=bool)
arg.add_argument('-b', help="Boundary Conditon Data Source", type=str)
arg.add_argument('-d', help="Max Domains", type=int)
arg.add_argument('-t', help="Namelist Template Directory", type=str)
arg.add_argument('-mp', help="Microphysics scheme", type=str)
arg.add_argument('-lw', help="Longwave radiation scheme", type=str)
arg.add_argument('-sw', help="Shortwave radiation scheme", type=str)
arg.add_argument('-lsm', help="Land surface model", type=str)
arg.add_argument('-pbl', help="Planetary boundary layer scheme", type=str)
arg.add_argument('-cu', help="Cumulus scheme", type=str)
args = arg.parse_args()
bc_data = args.b
generate_params = args.p
template_dir = args.t
# Set the input yaml file to user specification, or default to params.yml.
if args.y is not None:
    in_yaml = args.y
else:
    in_yaml = 'params.yml'
if args.mp is not None: mp = args.mp
else: mp = None
if args.lw is not None: lw = args.lw
else: lw = None
if args.sw is not None: sw = args.sw
else: sw = None
if args.lsm is not None: lsm = args.lsm
else: lsm = None
if args.pbl is not None: pbl = args.pbl
else: pbl = None
if args.cu is not None: cu = args.cu
else: cu = None
# Set the number of domains to user specification, or default to a single domain.
if args.d is not None and args.d > 0:
    MAX_DOMAINS = int(args.d)
else:
    MAX_DOMAINS = 3

# Set parameters here that should be set automatically eventually
remove_DIR_DATA = False

# Format the forecast start/end and determine the total time.
forecast_start = datetime.strptime(args.s, '%b %d %Y')
forecast_end = datetime.strptime(args.e, '%b %d %Y')
delt = forecast_end - forecast_start
print('Forecast starting on: {}'.format(forecast_start))
print('Forecast ending on: {}'.format(forecast_end))

# Generate a parameter combination of the 6 core parameters if the user has specified this option.
# Otherwise, use specified input parameters and use defaults for the remaining paramters.
param_ids, paramstr = flexible_generate(generate_params, mp, lw, sw, lsm, pbl, cu, in_yaml='params.yml')

# Write parameter combinations to CSV
# (if you would like to restart this, you must manually delete this CSV)
write_param_csv(param_ids)

# Next, get boundary condition data for the simulation
# ERA is the only supported data type right now.
vtable_sfx = rw.get_bc_data(paramstr, bc_data, template_dir, forecast_start, delt, remove_DIR_DATA)

# Setup the working directory to run the simulation
rw.wrfdir_setup(paramstr, forecast_start, bc_data, template_dir, vtable_sfx)

# Prepare the namelist
rw.prepare_namelists(paramstr, param_ids, forecast_start, forecast_end, delt,
                     bc_data, template_dir, MAX_DOMAINS)

# RUN WPS
rw.run_wps(paramstr, forecast_start, bc_data, template_dir)

# RUN REAL
rw.run_real(paramstr, forecast_start, bc_data, template_dir)

# RUN WRF
rw.run_wrf(paramstr, forecast_start, bc_data, template_dir, MAX_DOMAINS)
