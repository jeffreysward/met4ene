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


def get_wrf_proj(wrfdata, var):
    """
    Extracts the WRF projection information from the variable string attribute.

    :param wrfdata:
    :param var:
    :return:
    """
    # I have to do this tedious string parsing below to get the projection from the processed wrfout file.
    try:
        wrf_proj_params = wrfdata[var].attrs['projection']
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
        wrf_cartopy_crs = ccrs.LambertConformal(central_longitude=stand_lon,
                                                central_latitude=moad_cen_lat,
                                                standard_parallels=[truelat1, truelat2])
        return wrf_cartopy_crs
    else:
        print('Your WRF projection is not the expected Lambert Conformal.')
        raise ValueError


def get_domain_boundary(wrfds, var, cartopy_crs):
    """
    Finds the boundary of the WRF domain.

    :param wrfds:
    :param var:
    :param cartopy_crs:
    :return:
    """
    # Rename the lat-lon corrdinates to get wrf-python to recognize them
    variables = {'lat': 'XLAT',
                 'lon': 'XLONG'}
    try:
        wrfds = xr.Dataset.rename(wrfds, variables)
    except ValueError:
        print(f'Variables {variables} cannot be renamed, '
              f'those on the left are not in this dataset.')

    # I need to manually convert the boundaries of the WRF domain into Plate Carree to set the limits.
    # Get the raw map bounds using a wrf-python utility
    raw_bounds = wrfpy.util.geo_bounds(wrfds[var])

    # Get the projected bounds telling cartopy that the input coordinates are lat/lon (Plate Carree)
    projected_bounds = cartopy_crs.transform_points(ccrs.PlateCarree(),
                                                    np.array([raw_bounds.bottom_left.lon, raw_bounds.top_right.lon]),
                                                    np.array([raw_bounds.bottom_left.lat, raw_bounds.top_right.lat]))
    return projected_bounds


def format_cnplot_axis(axis, cn, proj_bounds, title_str='Contour Plot'):
    """
    Formats a contour plot axis.

    :param axis:
    :param cn:
    :param proj_bounds:
    :param title_str:
    :return:
    """
    # Format the projected bounds so they can be used in the xlim and ylim attributes
    proj_xbounds = [proj_bounds[0, 0], proj_bounds[1, 0]]
    proj_ybounds = [proj_bounds[0, 1], proj_bounds[1, 1]]

    # Finally, set the x and y limits
    axis.set_xlim(proj_xbounds)
    axis.set_ylim(proj_ybounds)

    # Download and add the states, coastlines, and lakes
    states = cfeature.NaturalEarthFeature(category="cultural", scale="50m",
                                          facecolor="none",
                                          name="admin_1_states_provinces_shp")

    # Add features to the maps
    axis.add_feature(states, linewidth=.5, edgecolor="black")
    axis.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
    axis.add_feature(cfeature.OCEAN.with_scale('50m'))

    # Add color bars
    plt.colorbar(cn, ax=axis, shrink=.7)

    # Add the axis title
    axis.set_title(title_str)


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

    # To start, we need to get the WRF map projection information (a Lambert Conformal grid),
    # and find the domain boundaries in this projection.
    # NOTE: this task MUST occurr before we regrid the WRF variables or the coordinates change and become incompatible.
    wrf_cartopy_proj = get_wrf_proj(wrfdat, 'dni')
    proj_bounds = get_domain_boundary(wrfdat, 'ghi', wrf_cartopy_proj)

    # # Rename the lat-lon corrdinates to get wrf-python to recognize them
    # variables = {'lat': 'XLAT',
    #              'lon': 'XLONG'}
    # try:
    #     wrfdat = xr.Dataset.rename(wrfdat, variables)
    # except ValueError:
    #     print(f'Variables {variables} cannot be renamed, '
    #           f'those on the left are not in this dataset.')
    #
    # # This makes it easy to get the latitude and longitude coordinates with the wrf-python function below
    # lats, lons = wrfpy.latlon_coords(wrfdat['dni'])
    #
    # # I have to do this tedious string parsing below to get the projection from the processed wrfout file.
    # try:
    #     wrf_proj_params = wrfdat.dni.attrs['projection']
    # except AttributeError:
    #     raise ValueError('Variable does not contain projection information')
    # wrf_proj_params = wrf_proj_params.replace('(', ', ')
    # wrf_proj_params = wrf_proj_params.replace(')', '')
    # wrf_proj_params = wrf_proj_params.split(',')
    # wrf_proj = wrf_proj_params[0]
    # stand_lon = float(wrf_proj_params[1].split('=')[1])
    # moad_cen_lat = float(wrf_proj_params[2].split('=')[1])
    # truelat1 = float(wrf_proj_params[3].split('=')[1])
    # truelat2 = float(wrf_proj_params[4].split('=')[1])
    # pole_lat = float(wrf_proj_params[5].split('=')[1])
    # pole_lon = float(wrf_proj_params[6].split('=')[1])
    #
    # # Fortunately, it still apppears to work.
    # if wrf_proj == 'LambertConformal':
    #     wrf_cartopy_proj = ccrs.LambertConformal(central_longitude=stand_lon,
    #                                              central_latitude=moad_cen_lat,
    #                                              standard_parallels=[truelat1, truelat2])
    # else:
    #     print('Your WRF projection is not the expected Lambert Conformal.')
    #     raise ValueError
    #
    # # I need to manually convert the boundaries of the WRF domain into Plate Carree to set the limits.
    # # Get the raw map bounds using a wrf-python utility
    # raw_bounds = wrfpy.util.geo_bounds(wrfdat['dni'])
    # # Get the projected bounds telling cartopy that the input coordinates are lat/lon (Plate Carree)
    # proj_bounds = wrf_cartopy_proj.transform_points(ccrs.PlateCarree(),
    #                                                 np.array([raw_bounds.bottom_left.lon, raw_bounds.top_right.lon]),
    #                                                 np.array([raw_bounds.bottom_left.lat, raw_bounds.top_right.lat]))

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

            # # Get, format, and set the map bounds
            #
            # # Format the projected bounds so they can be used in the xlim and ylim attributes
            # proj_xbounds = [proj_bounds[0, 0], proj_bounds[1, 0]]
            # proj_ybounds = [proj_bounds[0, 1], proj_bounds[1, 1]]
            # # Finally, set the x and y limits
            # ax.set_xlim(proj_xbounds)
            # ax.set_ylim(proj_ybounds)
            #
            # # Download and add the states, coastlines, and lakes
            # states = cfeature.NaturalEarthFeature(category="cultural", scale="50m",
            #                                       facecolor="none",
            #                                       name="admin_1_states_provinces_shp")
            #
            # # Add features to the maps
            # ax.add_feature(states, linewidth=.5, edgecolor="black")
            # ax.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
            # ax.add_feature(cfeature.OCEAN.with_scale('50m'))

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
                cn = ax.contourf(wrfpy.to_np(wrfdat.lat), wrfpy.to_np(wrfdat.lon), wrfpy.to_np(plot_var),
                                 contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)
            else:
                cn = ax.contourf(wrfpy.to_np(eradat.longitude), wrfpy.to_np(eradat.latitude), wrfpy.to_np(plot_var),
                                 contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)

            # Format the plot
            format_cnplot_axis(ax, cn, proj_bounds, title_str=title_str)

            # # Add a color bar
            # plt.colorbar(cn, ax=ax, shrink=.98)

            # # Add the axis title
            # ax.set_title(title_str)

            # Save the figure(s)
            if save_fig:
                fig_path_temp = fig_path + str(tidx).zfill(2)
                plt.savefig(fig_path_temp + '.png', dpi=300, transparent=True, bbox_inches='tight')

            plt.show()

    # Create a figure
    fig = plt.figure(figsize=(4, 4))

    # Set the GeoAxes to the projection used by WRF
    ax = fig.add_subplot(1, 1, 1, projection=wrf_cartopy_proj)

    # # Get, format, and set the map bounds
    #
    # # Format the projected bounds so they can be used in the xlim and ylim attributes
    # proj_xbounds = [proj_bounds[0, 0], proj_bounds[1, 0]]
    # proj_ybounds = [proj_bounds[0, 1], proj_bounds[1, 1]]
    # # Finally, set the x and y limits
    # ax.set_xlim(proj_xbounds)
    # ax.set_ylim(proj_ybounds)
    #
    # # Download and add the states, coastlines, and lakes
    # states = cfeature.NaturalEarthFeature(category="cultural", scale="50m",
    #                                       facecolor="none",
    #                                       name="admin_1_states_provinces_shp")
    #
    # # Add features to the maps
    # ax.add_feature(states, linewidth=.5, edgecolor="black")
    # ax.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.9)
    # ax.add_feature(cfeature.OCEAN.with_scale('50m'))

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
        cn = ax.contourf(wrfpy.to_np(wrfdat.lat), wrfpy.to_np(wrfdat.lat), wrfpy.to_np(plot_var),
                         contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)
    else:
        cn = ax.contourf(wrfpy.to_np(eradat.longitude), wrfpy.to_np(eradat.latitude), wrfpy.to_np(plot_var),
                         contour_levels, transform=ccrs.PlateCarree(), cmap=color_map)

    # Format the plot
    format_cnplot_axis(ax, cn, proj_bounds, title_str=title_str)

    # # Add a color bar
    # plt.colorbar(cn, ax=ax, shrink=.98)
    #
    # # Add the axis title
    # ax.set_title(title_str)

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
            contour_levels = np.linspace(0, 35000, 22)

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
    ax_wrf.set_title('OptWRF ' + title_str)
    ax_era5.set_title('ERA5 ' + title_str)

    # Save the figure(s)
    if save_fig:
        if hourly:
            plt.savefig(fig_path + '.png', dpi=300, transparent=True, bbox_inches='tight')
        else:
            plt.savefig(fig_path + '.pdf', transparent=True, bbox_inches='tight')
    plt.show()


def wrf_errorandfitness_plot(wrfdata, save_fig=False, wrf_dir='./', era_dir='./',
                             fig_path='./', verbose=False, fitness_short_title='Model Fitness',
                             ghi_error_short_title='GHI Error (kWh m-2 day-1)',
                             wpd_error_short_title='WPD Error (kWh m-2 day-1)'):
    """

    :return:
    """
    # Get the start_date and create the date string
    start_date = str(wrfdata.Time.dt.strftime('%b %d %Y')[0].values)

    # To start, we need to get the WRF map projection information (a Lambert Conformal grid),
    # and find the domain boundaries in this projection.
    # NOTE: this task MUST occurr before we regrid the WRF variables or the coordinates change and become incompatible.
    wrf_cartopy_proj = get_wrf_proj(wrfdata, 'dni')
    proj_bounds = get_domain_boundary(wrfdata, 'ghi', wrf_cartopy_proj)
    if verbose:
        print(f'WRF Projection:\n{wrf_cartopy_proj}')
        print(f'\nDomain Boundaries:\n{proj_bounds}')

    # Regrid the wrf GHI and WPD
    input_year = helper_functions.format_date(start_date).strftime('%Y')
    input_month = helper_functions.format_date(start_date).strftime('%m')
    wrfdata, eradata = runwrf.wrf_era5_regrid_xesmf(input_year, input_month,
                                                    wrfdir=wrf_dir, eradir=era_dir)
    # Calculate the error in GHI and WPD
    wrfdata = runwrf.wrf_era5_error(wrfdata, eradata)

    # Calculate the fitness
    correction_factor = 0.0004218304553577255
    daylight_factor = helper_functions.daylight_frac(start_date)  # daylight fraction
    wrfdata['fitness'] = daylight_factor * wrfdata.total_ghi_error + correction_factor * wrfdata.total_wpd_error

    # Create a figure
    fig = plt.figure(figsize=(9.5, 3))

    # Set the GeoAxes to the projection used by WRF
    ax_fitness = fig.add_subplot(1, 3, 1, projection=wrf_cartopy_proj)
    ax_ghierr = fig.add_subplot(1, 3, 2, projection=wrf_cartopy_proj, sharey=ax_fitness)
    ax_wpderr = fig.add_subplot(1, 3, 3, projection=wrf_cartopy_proj, sharey=ax_ghierr)

    # Create the filled contour levels
    fitness_cn = ax_fitness.contourf(wrfpy.to_np(wrfdata.lon), wrfpy.to_np(wrfdata.lat),
                                     wrfpy.to_np(wrfdata['fitness']),
                                     np.linspace(0, np.amax(wrfdata['fitness']), 22),
                                     transform=ccrs.PlateCarree(), cmap=get_cmap("Greys"))
    ghierr_cn = ax_ghierr.contourf(wrfpy.to_np(wrfdata.lon), wrfpy.to_np(wrfdata.lat),
                                   wrfpy.to_np(wrfdata['total_ghi_error']),
                                   np.linspace(0, np.amax(wrfdata['total_ghi_error']), 22),
                                   transform=ccrs.PlateCarree(), cmap=get_cmap("hot_r"))
    wpderr_cn = ax_wpderr.contourf(wrfpy.to_np(wrfdata.lon), wrfpy.to_np(wrfdata.lat),
                                   wrfpy.to_np(wrfdata['total_wpd_error']),
                                   np.linspace(0, np.amax(wrfdata['total_wpd_error']), 22),
                                   transform=ccrs.PlateCarree(), cmap=get_cmap("Greens"))

    # Format the axes
    time_string_f = wrfdata.Time[0].dt.strftime('%b %d, %Y')
    format_cnplot_axis(ax_fitness, fitness_cn, proj_bounds,
                       title_str=f'{fitness_short_title}\n{time_string_f.values}')
    format_cnplot_axis(ax_ghierr, ghierr_cn, proj_bounds,
                       title_str=f'{ghi_error_short_title}\n{time_string_f.values}')
    format_cnplot_axis(ax_wpderr, wpderr_cn, proj_bounds,
                       title_str=f'{wpd_error_short_title}\n{time_string_f.values}')
    if save_fig:
        print('Saving figure...')
        plt.savefig(fig_path + '.pdf', transparent=True, bbox_inches='tight')

    plt.show()


