"""
Plotting functions
"""

import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import numpy as np
import xarray as xr
import wrf as wrfpy
from optwrf import runwrf, helper_functions


def wrf_era5_plot(var, wrfdat, eradat, datestr, src='wrf', hourly=False, save_fig=False,
                  wrf_dir='./', era_dir='./', short_title_str='Title', fig_path='./'):
    """
    Creates a single WRF or ERA5 plot, using the WRF bounds, producing either a plot every hour
    or a single plot for the day.
    """
    # Format the var input
    if type(var) is not str:
        print(f'The var input, {var}, must be a string.')
        raise TypeError
    if var in ['GHI', 'ghi']:
        var = 'ghi'
        wrf_var = 'ghi'
        era_var = 'GHI'
    elif var in ['WPD', 'wpd']:
        var = 'wpd'
        wrf_var = 'wpd'
        era_var = 'WPD'
    elif var in ['ghi_error', 'GHI_ERROR']:
        var = 'ghi_error'
        wrf_var = var
    elif var in ['wpd_error', 'WPD_ERROR']:
        var = 'wpd_error'
        wrf_var = var
    elif var in ['fitness', 'Fitness', 'FITNESS']:
        var = 'fitness'
        wrf_var = var
    else:
        print(f'Variable {var} is not supported.')
        raise KeyError

    # Rename the lat-lon corrdinates to get wrf-python to recognize them
    variables = {'lat': 'XLAT',
                 'lon': 'XLONG'}
    try:
        wrfdat = xr.Dataset.rename(wrfdat, variables)
    except ValueError:
        print(f'Variables {variables} cannot be renamed, '
              f'those on the left are not in this dataset.')

    # This makes it easy to get the latitude and longitude coordinates with the wrf-python function below
    lats, lons = wrfpy.latlon_coords(wrfdat['dni'])

    # I have to do this tedious string parsing below to get the projection from the processed wrfout file.
    try:
        wrf_proj_params = wrfdat.dni.attrs['projection']
    except AttributeError:
        raise ValueError('Variable does not contain projection information')
    wrf_proj_params = wrf_proj_params.replace('(', ', ')
    wrf_proj_params = wrf_proj_params.replace(')', '')
    wrf_proj_params = wrf_proj_params.split(',')
    wrf_proj = wrf_proj_params[0]
    stand_lon = float(wrf_proj_params[1].split('=')[1])
    moad_cen_lat = float(wrf_proj_params[2].split('=')[1])
    truelat1 = float(wrf_proj_params[3].split('=')[1])
    truelat2 = float(wrf_proj_params[4].split('=')[1])
    pole_lat = float(wrf_proj_params[5].split('=')[1])
    pole_lon = float(wrf_proj_params[6].split('=')[1])

    # Fortunately, it still apppears to work.
    if wrf_proj == 'LambertConformal':
        wrf_cartopy_proj = ccrs.LambertConformal(central_longitude=stand_lon,
                                                 central_latitude=moad_cen_lat,
                                                 standard_parallels=[truelat1, truelat2])
    else:
        print('Your WRF projection is not the expected Lambert Conformal.')
        raise ValueError

    # I need to manually convert the boundaries of the WRF domain into Plate Carree to set the limits.
    # Get the raw map bounds using a wrf-python utility
    raw_bounds = wrfpy.util.geo_bounds(wrfdat['dni'])
    # Get the projected bounds telling cartopy that the input coordinates are lat/lon (Plate Carree)
    proj_bounds = wrf_cartopy_proj.transform_points(ccrs.PlateCarree(),
                                                    np.array([raw_bounds.bottom_left.lon, raw_bounds.top_right.lon]),
                                                    np.array([raw_bounds.bottom_left.lat, raw_bounds.top_right.lat]))

    # We can use a basic Plate Carree projection for ERA5
    era5_cartopy_proj = ccrs.PlateCarree()

    # Now, get the desired variables
    if var in ['ghi_error', 'wpd_error', 'fitness']:
        input_year = helper_functions.format_date(datestr).strftime('%Y')
        input_month = helper_functions.format_date(datestr).strftime('%m')
        wrfdat_proc, eradat_proc = runwrf.wrf_era5_regrid_xesmf(input_year,
                                                                input_month,
                                                                wrfdir=wrf_dir,
                                                                eradir=era_dir)

        # Calculate the error in GHI and WPD
        wrfdat_proc = runwrf.wrf_era5_error(wrfdat_proc, eradat_proc)

        print(wrfdat_proc)

        # Calculate the fitness
        correction_factor = 0.0004218304553577255
        daylight_factor = helper_functions.daylight_frac(datestr)  # daylight fraction
        wrfdat_proc['fitness'] = daylight_factor * wrfdat_proc.ghi_error \
                                 + correction_factor * wrfdat_proc.wpd_error

    # Define the time indicies from the times variable
    time_indicies = range(0, len(wrfdat.Time))
    # Format the times for title slides
    times_strings_f = wrfdat.Time.dt.strftime('%b %d, %Y %H:%M')
    # Get the desired variable(s)
    for tidx in time_indicies:
        timestr = wrfdat.Time[tidx].values
        timestr_f = times_strings_f[tidx].values
        if hourly:
            title_str = f'{short_title_str}\n{timestr_f} (UTC)'
        else:
            time_string_f = wrfdat.Time[0].dt.strftime('%b %d, %Y')
            title_str = f'{short_title_str}\n{time_string_f.values}'

        # WRF Variable (divide by 1000 to convert from W to kW or Wh to kWh)
        if not hourly and tidx != 0:
            if src == 'wrf':
                if var in ['ghi', 'wpd']:
                    plot_var = plot_var + (wrfdat[wrf_var].sel(Time=np.datetime_as_string(timestr)) / 1000)
                else:
                    plot_var = plot_var + wrfdat_proc[wrf_var].sel(Time=np.datetime_as_string(timestr))
            elif src == 'era5':
                if var in ['ghi', 'wpd']:
                    plot_var = plot_var + (eradat[era_var].sel(Time=np.datetime_as_string(timestr)) / 1000)
                else:
                    print(f'Variable {var} is not provided by {src}')
                    raise ValueError
        else:
            if src == 'wrf':
                if var in ['ghi', 'wpd']:
                    plot_var = wrfdat[wrf_var].sel(Time=np.datetime_as_string(timestr)) / 1000
                else:
                    plot_var = wrfdat_proc[wrf_var].sel(Time=np.datetime_as_string(timestr))
            elif src == 'era5':
                if var in ['ghi', 'wpd']:
                    plot_var = eradat[era_var].sel(Time=np.datetime_as_string(timestr)) / 1000
                else:
                    print(f'Variable {var} is not provided by {src}')
                    raise ValueError

        if hourly:
            # Create a figure
            fig = plt.figure(figsize=(4, 4))

            # Set the GeoAxes to the projection used by WRF
            ax = fig.add_subplot(1, 1, 1, projection=wrf_cartopy_proj)

            # Get, format, and set the map bounds

            # Format the projected bounds so they can be used in the xlim and ylim attributes
            proj_xbounds = [proj_bounds[0, 0], proj_bounds[1, 0]]
            proj_ybounds = [proj_bounds[0, 1], proj_bounds[1, 1]]
            # Finally, set the x and y limits
            ax.set_xlim(proj_xbounds)
            ax.set_ylim(proj_ybounds)

            # Download and add the states, coastlines, and lakes
            states = cfeature.NaturalEarthFeature(category="cultural", scale="50m",
                                                  facecolor="none",
                                                  name="admin_1_states_provinces_shp")

            # Add features to the maps
            ax.add_feature(states, linewidth=.5, edgecolor="black")
            ax.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
            ax.add_feature(cfeature.OCEAN.with_scale('50m'))

            # Make the countour lines for filled contours for the GHI
            if hourly:
                if var in ['ghi', 'ghi_error']:
                    contour_levels = np.linspace(0, 0.75, 22)
                elif var in ['wpd', 'wpd_error']:
                    contour_levels = np.linspace(0, 2500, 22)
                elif var == 'fitness':
                    contour_levels = np.linspace(0, 1.5, 22)
            else:
                if var in ['ghi', 'ghi_error']:
                    contour_levels = np.linspace(0, 5, 22)
                elif var in ['wpd', 'wpd_error']:
                    contour_levels = np.linspace(0, np.amax(wrfpy.to_np(plot_var)), 22)
                elif var == 'fitness':
                    contour_levels = np.linspace(0, 10, 22)

            # Add the filled contour levels
            if var in ['ghi', 'ghi_error']:
                color_map = get_cmap("hot_r")
            elif var in ['wpd', 'wpd_error']:
                color_map = get_cmap("Greens")
            elif var == 'fitness':
                color_map = get_cmap("Greys")
            if src == 'wrf' and var in ['ghi', 'wpd']:
                cn = ax.contourf(wrfpy.to_np(lons), wrfpy.to_np(lats), wrfpy.to_np(plot_var),
                                 contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)
            else:
                cn = ax.contourf(wrfpy.to_np(eradat.longitude), wrfpy.to_np(eradat.latitude), wrfpy.to_np(plot_var),
                                 contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)

            # Add a color bar
            plt.colorbar(cn, ax=ax, shrink=.98)

            # Add the axis title
            ax.set_title(title_str)

            # Save the figure(s)
            if save_fig:
                fig_path_temp = fig_path + str(tidx).zfill(2)
                plt.savefig(fig_path_temp + '.png', dpi=300, transparent=True, bbox_inches='tight')

            plt.show()

    # Create a figure
    fig = plt.figure(figsize=(4, 4))

    # Set the GeoAxes to the projection used by WRF
    ax = fig.add_subplot(1, 1, 1, projection=wrf_cartopy_proj)

    # Get, format, and set the map bounds

    # Format the projected bounds so they can be used in the xlim and ylim attributes
    proj_xbounds = [proj_bounds[0, 0], proj_bounds[1, 0]]
    proj_ybounds = [proj_bounds[0, 1], proj_bounds[1, 1]]
    # Finally, set the x and y limits
    ax.set_xlim(proj_xbounds)
    ax.set_ylim(proj_ybounds)

    # Download and add the states, coastlines, and lakes
    states = cfeature.NaturalEarthFeature(category="cultural", scale="50m",
                                          facecolor="none",
                                          name="admin_1_states_provinces_shp")

    # Add features to the maps
    ax.add_feature(states, linewidth=.5, edgecolor="black")
    ax.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
    ax.add_feature(cfeature.OCEAN.with_scale('50m'))

    # Make the countour lines for filled contours for the GHI
    if hourly:
        if var in ['ghi', 'ghi_error']:
            contour_levels = np.linspace(0, 0.75, 22)
        elif var in ['wpd', 'wpd_error']:
            contour_levels = np.linspace(0, 25000, 22)
        elif var == 'fitness':
            contour_levels = np.linspace(0, 1.5, 22)
    else:
        if var in ['ghi', 'ghi_error']:
            contour_levels = np.linspace(0, 5, 22)
        elif var in ['wpd', 'wpd_error']:
            contour_levels = np.linspace(0, np.amax(wrfpy.to_np(plot_var)), 22)
        elif var == 'fitness':
            contour_levels = np.linspace(0, 10, 22)

    # Add the filled contour levels
    if var in ['ghi', 'ghi_error']:
        color_map = get_cmap("hot_r")
    elif var in ['wpd', 'wpd_error']:
        color_map = get_cmap("Greens")
    elif var == 'fitness':
        color_map = get_cmap("Greys")
    if src == 'wrf' and var in ['ghi', 'wpd']:
        cn = ax.contourf(wrfpy.to_np(lons), wrfpy.to_np(lats), wrfpy.to_np(plot_var),
                         contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)
    else:
        cn = ax.contourf(wrfpy.to_np(eradat.longitude), wrfpy.to_np(eradat.latitude), wrfpy.to_np(plot_var),
                         contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)

    # Add a color bar
    plt.colorbar(cn, ax=ax, shrink=.98)

    # Add the axis title
    ax.set_title(title_str)

    # Save the figure(s)
    if save_fig:
        plt.savefig(fig_path + '.pdf', transparent=True, bbox_inches='tight')

    plt.show()


def compare_wrf_era5_plot(var, wrfdat, eradat, hourly=False, save_fig=False, fig_path='./'):
    """
    Creates a side-by-side comparison plot of WRF and ERA5 producing either a plot every hour
    or a single plot for the day.
    """
    # Format the var input
    if type(var) is not str:
        print(f'The var input, {var}, must be a string.')
        raise TypeError
    if var in ['GHI', 'ghi']:
        var = 'ghi'
        wrf_var = 'ghi'
        era_var = 'GHI'
    elif var in ['WPD', 'wpd']:
        var = 'wpd'
        wrf_var = 'wpd'
        era_var = 'WPD'
    else:
        print(f'Variable {var} is not supported.')
        raise KeyError

    # Rename the lat-lon corrdinates to get wrf-python to recognize them
    variables = {'lat': 'XLAT',
                 'lon': 'XLONG'}
    try:
        wrfdat = xr.Dataset.rename(wrfdat, variables)
    except ValueError:
        print(f'Variables {variables} cannot be renamed, '
              f'those on the left are not in this dataset.')

    # This makes it easy to get the latitude and longitude coordinates with the wrf-python function below
    lats, lons = wrfpy.latlon_coords(wrfdat[wrf_var])

    # I have to do this tedious string parsing below to get the projection from the processed wrfout file.
    try:
        wrf_proj_params = wrfdat.dni.attrs['projection']
    except AttributeError:
        raise ValueError('Variable does not contain projection information')
    wrf_proj_params = wrf_proj_params.replace('(', ', ')
    wrf_proj_params = wrf_proj_params.replace(')', '')
    wrf_proj_params = wrf_proj_params.split(',')
    wrf_proj = wrf_proj_params[0]
    stand_lon = float(wrf_proj_params[1].split('=')[1])
    moad_cen_lat = float(wrf_proj_params[2].split('=')[1])
    truelat1 = float(wrf_proj_params[3].split('=')[1])
    truelat2 = float(wrf_proj_params[4].split('=')[1])
    pole_lat = float(wrf_proj_params[5].split('=')[1])
    pole_lon = float(wrf_proj_params[6].split('=')[1])

    # Fortunately, it still apppears to work.
    if wrf_proj == 'LambertConformal':
        wrf_cartopy_proj = ccrs.LambertConformal(central_longitude=stand_lon,
                                                 central_latitude=moad_cen_lat,
                                                 standard_parallels=[truelat1, truelat2])
    else:
        print('Your WRF projection is not the expected Lambert Conformal.')
        raise ValueError

    # We can use a basic Plate Carree projection for ERA5
    era5_cartopy_proj = ccrs.PlateCarree()

    # Now, get the desired variables
    # Define the time indicies from the times variable
    time_indicies = range(0, len(wrfdat.Time))
    # Format the times for title slides
    times_strings_f = wrfdat.Time.dt.strftime('%b %d, %Y %H:%M')
    # Get the desired variable(s)
    for tidx in time_indicies:
        timestr = wrfdat.Time[tidx].values
        timestr_f = times_strings_f[tidx].values
        if hourly:
            title_str = f'{era_var} (kW m-2)\n{timestr_f} (UTC)'
        else:
            time_string_f = wrfdat.Time[0].dt.strftime('%b %d, %Y')
            title_str = f'{era_var} (kWh m-2 day-1) \n{time_string_f.values}'

        # WRF Variable (divide by 1000 to convert from W to kW or Wh to kWh)
        if not hourly and tidx != 0:
            plot_wrfvar = plot_wrfvar + (wrfdat[wrf_var].sel(Time=np.datetime_as_string(timestr)) / 1000)
        else:
            plot_wrfvar = wrfdat[wrf_var].sel(Time=np.datetime_as_string(timestr)) / 1000

        # ERA5 GHI (divide by 1000 to convert from W to kW or Wh to kWh)
        if not hourly and tidx != 0:
            plot_era5var = plot_era5var + (eradat[era_var].sel(Time=timestr_f) / 1000)
        else:
            plot_era5var = eradat[era_var].sel(Time=timestr_f) / 1000

    # Create a figure
    fig = plt.figure(figsize=(6.5, 2.4))

    # Set the GeoAxes to the projection used by WRF
    ax_wrf = fig.add_subplot(1, 2, 1, projection=wrf_cartopy_proj)
    ax_era5 = fig.add_subplot(1, 2, 2, projection=wrf_cartopy_proj, sharey=ax_wrf)

    # Get, format, and set the map bounds
    # I need to manually convert the boundaries of the WRF domain into Plate Carree to set the limits.
    # Get the raw map bounds using a wrf-python utility
    raw_bounds = wrfpy.util.geo_bounds(wrfdat[wrf_var])
    # Get the projected bounds telling cartopy that the input coordinates are lat/lon (Plate Carree)
    proj_bounds = wrf_cartopy_proj.transform_points(ccrs.PlateCarree(),
                                                    np.array([raw_bounds.bottom_left.lon, raw_bounds.top_right.lon]),
                                                    np.array([raw_bounds.bottom_left.lat, raw_bounds.top_right.lat]))
    # Format the projected bounds so they can be used in the xlim and ylim attributes
    proj_xbounds = [proj_bounds[0, 0], proj_bounds[1, 0]]
    proj_ybounds = [proj_bounds[0, 1], proj_bounds[1, 1]]
    # Finally, set the x and y limits
    ax_wrf.set_xlim(proj_xbounds)
    ax_wrf.set_ylim(proj_ybounds)
    ax_era5.set_xlim(proj_xbounds)
    ax_era5.set_ylim(proj_ybounds)

    # Download and add the states, coastlines, and lakes
    states = cfeature.NaturalEarthFeature(category="cultural", scale="50m",
                                          facecolor="none",
                                          name="admin_1_states_provinces_shp")

    # Add features to the maps
    ax_wrf.add_feature(states, linewidth=.5, edgecolor="black")
    ax_wrf.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
    ax_wrf.add_feature(cfeature.OCEAN.with_scale('50m'))
    ax_era5.add_feature(states, linewidth=.5, edgecolor="black")
    ax_era5.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
    ax_era5.add_feature(cfeature.OCEAN.with_scale('50m'))

    # Make the countour lines for filled contours for the GHI
    if hourly:
        if var == 'ghi':
            contour_levels = np.linspace(0, 0.75, 22)
        elif var == 'wpd':
            contour_levels = np.linspace(0, 10000, 22)
    else:
        if var == 'ghi':
            contour_levels = np.linspace(0, 5, 22)
        elif var == 'wpd':
            contour_levels = np.linspace(0, np.amax(wrfpy.to_np(plot_wrfvar)), 22)

    # Add the filled contour levels
    if var == 'ghi':
        color_map = get_cmap("hot_r")
    elif var == 'wpd':
        color_map = get_cmap("Greens")
    wrf_cn = ax_wrf.contourf(wrfpy.to_np(lons), wrfpy.to_np(lats), wrfpy.to_np(plot_wrfvar),
                             contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)
    era5_cn = ax_era5.contourf(wrfpy.to_np(eradat.longitude), wrfpy.to_np(eradat.latitude), wrfpy.to_np(plot_era5var),
                               contour_levels, transform=era5_cartopy_proj, cmap=color_map)

    # Add a color bar
    plt.colorbar(era5_cn, ax=ax_era5, shrink=.98)

    # Add the axis title
    ax_wrf.set_title('WRF ' + title_str)
    ax_era5.set_title('ERA5 ' + title_str)

    # Save the figure(s)
    if save_fig:
        if hourly:
            plt.savefig(fig_path + '.png', dpi=300, transparent=True, bbox_inches='tight')
        else:
            plt.savefig(fig_path + '.pdf', transparent=True, bbox_inches='tight')
    plt.show()
