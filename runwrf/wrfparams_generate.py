#!/usr/bin/env python
# wrfparams_generate.py generates a random set of physics parameters 
# using the rand function and returns the strings associated with 
# each paraterization.
import yaml
import random


def wrfparams_generate():
    with open("params.yml", 'r') as params_file:
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


rand_params = wrfparams_generate()
print(rand_params)
print(rand_params[1])