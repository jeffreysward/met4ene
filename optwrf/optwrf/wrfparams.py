"""
Generates sets of WRF physics parameters, finds corresponding numeric identifies,
and writes the numeric paramter options to a CSV.


Known Issues/Wishlist:
- It would be better if I could read in the parameters from the in_yaml
file only once, but I'm not sure how variables across different
functions in the same module work.

"""

import random
import yaml


def generate(in_yaml='params.yml'):
    """
    Generates a random set of WRF physics parameters. These physics parameters include:
    1. Microphysics
    2. Longwave radiation
    3. Shortwave Radieation
    4. Land Surface
    5. Planetary Boundary Layer
    6. Cumulus (clouds)

    :param in_yaml: string
        specifying the name of the yaml file containing parameter name integer pairs
        in sections by parameterization option.
    :return param_list: list
        specifying the integer assoicated with each parameter option.

    """
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


def flexible_generate(generate_params=True, mp=None, lw=None, sw=None,
                      lsm=None, pbl=None, cu=None, in_yaml='params.yml', verbose=False):
    """
    Generate a parameter combination of the 6 core parameters if the user has specified this option.
    Otherwise, use specified input parameters and use defaults (determined by the fill_default() method)
    for the remaining paramters.

    :param generate_params: boolean (default=True)
        specifying if parameters should be randomly generated or if some/all parameters
        will be user-specified. In the event that generate_params=False and not all
        parameters are specified, the remaining parameters will be filled with defaults.
    :param mp: string or integer (default=None)
        specifying the microphysics parameterization name or namelist.input value.
    :param lw: string or integer (default=None)
        specifying the longwave radiation parameterization name or namelist.input value.
    :param sw: string or integer (default=None)
        specifying the shortwave radiation parameterization name or namelist.input value.
    :param lsm: string or integer (default=None)
        specifying the land surface parameterization name or namelist.input value.
    :param pbl: string or integer (default=None)
        specifying the planetary boundary layer parameterization name or namelist.input value.
    :param cu: string or integer (default=None)
        specifying the cumulus parameterization name or namelist.input value.
    :param in_yaml: string
        specifying the name of the yaml file containing parameter name integer pairs
        in sections by parameterization option.
    :param verbose: boolean (default=False)
        determining whether or not to print lots of model information to the screen.
    :return param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization.

    """
    if generate_params:
        rand_params = generate(in_yaml)
        param_ids = name2num(in_yaml, mp_in=rand_params[0], lw_in=rand_params[1],
                             sw_in=rand_params[2], lsm_in=rand_params[3],
                             pbl_in=rand_params[4], clo_in=rand_params[5])
    else:
        param_ids = [None, None, None, None, None, None]
        if mp is not None:
            if type(mp) is str:
                param_ids1 = name2num(in_yaml, use_defaults=False, mp_in=mp, lw_in="None",
                                      sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
            elif type(mp) is int:
                param_ids1 = [mp, None, None, None, None, None]
            else:
                print(f'Variable mp = {mp} has an incorrect type.')
                raise TypeError
            param_ids = combine(param_ids, param_ids1)
        if lw is not None:
            if type(lw) is str:
                param_ids2 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in=lw,
                                      sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
            elif type(lw) is int:
                param_ids2 = [None, lw, None, None, None, None]
            else:
                print(f'Variable lw = {lw} has an incorrect type.')
                raise TypeError
            param_ids = combine(param_ids, param_ids2)
        if sw is not None:
            if type(sw) is str:
                param_ids3 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                      sw_in=sw, lsm_in="None", pbl_in="None", clo_in="None")
            elif type(sw) is int:
                param_ids3 = [None, None, sw, None, None, None]
            else:
                print(f'Variable sw = {sw} has an incorrect type.')
                raise TypeError
            param_ids = combine(param_ids, param_ids3)
        if lsm is not None:
            if type(lsm) is str:
                param_ids4 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                      sw_in="None", lsm_in=lsm, pbl_in="None", clo_in="None")
            elif type(lsm) is int:
                param_ids4 = [None, None, None, lsm, None, None]
            else:
                print(f'Variable lsm = {lsm} has an incorrect type.')
                raise TypeError
            param_ids = combine(param_ids, param_ids4)
        if pbl is not None:
            if type(pbl) is str:
                param_ids5 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                      sw_in="None", lsm_in="None", pbl_in=pbl, clo_in="None")
            elif type(pbl) is int:
                param_ids5 = [None, None, None, None, pbl, None]
            else:
                print(f'Variable pbl = {pbl} has an incorrect type.')
                raise TypeError
            param_ids = combine(param_ids, param_ids5)
        if cu is not None:
            if type(cu) is str:
                param_ids6 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                                      sw_in="None", lsm_in="None", pbl_in="None", clo_in=cu)
            elif type(cu) is int:
                param_ids6 = [None, None, None, None, None, cu]
            else:
                print(f'Variable cu = {cu} has an incorrect type.')
                raise TypeError
            param_ids = combine(param_ids, param_ids6)
        param_ids = filldefault(in_yaml, param_ids)

    # Set the sf_sfclay_pysics option based on that selected for PBL
    id_sfclay = pbl2sfclay(param_ids[4])
    param_ids.append(id_sfclay)
    # Apply known parameter dependencies
    param_ids = apply_dependencies(param_ids)
    if verbose:
        print(f'The following parameters were generated: {param_ids}')
    return param_ids


def name2num(in_yaml='params.yml', use_defaults=True, mp_in="morrison2mom", lw_in="rrtm", sw_in="dudia",
             lsm_in="noah", pbl_in="myj", clo_in="grell-freitas"):
    """
    Maps the name of the physics parameterization,
    which is defined generally by the name of the individual or
    institution that designed the scheme, to the namelist.input value.
    The default value of these parameterization schemes is set by those that
    were originally used by ICF in the study over NYC.

    :param in_yaml: string
        specifying the name of the yaml file containing parameter name integer pairs
        in sections by parameterization option.
    :param use_defaults: boolean (default=True)
        determining wether or not you would like to return the default parameterization
        option if none is specified or if you would rather return None.
    :param mp_in: string
        specifying the microphysics parameterization name.
    :param lw_in: string
        specifying the longwave radiation parameterization name.
    :param sw_in: string
        specifying the shortwave radiation paramterization name.
    :param lsm_in: string
        specifying the land surface model parameterization name.
    :param pbl_in: string
        specifying the planetary boundary layer parameterization name.
    :param clo_in: string
        specifying the cumulus parameterization name.
    :return param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization.

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


def num2name(param_ids, physics_type, in_yaml='params.yml'):
    """
    Takes a list of param_ids and maps them to the physical parameterization name.
    Note that this only works for one type of physics at a time (i.e., microphysics,
    lw radiation, sw radiation, land surface, PBL, cumulus).

    :param param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization.
    :param physics_type: string
        specifying a parameterization category. Options include: microphysics,
        lw radiation, sw radiation, land surface, PBL, and cumulus.
    :param in_yaml: string
        specifying the name of the yaml file containing parameter name integer pairs
        in sections by parameterization option.
    :return param_names: list of strings
        corresponding to the physical parameterization names.

    """
    with open(in_yaml, 'r') as params_file:
        try:
            params = yaml.safe_load(params_file)
            physics = params.get(physics_type)
            # list out keys and values separately
            key_list = list(physics.keys())
            val_list = list(physics.values())
            # get the param names using the list index method
            param_names = [key_list[val_list.index(param)] for param in param_ids]
        except yaml.YAMLError as exc:
            print(exc)
            param_names = []

    return param_names


def combine(lst1, lst2):
    """
    Combines two lists where at LEAST one of the two entries in the i'th position is None.
    The out_list contains values that are not None contained in either list.
    If both lists have None in the i'th position, then the out_list will also contain None.

    :param lst1: list
    :param lst2: list
    :return out_list: list
        combined from lst1 and lst2.

    """
    out_list = []
    for i in range(0, len(lst1)):
        if lst1[i] is None and lst2[i] is None:
            out_list.append(None)
        elif lst1[i] is None:
            out_list.append(lst2[i])
        elif lst2[i] is None:
            out_list.append(lst1[i])
        else:
            print(f'WARNING: you are using this function for the wrong type of lists.'
                  f'\nFor each ith entry in the two lists, at most one should be not None.')
    return out_list


def filldefault(in_yaml, in_param_ids):
    """
    Fills an incomplete list (None values) of paramerization IDs with the defaults. The default value of
    these parameterization schemes is set by those that were originally used by ICF in the study over NYC.

    :param in_yaml: string
        specifying the name of the yaml file containing parameter name integer pairs
        in sections by parameterization option.
    :param in_param_ids: list of integers containing some Nones
        corresponding to the namelist.input values of each input parameterization.
    :return param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization.

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
    Assigns the surface layer scheme based on the specified or randomly selected PBL scheme.
    If multiple surface layer schemes are available, one may be selected at random
    by setting rnd = True. Otherwise, id_sfclay defaults to option 1 (revised MM5 scheme).

    :param id_pbl: integer
        corresponding to the namelist.input value of the planetary boundary layer parameterization.
    :param rnd: boolean (default=False)
        that dictates whether or not compatible id_sfclay parameterization options are
        selected randomly or if the default value, id_sfclay = 1, is used.
    :return id_sfclay: integer
        corresponding to the namelist.input value of the surface layer parameterization.

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
            id_sfclay = random.choice([1, 91])
        else:
            id_sfclay = 1
    elif id_pbl == 12:
        id_sfclay = 1
    else:
        print('WARNING: No valid PBL scheme specified; turning off surface layer scheme.')
        id_sfclay = 0

    return id_sfclay


def apply_dependencies(param_ids):
    """
    Applies depependencies among parameters. Generally,
    these were discovered by attempting to run an incompatible combination
    of parameters or from the WRF User's Guide.

    :param param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization.
    :return param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization
        after known dependencies have been applied.

    """
    # The following exception takes care of the error:
    # CAMZMSCHEME requires MYJPBLSCHEME or CAMUWPBLSCHEME
    if param_ids[5] is 7 and param_ids[4] not in [2, 9]:
        param_ids[4] = random.choice([2, 9])
    # The following exception takes care of the error:
    # bl_pbl_physics must be set to 1 for cu_physics = 11
    if param_ids[5] is 11:
        param_ids[4] = 1
    return param_ids


def ids2str(param_ids):
    """
    Takes the parameterization IDs and combines them to form a string for appending to directory
    and file names for easy identification.

    :param param_ids: list of integers
        corresponding to the namelist.input values of each input parameterization.
    :return: paramstr: string
        combining each integer and associated abbreviation for all the parameterization options.

    """
    paramstr = '%dmp%dlw%dsw%dlsm%dpbl%dcu' % \
               (param_ids[0], param_ids[1], param_ids[2],
                param_ids[3], param_ids[4], param_ids[5])
    return paramstr
