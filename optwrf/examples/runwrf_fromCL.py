"""
Run WRF using command line arguments
====================================

This example provides the method for using the optwrf.runwrf module
to run the WRF model for a either a random or specified set of parameters.
It's a good idea to run this inside a tmux session. Otherwise, your terminal
window will be tied up for quite some time.
-------------------------------------------------------------------------------
Use this command for randomly generating a set of parameters:

python runwrf_fromCL.py -s 'Jan 15 2011' -e 'Jan 16 2011' -b 'ERA' -d 1 -p True

Use this command to use parameter defaults (see broader documentation):

python runwrf_fromCL.py -s 'Jan 15 2011' -e 'Jan 16 2011' -b 'ERA' -d 1

There are numerous other arguments that you can inclue to control how WRF runs:
-s : string specifying the start date of the simulation.
-e : string specifying the end date of the simulaiton.
-par : path to a yaml file containing WRF
       physics parameterization options.
-p : specify True or False for random physics parameter generation.
-su : path to a yaml file containing your directory setup info.
-b : string specifying your boundary condition data source
     (only 'ERA' is supportted currently).
-d : integer specifying the number of domains you want to run [1, 2, 3].
-t : path to your namelist template directory.
-mp : string identifying a microphysics parametization scheme in your
      parameterization yaml file.
-lw : string identifying a longwave radiation parameterization scheme in
      your paramterization yaml file.
-sw : string identifying a shortwave radiation parameterization scheme in
      your paramterization yaml file.
-lsm : string identifying a land surface model parameterization scheme in
      your paramterization yaml file.
-pbl : string identifying a planetary boundary layer parameterization scheme in
      your paramterization yaml file.
-cu : string identifying a cumulus parameterization scheme in
      your paramterization yaml file.

By default, timeout of WPS, Real, and WRF have been disabled in this script.

"""

from argparse import ArgumentParser
from optwrf.wrfparams import flexible_generate
from optwrf.runwrf import WRFModel


# Define command line input options
arg = ArgumentParser()
arg.add_argument('-s', help="Start Date", type=str)
arg.add_argument('-e', help="End Date", type=str)
arg.add_argument('-par', help="Parameterizations Yaml File", type=str)
arg.add_argument('-p', help="Generate Params?", type=bool)
arg.add_argument('-su', help="Setup Yaml File", type=str)
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

# Set the params yaml file to user specification, or default to params.yml.
if args.par is not None:
    in_yaml = args.par
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

# Set the setup yaml file to user specification, or default to dirpath.yml.
if args.su is not None:
    setup_yaml = args.su
else:
    setup_yaml = 'dirpath.yml'

# Set the number of domains to user specification, or default to a single domain.
if args.d is not None and args.d > 0:
    n_domains = int(args.d)
else:
    n_domains = 3

# Format the forecast start/end and determine the total time.
start_date = args.s
end_date = args.e

# Generate a parameter combination of the 6 core parameters if the user has specified this option.
# Otherwise, use specified input parameters and use defaults for the remaining paramters.
param_ids = flexible_generate(generate_params, mp, lw, sw, lsm, pbl, cu, in_yaml)

wrf_sim = WRFModel(param_ids, start_date, end_date,
                   bc_data=bc_data, n_domains=n_domains, setup_yaml=setup_yaml)

# Next, get boundary condition data for the simulation
# ERA is the only supported data type right now.
vtable_sfx = wrf_sim.get_bc_data()

# Setup the working directory to run the simulation
wrf_sim.wrfdir_setup(vtable_sfx)

# Prepare the namelist
wrf_sim.prepare_namelists()

# Run WPS
success = wrf_sim.run_wps(disable_timeout=True)
print(f'WPS ran successfully? {success}')

# RUN REAL
if success:
    success = wrf_sim.run_real(disable_timeout=True)
    print(f'Real ran successfully? {success}')

# RUN WRF
if success:
    success, runtime = wrf_sim.run_wrf(disable_timeout=True)
    print(f'WRF ran successfully? {success}')
