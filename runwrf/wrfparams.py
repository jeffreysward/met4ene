"""
Overview:

- This module deals with wrf's input parameters.

- wrfparams_generate() can be used to generate a random set of parameters

- wrfparams_name2num() is used to map the name of the parameterization,
which is defined generally by the name of the individual or
institution that designed the scheme, to the namelist.input value.

_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues:

- It would be better if I could read in the parameters from the in_yaml
file only once, but I'm not sure how variables across different
functions in the same module work.

"""

import yaml
import random


def generate(in_yaml):
    with open(in_yaml, 'r') as params_file:
        try:
            params = yaml.safe_load(params_file)

        except yaml.YAMLError as exc:
            print(exc)

    mp = params.get("microphysics")
    lw = params.get("lw radiation")
    sw = params.get("sw radiation")
    slay = params.get("surface layer")
    lsm = params.get("land surface")
    usurf = params.get("urban surface")
    lsurf = params.get("lake physics")
    pbl = params.get("PBL")
    clo = params.get("cumulus")
    conv = params.get("shallow convection")

    param_opts = [mp, lw, sw, slay, lsm, usurf, lsurf, pbl, clo, conv]

    param_list = []
    for opt in param_opts:
        param_choice = random.choice(list(opt.keys()))
        param_list.append(str(param_choice))

    return param_list


def name2num(in_yaml, mp_in="kressler", lw_in="rrtmg", sw_in="rrtmg",
                       slay_in="mynn", lsm_in="noah", usurf_in="urban canopy",
                       lsurf_in="clm", pbl_in="mynn2",
                       clo_in="kain-fritsch", conv_in="ishallow"):
    with open(in_yaml, 'r') as params_file:
        try:
            params = yaml.safe_load(params_file)

            mp = params.get("microphysics")
            lw = params.get("lw radiation")
            sw = params.get("sw radiation")
            slay = params.get("surface layer")
            lsm = params.get("land surface")
            usurf = params.get("urban surface")
            lsurf = params.get("lake physics")
            pbl = params.get("PBL")
            clo = params.get("cumulus")
            conv = params.get("shallow convection")

            id_mp = mp.get(mp_in)
            id_lw = lw.get(lw_in)
            id_sw = sw.get(sw_in)
            id_slay = slay.get(slay_in)
            id_lsm = lsm.get(lsm_in)
            id_usurf = usurf.get(usurf_in)
            id_lsurf = lsurf.get(lsurf_in)
            id_pbl = pbl.get(pbl_in)
            id_clo = clo.get(clo_in)
            id_conv = conv.get(conv_in)

            param_ids = [id_mp, id_lw, id_sw, id_slay, id_lsm,
                         id_usurf, id_lsurf, id_pbl, id_clo, id_conv]

        except yaml.YAMLError as exc:
            print(exc)
            param_ids = []

    return param_ids
