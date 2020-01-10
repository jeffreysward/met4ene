import yaml


def name2num(in_yaml, use_defaults=True, mp_in="morrison2mom", lw_in="rrtm", sw_in="dudia",
             lsm_in="noah", pbl_in="myj", clo_in="grell-freitas"):
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
    default_params = name2num(in_yaml)
    param_ids = []
    for i in range(0, len(in_param_ids)):
        if in_param_ids[i] is None:
            param_ids.append(default_params[i])
        else:
            param_ids.append(in_param_ids[i])
    return param_ids


yaml_file = 'params.yml'
params1 = name2num(yaml_file, use_defaults=False, mp_in="thompson", lw_in="None",
                   sw_in="dudia", lsm_in="None", pbl_in="None", clo_in="None")
print(params1)
params2 = name2num(yaml_file, use_defaults=False, mp_in="None", lw_in="rrtm",
                   sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
print(params2)

params = combine(params1, params2)
print(params)
params = filldefault(yaml_file, params)
print(params)
