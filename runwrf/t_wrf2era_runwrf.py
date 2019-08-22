from argparse import ArgumentParser
from datetime import datetime, timedelta
from os import chdir, getcwd, mkdir, makedirs, system, path, environ
from shutil import rmtree
from socket import gethostname
from subprocess import call
from sys import exit
from time import localtime, strftime, strptime, time
import time as tm
from wrfparams import name2num, generate, combine, filldefault, pbl2sfclay
import sys
import os
import csv


forecast_start = datetime.strptime('Jan 16 2011', '%b %d %Y')
DIR_LOCAL_TMP = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/%s_10mp1lw1sw2lsm2pbl2cu/' % \
                (forecast_start.strftime('%Y-%m-%d'))
CMD_REGRID = 'ncl in_yr=%s in_mo=%s in_da=%s WRFdir=%s wrf2era_runwrf.ncl' % \
             (forecast_start.strftime('%Y'), forecast_start.strftime('%m'), forecast_start.strftime('%d'), DIR_LOCAL_TMP)

system(CMD_REGRID)

