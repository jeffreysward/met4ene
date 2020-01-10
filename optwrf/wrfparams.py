"""
Generates sets of WRF physics parameters, finds corresponding numeric identifies,
and writes the numeric paramter options to a CSV.
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues/Wishlist:
- It would be better if I could read in the parameters from the in_yaml
file only once, but I'm not sure how variables across different
functions in the same module work.

"""

import csv
import os
import random
import yaml

import sys


def generate(in_yaml='params.yml'):
    """
    Generates a random set of parameters.

    Parameters:
    ----------


    Returns:
    ----------

    """
    print(sys.path)
    with open(in_yaml, 'r') as params_file:
        try:
            params = yaml.safe_load(params_file)

        except yaml.YAMLError as exc:
            print(exc)

    mp = params.get("microphysics")
    lw = params.get("lw radiation")
    sw = params.get("sw radiation")
    lsm = params.get("land surface")
    pbl = params.get("PBL")
    clo = params.get("cumulus")

    param_opts = [mp, lw, sw, lsm, pbl, clo]

    param_list = []
    for opt in param_opts:
        param_choice = random.choice(list(opt.keys()))
        param_list.append(str(param_choice))

    return param_list


def name2num(in_yaml='params.yml', use_defaults=True, mp_in="morrison2mom", lw_in="rrtm", sw_in="dudia",
             lsm_in="noah", pbl_in="myj", clo_in="grell-freitas"):
    """
    Maps the name of the parameterization,
    which is defined generally by the name of the individual or
    institution that designed the scheme, to the namelist.input value.
    The default value of these parameterization schemes is set by those that
    were originally used by ICF in the study over NYC.

    Parameters:
    ----------


    Returns:
    ----------

    """

    with open(in_yaml, 'r') as params_file:
        try:
            params = yaml.safe_load(params_file)

            mp = params.get("microphysics")
            lw = params.get("lw radiation")
            sw = params.get("sw radiation")
            lsm = params.get("land surface")
            pbl = params.get("PBL")
            clo = params.get("cumulus")

            if not use_defaults and mp_in is "None":
                id_mp = None
            else:
                id_mp = mp.get(mp_in)
            if not use_defaults and lw_in is "None":
                id_lw = None
            else:
                id_lw = lw.get(lw_in)
            if not use_defaults and sw_in is "None":
                id_sw = None
            else:
                id_sw = sw.get(sw_in)
            if not use_defaults and lsm_in is "None":
                id_lsm = None
            else:
                id_lsm = lsm.get(lsm_in)
            if not use_defaults and pbl_in is "None":
                id_pbl = None
            else:
                id_pbl = pbl.get(pbl_in)
            if not use_defaults and clo_in is "None":
                id_clo = None
            else:
                id_clo = clo.get(clo_in)

            param_ids = [id_mp, id_lw, id_sw, id_lsm, id_pbl, id_clo]

        except yaml.YAMLError as exc:
            print(exc)
            param_ids = []

    return param_ids


def combine(lst1, lst2):
    """


    Parameters:
    ----------


    Returns:
    ----------

    """

    out_list = []
    for i in range(0, len(lst1)):
        if lst1[i] is None and lst2[i] is None:
            out_list.append(None)
        elif lst1[i] is None:
            out_list.append(lst2[i])
        elif lst2[i] is None:
            out_list.append(lst1[i])
    return out_list


def filldefault(in_yaml, in_param_ids):
    """


    Parameters:
    ----------


    Returns:
    ----------

    """

    default_params = name2num(in_yaml)
    param_ids = []
    for i in range(0, len(in_param_ids)):
        if in_param_ids[i] is None:
            param_ids.append(default_params[i])
        else:
            param_ids.append(in_param_ids[i])
    return param_ids


def pbl2sfclay(id_pbl, rnd=False):
    """
    Assigns the surface layer scheme based on the
    specified or randomly selected PBL scheme. If multiple surface layer
    schemes are available, one may be selected at random by setting rnd = True.
    Otherwise, sf_sfclay defaults to option 1 (the revised MM5 scheme).

    Parameters:
    ----------


    Returns:
    ----------

    """

    if id_pbl == 0:
        id_sfclay = 0
    elif id_pbl == 1:
        id_sfclay = 1
    elif id_pbl == 2:
        id_sfclay = 2
    elif id_pbl == 4:
        id_sfclay = 4
    elif id_pbl == 5:
        if rnd:
            id_sfclay = random.choice([1, 2, 5])
        else:
            id_sfclay = 1
    elif id_pbl == 6:
        id_sfclay = 5
    elif id_pbl == 7:
        if rnd:
            id_sfclay = random.choice([1, 7])
        else:
            id_sfclay = 1
    elif id_pbl == 8:
        if rnd:
            id_sfclay = random.choice([1, 2])
        else:
            id_sfclay = 1
    elif id_pbl == 9:
        if rnd:
            id_sfclay = random.choice([1, 2])
        else:
            id_sfclay = 1
    elif id_pbl == 10:
        id_sfclay = 10
    elif id_pbl == 11:
        if rnd:
            id_sfclay = random.choice([1, 2, 4, 5, 7, 10, 91])
        else:
            id_sfclay = 1
    elif id_pbl == 12:
        id_sfclay = 1
    else:
        print('No valid PBL scheme specified; turning off surface layer scheme.')
        id_sfclay = 0

    return id_sfclay


def flexible_generate(generate_params=True, mp=None, lw=None, sw=None,
                      lsm=None, pbl=None, cu=None, in_yaml='params.yml'):
    """
    Generate a parameter combination of the 6 core parameters if the user has specified this option.
    Otherwise, use specified input parameters and use defaults for the remaining paramters.

    Parameters:
    ----------


    Returns:
    ----------

    """

    if generate_params:
        rand_params = generate(in_yaml)
        param_ids = name2num(in_yaml, mp_in=rand_params[0], lw_in=rand_params[1],
                             sw_in=rand_params[2], lsm_in=rand_params[3],
                             pbl_in=rand_params[4], clo_in=rand_params[5])
    else:
        param_ids = [None, None, None, None, None, None]
        if mp is not None:
            param_ids1 = name2num(in_yaml, use_defaults=False, mp_in=mp, lw_in="None",
                                  sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
            param_ids = combine(param_ids, param_ids1)
        if lw is not None:
            param_ids2 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in=lw,
                                  sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
            param_ids = combine(param_ids, param_ids2)
        if sw is not None:
            param_ids3 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                  sw_in=sw, lsm_in="None", pbl_in="None", clo_in="None")
            param_ids = combine(param_ids, param_ids3)
        if lsm is not None:
            param_ids4 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                  sw_in="None", lsm_in=lsm, pbl_in="None", clo_in="None")
            param_ids = combine(param_ids, param_ids4)
        if pbl is not None:
            param_ids5 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                  sw_in="None", lsm_in="None", pbl_in=pbl, clo_in="None")
            param_ids = combine(param_ids, param_ids5)
        if cu is not None:
            param_ids6 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                  sw_in="None", lsm_in="None", pbl_in="None", clo_in=cu)
            param_ids = combine(param_ids, param_ids6)
        param_ids = filldefault(in_yaml, param_ids)

    # Set the sf_sfclay_pysics option based on that selected for PBL
    id_sfclay = pbl2sfclay(param_ids[4])
    param_ids.append(id_sfclay)
    print('The following parameters were generated: {}'.format(param_ids))
    return param_ids


def ids2str(param_ids):
    """


    Parameters:
    ----------


    Returns:
    ----------

    """

    paramstr = '%dmp%dlw%dsw%dlsm%dpbl%dcu' % \
               (param_ids[0], param_ids[1], param_ids[2],
                param_ids[3], param_ids[4], param_ids[5])
    return paramstr


def write_param_csv(param_ids, fitness):
    """


    This function is deprecated.

    Parameters:
    ----------


    Returns:
    ----------

    """

    runwrfcsv = 'paramfeed_runwrf.csv'
    if not os.path.exists(runwrfcsv):
        csvData = [['ra_lw_physics', 'ra_sw_physics', 'sf_surface_physics',
                    'bl_pbl_physics', 'cu_physics', 'sf_sfclay_physics', 'FITNESS'], [param_ids, fitness]]
        with open(runwrfcsv, 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows(csvData)
    else:
        with open(runwrfcsv, 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(param_ids)
