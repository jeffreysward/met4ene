#!/usr/bin/env python3
# wrfparams_name2num.py takes strings associated with different parameter choices 
# and maps them to their numeric identifier to be written to namelist.input. 
# You may specify any number of parameter options, and default(s) (defined 
# as the ones that ICF used initially) will be used for the rest. 
import yaml


def wrfparams_name2num(mp_in="kressler", lw_in="rrtmg", sw_in="rrtmg",
                     slay_in="mynn", lsm_in="noah", usurf_in="urban canopy", lsurf_in="clm", pbl_in="mynn2",
                     clo_in="kain-fritsch", conv_in="ishallow"):
    with open("params.yml", 'r') as params_file:
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


param_nums = wrfparams_name2num(mp_in="kressler", lw_in="rrtmg", sw_in="rrtmg",
                              slay_in="mynn", lsm_in="noah", usurf_in="urban canopy",
                              lsurf_in="clm", pbl_in="mynn2", clo_in="kain-fritsch", conv_in="ishallow")
print(param_nums)

