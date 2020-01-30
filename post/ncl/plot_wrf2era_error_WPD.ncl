;----------------------------------------------------------------------
; plot_wrf2era_error_WPD.ncl
;
; This is an NCL/ESMF regridding from a WRF
; (curvilinear) grid to the ERA5 grid. It uses
; ESMF_regrid to do the regridding.
;
; This function takes the year, month, day, WRFdir - so it can locate the
; wrfout file and the corresponding ERA5 data - and paramstr to define
; the output file name as inputs and computes a single mean absolute
; error (MAE) across the entire domain for two different variables,
; global horizontal irradiance (GHI_MAE) and wind power density (WPD_MAE),
; which are written to a csv file named mae_wrf2era_<parmstr>.csv.
;
; Here is a syntax example of calling this script:
; ncl in_yr=2011 in_mo=01 in_da=15 'WRFdir="/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2011-01-15_10mp1lw1sw2lsm2pbl3cu/"' 'paramstr="10mp1lw1sw2lsm2pbl3cu"' plot_wrf2era_error_WPD.ncl
;
;----------------------------------------------------------------------
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/esmf/ESMF_regridding.ncl"

begin
;---WRF file containing source grid 
    WRFfile  = "wrfout_processed_d01.nc"
    if (fileexists(WRFdir+WRFfile)) then
        sfile = addfile(WRFdir+WRFfile, "r")
    else
        print("")
        print("The wrfout file "+WRFdir+WRFfile+" does not exist. Check that your path.")
        print("")
        exit
    end if

;---Get wrf variable(s) to regrid
    wrf_lat = sfile->XLAT
    wrf_lon = sfile->XLONG
    wrf_time = sfile->Times
    print(wrf_time(0))
    GHI     = sfile->ghi
    WPD     = sfile->wpd

    ;---Array to hold month abbreviations. Don't store anything in index
    ; '0' (i.e. let index 1=Jan, 2=Feb, ..., index 12=Dec).
    month_abbr = (/"","01","02","03","04","05","06","07","08","09", \
                    "10","11","12"/)

    ;---Convert to global UTC time.
    wrf_time_UTC = cd_calendar(wrf_time, 0)
    ;printVarSummary(wrf_time_UTC)

    ;---Store return information into more meaningful variables.
    year   = tointeger(wrf_time_UTC(:,0))    ; Convert to integer for
    month  = tointeger(wrf_time_UTC(:,1))    ; use sprinti
    day    = tointeger(wrf_time_UTC(:,2))
    hour   = tointeger(wrf_time_UTC(:,3))

    ;---Write out strings in the format "yyyy-mm-dd_hh:mm:ss"
    wrf_datestr = sprinti("%0.4i", year) + "-" + month_abbr(month) + "-" + sprinti("%0.2i", day) + \
                "_" + sprinti("%0.2i", hour) + ":00:00"
    print(wrf_datestr(0))

;---ERA data file(s)
    ERAdir   = "/share/mzhang/jas983/wrf_data/data/ERA5/"
    ERAfile  = "ERA5_EastUS_WPD-GHI_" + sprinti("%0.4i", in_yr) + "-" + sprinti("%0.2i", in_mo) +  ".nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The ERA data file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if

    ERA_lat  = dfile->latitude
    ERA_lon  = dfile->longitude
    ERA_time = dfile->time
    print(ERA_time(0))
    ERA_GHI  = dfile->GHI
    ERA_WPD  = dfile->WPD

    ;---Convert to global UTC time.
    ERA_time_UTC = cd_calendar(ERA_time, 0)
    ;printVarSummary(ERA_time_UTC)

    ;---Store return information into more meaningful variables.
    year   = tointeger(ERA_time_UTC(:,0))    ; Convert to integer for
    month  = tointeger(ERA_time_UTC(:,1))    ; use sprinti
    day    = tointeger(ERA_time_UTC(:,2))
    hour   = tointeger(ERA_time_UTC(:,3))

    ;---Write out strings in the format "yyyy-mm-dd_hh:mm:ss"
    ERA_datestr = sprinti("%0.4i", year) + "-" + month_abbr(month) + "-" + sprinti("%0.2i", day) + \
                "_" + sprinti("%0.2i", hour) + ":00:00"
    print(ERA_datestr(0))
    ;printVarSummary(ERA_datestr)
    ;printVarSummary(ERA_GHI)
    ;printVarSummary(ERA_WPD)

;---Set up regridding options
    Opt                   = True

    ;---"bilinear" is the default. "patch" and "conserve" are other options.
    Opt@InterpMethod      = "patch"        ;;---Change (maybe)

    Opt@WgtFileName       = "WRF_to_ERA5.nc"

    Opt@SrcGridLat        = wrf_lat           ; source grid
    Opt@SrcGridLon        = wrf_lon
    Opt@SrcRegional       = True              ;;--Change (maybe)
    Opt@SrcInputFileName  = sfile             ; optional, but good idea

    Opt@DstGridLat        = ERA_lat           ; destination grid
    Opt@DstGridLon        = ERA_lon
    Opt@DstRegional       = True              ;;--Change (maybe)
;    Opt@DstMask2D = where(.not.ismissing(ERA_lat).and.\
;                          .not.ismissing(ERA_lon),1,0) ; Necessary if lat/lon
;                                                       ; has missing values.
    Opt@ForceOverwrite    = True
;    Opt@PrintTimings      = True
;    Opt@Debug             = True

;---Do the regridding
    GHI_regrid = ESMF_regrid(GHI,Opt)
    WPD_regrid = ESMF_regrid(WPD,Opt)

    ;printVarSummary(GHI_regrid)
    ;printVarSummary(WPD_regrid)

;---Loop through all the times in the WRF file to compute mean bias
    ntimes = dimsizes(wrf_time)                 ; number of times in the file
    n = 1
    GHI_MAE = 0
    WPD_MAE = 0
    do iwrf = 0,ntimes-1,72                       ; TIME LOOP <-------- MAKE SURE TO RESET THIS LINE TO: 0,ntimes-1,1
        print("The wrf time is:" + wrf_datestr(iwrf))
        iera = str_match_ind(ERA_datestr, wrf_datestr(iwrf))
        ;---Compute difference between ERA5 variable and WRF variable(s)
        GHI_diff = abs(GHI_regrid(iwrf,:,:) - ERA_GHI(iera,:,:))
        GHI_diff!0 = "lat"
        GHI_diff!1 = "lon"
        GHI_diff&lat = ERA_lat
        GHI_diff&lon = ERA_lon
        ;printVarSummary(GHI_diff)

        WPD_diff = abs(WPD_regrid(iwrf,:,:) - ERA_GHI(iera,:,:))
        WPD_diff!0 = "lat"
        WPD_diff!1 = "lon"
        WPD_diff&lat = ERA_lat
        WPD_diff&lon = ERA_lon
        ;printVarSummary(WPD_diff)

        ;---Sum all computed biases across the domain
        ;***May need to set the missing values for all the *_diff variables.
        GHI_MAE := GHI_MAE + sum(GHI_diff)
        WPD_MAE := WPD_MAE + sum(WPD_diff)

        ;----------------------------------------------------------------------
        ; Plotting section
        ;
        ; This section creates filled contour plots of both the original
        ; data and the regridded data, and panels them.
        ;----------------------------------------------------------------------
        WPD@lat2d = wrf_lat     ; Needed for plotting. "t2_regrid"
        WPD@lon2d = wrf_lon     ; already has these attrs attached.

        wks = gsn_open_wks("x11", outfile)

        res                       = True
        res@gsnMaximize           = True
        res@gsnDraw               = False
        res@gsnFrame              = False

        ;-- Set the center string to time
        res@gsnCenterString        = wrf_datestr           ;-- write time to center string
        res@gsnCenterStringOrthogonalPosF = 0.05        ;-- move center string upwards

        res@cnFillOn              = True
        res@cnLinesOn             = False
        res@cnLineLabelsOn        = False
        res@cnFillMode            = "RasterFill"

        res@lbLabelBarOn          = False    ; Turn on later in panel
        res@mpDataBaseVersion     = "MediumRes"
        res@mpMinLatF             = min(wrf_lat)
        res@mpMaxLatF             = max(wrf_lat)
        res@mpMinLonF             = min(wrf_lon)
        res@mpMaxLonF             = max(wrf_lon)
        d_res                     = res
        d_res@lbLabelBarOn        = True

        ;--Set contour spacing interval         Change (maybe)
        mnmxint = nice_mnmxintvl( min(WPD(iwrf,:,:)), max(WPD(iwrf,:,:)), 18, False)
        res@cnLevelSelectionMode  = "ManualLevels"
        res@cnMinLevelValF        = mnmxint(0)
        res@cnMaxLevelValF        = mnmxint(1)
        res@cnLevelSpacingF       = mnmxint(2)

        mnmxint = nice_mnmxintvl( min(WPD_diff), max(WPD_diff), 18, False)
        d_res@cnLevelSelectionMode  = "ManualLevels"
        ;d_res@cnMinLevelValF      = -mnmxint(1)
        ;d_res@cnMaxLevelValF      = mnmxint(1)
        ;d_res@cnLevelSpacingF     = mnmxint(2)
        d_res@cnMinLevelValF      = -10
        d_res@cnMaxLevelValF      = 10
        d_res@cnLevelSpacingF     = 2

        ;---Resources for plotting regridded data
        res@gsnAddCyclic  = False            ;;---Change (maybe)
        res@tiMainString  = "Curvilinear grid (" + Opt@InterpMethod + ")"

        plot_regrid = gsn_csm_contour_map(wks,WPD_regrid(iwrf,:,:),res)

        ;---Resources for plotting original data
        res@gsnAddCyclic = False            ;;---Change (maybe)
        res@tiMainString = "Original WRF grid"

        plot_orig = gsn_csm_contour_map(wks,WPD(iwrf,:,:),res)

        ;---Resources for plotting difference in WRF and ERA5 data
        d_res@gsnAddCyclic           = False            ;;---Change (maybe)
        d_res@tiMainString           = "WRF & ERA5 Difference"
        d_res@lbTitleString          = "Wind Power Density Difference (W/m -2)"
        d_res@lbTitleOffsetF         = -0.25            ;-- move the color bar label down
        d_res@lbTitleFontHeightF     = 0.02
        d_res@lbLabelFontHeightF     = 0.012
        cmap = read_colormap_file("BlueDarkRed18")      ;-- so we can subset later
        d_res@cnFillPalette          = cmap(:,:)        ;-- subset the color map
        d_res@pmLabelBarOrthogonalPosF = 0.15           ;-- move th color bar down
        plot_diff = gsn_csm_contour_map(wks,WPD_diff,d_res)

        ;---Compare the plots in a panel
        pres                   = True
        pres@gsnMaximize       = True
        pres@gsnPanelLabelBar  = True
        gsn_panel(wks,(/plot_orig,plot_regrid/),(/2,1/),pres)

        ;---Plot the difference
        draw(plot_diff)
        frame(wks)

        n := n + 1
    end do        ; END OF TIME LOOP

;---Compute the mean bias and save/print
    n := n - 1
    GHI_MAE := GHI_MAE/n
    WPD_MAE := WPD_MAE/n

end
