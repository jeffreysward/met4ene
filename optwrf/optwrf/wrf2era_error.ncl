;----------------------------------------------------------------------
; wrf2era_error.ncl
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
; ncl in_yr=2011 in_mo=01 in_da=10 'WRFdir="/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2011-01-10_10mp1lw1sw2lsm2pbl2cu/"' 'paramstr="10mp1lw1sw2lsm2pbl2cu"' wrf2era_error.ncl
;
;----------------------------------------------------------------------
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/esmf/ESMF_regridding.ncl"

begin
;---WRF file containing source grid (the first two commented lines with WRFdir = "..." are for testing purposes only)
;    WRFdir = "/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2011-01-16_10mp1lw1sw2lsm2pbl2cu/"
;    WRFdir   = "/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/" + sprinti("%0.4i", in_yr) + "-" + sprinti("%0.2i", in_mo) + "-" + sprinti("%0.2i", in_da) + "_10mp1lw1sw2lsm2pbl2cu/"
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
    wrf_time = sfile->Time
    GHI     = sfile->ghi
    WPD     = sfile->wpd

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

    ;---Array to hold month abbreviations. Don't store anything in index
    ; '0' (i.e. let index 1=Jan, 2=Feb, ..., index 12=Dec).
    month_abbr = (/"","01","02","03","04","05","06","07","08","09", \
                    "10","11","12"/)

    ;---Convert to UTC time. (I THINK THIS IS NO LONGER NECESSARY, SO I COMMENTED IT OUT)
    ;---(turn out it was necessary...)
    utc_time_ERA = cd_calendar(ERA_time, 0)
    ;utc_time_ERA = ERA_time
    printVarSummary(utc_time_ERA)

    ;---Store return information into more meaningful variables.
    year   = tointeger(utc_time_ERA(:,0))    ; Convert to integer for
    month  = tointeger(utc_time_ERA(:,1))    ; use sprinti
    day    = tointeger(utc_time_ERA(:,2))
    hour   = tointeger(utc_time_ERA(:,3))

    ;---Write out strings in the format "yyyy-mm-dd_hh:mm:ss"
    date_str = sprinti("%0.4i", year) + "-" + month_abbr(month) + "-" + sprinti("%0.2i", day) + \
                "_" + sprinti("%0.2i", hour) + ":00:00"
    ERA_GHI  = dfile->GHI
    ERA_WPD  = dfile->WPD

    printVarSummary(ERA_GHI)
    printVarSummary(ERA_WPD)

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

    printVarSummary(GHI_regrid)
    printVarSummary(WPD_regrid)

;---Loop through all the times in the WRF file to compute mean bias
    ntimes = dimsizes(wrf_time)                 ; number of times in the file
    n = 1
    GHI_MAE = 0
    WPD_MAE = 0
    do iwrf = 0,ntimes-1,72                       ; TIME LOOP <-------- MAKE SURE TO RESET THIS LINE TO: 0,ntimes-1,1
        print("The iwrf time indes is:")
        print(iwrf)
        iera = str_match_ind(date_str, wrf_time(iwrf))
        print("The iera time indes is:")
        print(iera)
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

        n := n + 1
    end do        ; END OF TIME LOOP

;---Compute the mean bias and save/print
    n := n - 1
    GHI_MAE := GHI_MAE/n
    WPD_MAE := WPD_MAE/n

    dq = str_get_dq()                ; double quote character
    csv_filename = "mae_wrfyera_" + paramstr + ".csv"

    fields = (/"GHI_MAE", "WPD_MAE"/)
    fields = dq + fields + dq           ; Pre/append quotes to field names
    header = [/str_join(fields,", ")/]  ; Header is field names separated by commas.
    alist  = [/GHI_MAE, WPD_MAE/]        ; List of variables to write.
    format = "%7.2f,%7.2f"              ; Format to use for each variable.

    if (fileexists(csv_filename)) then
        write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
    else
        write_table(csv_filename, "w", header, "%s")   ; Write header to CSV file.
        write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
    end if

end
