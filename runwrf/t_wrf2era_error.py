from datetime import datetime 
from os import system
from wrfparams import ids2str

param_ids = [0, 3, 7, 7, 5, 2, 1]
start_date='Jan 15 2011'
forecast_start = datetime.strptime(start_date, '%b %d %Y')
paramstr = ids2str(param_ids)

DIR_LOCAL_TMP = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/%s_%s/' % \
                (forecast_start.strftime('%Y-%m-%d'), paramstr)
CMD_REGRID = 'ncl in_yr=%s in_mo=%s in_da=%s \'WRFdir="%s"\' \'paramstr="%s"\' wrf2era_error.ncl' % \
		                 (forecast_start.strftime('%Y'), forecast_start.strftime('%m'),
				  forecast_start.strftime('%d'), DIR_LOCAL_TMP, paramstr)
print(CMD_REGRID)
system(CMD_REGRID) 
