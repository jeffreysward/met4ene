# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 12:05:31 2019

@author: Colin
"""

from netCDF4 import Dataset
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
from matplotlib.cm import get_cmap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as N
import os
import glob
import moviepy.editor as mpy
from datetime import datetime
from dateutil import tz
import xarray


from wrf import getvar, ALL_TIMES, extract_times, latlon_coords, get_cartopy, to_np, ll_to_xy, xy_to_ll, geo_bounds, CoordPair

# Open the NetCDF file
ncfile = Dataset("wrf_jan_29.nc")
pressure = N.array(ncfile.variables['PSFC'][::])
pressure = pressure/100
temps = N.array(ncfile.variables['T2'][::])
lats = N.array(ncfile.variables['XLAT'][0,:,:])
lons = N.array(ncfile.variables['XLONG'][0,:,:])
temps = temps - 273.15
temp_f = ((temps * (9./5.)) + 32.)
time = extract_times(ncfile, ALL_TIMES, method="cat")
temp = getvar(ncfile, "tk")
tempf = ((temp * 9./5.) + 32.)
time_string=[]
for i in range(41):
    string = str(time[i])
    string = string[0:13]
    time_string.append(string)
    
EST = []
from_zone = tz.tzutc()
to_zone = tz.tzlocal()
counter = 0
for i in range(41):
    utc = datetime.strptime(time_string[i], '%Y-%m-%dT%H')
    utc = utc.replace(tzinfo=from_zone)
    eastern = utc.astimezone(to_zone)
    string = str(eastern)
    EST.append(string[0:13])

oDir = "/home/cpe28/cfd/figs"
os.chdir(oDir)

temp_levels = N.arange(-60,90,0.5)
pressure_levels = N.arange(800,1051,50)
states_provinces = cfeature.NaturalEarthFeature(category='cultural',name='admin_1_states_provinces_lines',scale='50m',facecolor='none')
for i in range(41):
    lats, lons = latlon_coords(tempf)
    cart_proj = get_cartopy(temp)
    fig = plt.figure(figsize=(12,9))
    ax = plt.axes(projection=cart_proj)
    ax.coastlines(resolution='50m', linewidth=0.5)
    ax.add_feature(states_provinces, edgecolor='k', linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, edgecolor='k', linewidth=0.5)
    ax.set_extent([-114,-55,20,64])
    contours = ax.contourf(to_np(lons), to_np(lats), temp_f[i,:,:], temp_levels, transform=ccrs.PlateCarree(), cmap=get_cmap('jet'))
    contour = ax.contour(to_np(lons), to_np(lats), pressure[i,:,:], pressure_levels, colors='k', transform=ccrs.PlateCarree(), linestyles='solid')
    plt.title("Temperature and Pressure Forecast for \n" + EST[i] + ' EST')
    plt.colorbar(contours, ax=ax, orientation="horizontal", label="Temperature(F)")
    plt.clabel(contour, pressure_levels[::2], inline=1, fmt='%1.f', fontsize=10)
#    plt.savefig("forecast_"+str(i)+".jpeg", dpi=200)
    plt.show()
    plt.close()
    
mp4_name = 'forecast'
fps=6
file_list1 = glob.glob('*.jpeg')
list.sort(file_list1, key=lambda x: int(x.split('_')[1].split('.jpeg')[0]))
clip = mpy.ImageSequenceClip(file_list1, fps=fps)
clip.write_videofile('{}.mp4'.format(mp4_name), fps=fps)

mp4_name = 'forecast_gif'
fps=6
file_list1 = glob.glob('*.jpeg')
list.sort(file_list1, key=lambda x: int(x.split('_')[1].split('.jpeg')[0]))
clip = mpy.ImageSequenceClip(file_list1, fps=fps)
clip.write_gif('{}.gif'.format(mp4_name), fps=fps)

dir_name = oDir
test = os.listdir(dir_name)
for item in test:
    if item.endswith(".jpeg"):
        os.remove(os.path.join(dir_name, item))


def find_location(lat_data, lon_data, xlat, xlon):
    A = (lats - xlat)**2
    B = (lons - xlon)**2
    D = (A+B)**0.5
    index = N.where(D==N.min(D))
    return D, index

distance, index = find_location(lats, lons, 42.44, -76.5)

distance_levels = N.arange(0,80,0.5)
states_provinces = cfeature.NaturalEarthFeature(category='cultural',name='admin_1_states_provinces_lines',scale='50m',facecolor='none')
lats, lons = latlon_coords(tempf)
cart_proj = get_cartopy(temp)
fig = plt.figure()
ax = plt.axes(projection=cart_proj)
ax.coastlines(resolution='50m', linewidth=0.5)
ax.add_feature(states_provinces, edgecolor='k', linewidth=0.5)
ax.add_feature(cfeature.BORDERS, edgecolor='k', linewidth=0.5)
ax.set_extent([-114,-55,20,64])
contours = ax.contourf(to_np(lons), to_np(lats), distance, distance_levels, transform=ccrs.PlateCarree(), cmap=get_cmap('jet'))
plt.title("Grid Distance Map")
plt.colorbar(contours, ax=ax, orientation="horizontal", label="Distance from Ithaca, NY")
plt.savefig("distance_map.jpeg", dpi=200)
plt.show()
plt.close()


ithaca_temps = temp_f[:,int(index[0]),int(index[1])]
fig = plt.figure()
plt.plot(EST, ithaca_temps)
plt.xticks(EST[::5], rotation=45)
plt.title("WRF Temperature Forecast\nIthaca, NY")
plt.ylabel("Temperature (F)")
plt.savefig("timeseries.jpeg", dpi=200)
plt.show()
plt.close()