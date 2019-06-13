#!/usr/bin/env python3
#This file tests the the ability of a yaml file to input into a python

import yaml

with open("params.yml", 'r') as params_file:
    try:
        params = yaml.load(params_file)

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

        print(mp.get("kressler"))
        print(lw.get("rrtmg"))
        print(sw.get("rrtmg"))
        print(slay.get("mynn"))
        print(lsm.get("noah"))
        print(usurf.get("urban canopy"))
        print(lsurf.get("clm"))
        print(pbl.get("mynn2"))
        print(clo.get("kain-fritsch"))
        print(conv.get("ishallow"))

    except yaml.YAMLError as exc:
        print(exc)

        