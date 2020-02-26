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

;---Get wrf variable(s) to regrid, and format them for NCL.
    wrf_lat = sfile->XLAT
    wrf_lon = sfile->XLONG
    wrf_time_raw = sfile->Times
    ;---The Times variable from wrf in datetime64 python format; NCL requires integer
    wrf_time = toint(wrf_time_raw)
    ;---Assign the units and calendar attributes to the integer time variable
    wrf_time@units = wrf_time_raw@units
    wrf_time@calendar = wrf_time_raw@calendar
    ;---Read in and convert GHI from W m-2 to kW m-2
    GHI = sfile->ghi
    GHI = GHI/1000
    GHI@units = "kW m-2"
    ;---Python uses nan to denote missing data, which is not recognized by NCL, so
    ;---we must reset the default _FillValue to get NCL to regrid and carry out
    ;---calcualtions correctly.
    GHI@_FillValue = default_fillvalue("float")
    ;---For some reason, some nans may be left even after resetting the default_fillvalue()
    ;---Therefore, we account for this using the following replace_ieenan function.
    if (any(isnan_ieee(GHI))) then
        replace_ieeenan (GHI, GHI@_FillValue, 0)
    end if
    ;---Read in WPD, convert from W m-2 to kW m-2, and reset the default _FillValue
    WPD = sfile->wpd
    WPD = WPD/1000
    WPD@units = "kW m-2"
    WPD@_FillValue = default_fillvalue("float")
    if (any(isnan_ieee(WPD))) then
        replace_ieeenan (WPD, WPD@_FillValue, 0)
    end if
    ;printVarSummary(GHI)
    ;printVarSummary(WPD)

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
    print("First WRF time: " + wrf_datestr(0))
    print("Last WRF time: " + wrf_datestr(dimsizes(wrf_datestr) - 1))

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

    ;---Get variables to compare with regridded WRF variables.
    ERA_lat  = dfile->latitude
    ERA_lon  = dfile->longitude
    ERA_time = dfile->time
    ;---Read in ERA_GHI, convert from W m-2 to kW m-2, and reset the default _FillValue
    ERA_GHI  = dfile->GHI
    ERA_GHI  = ERA_GHI/1000
    ERA_GHI@units = "kW m-2"
    print("Before _FillValue reset: " + ERA_GHI(0,0,0))
    ERA_GHI@_FillValue = default_fillvalue("float")
    print("After _FillValue reset: " + ERA_GHI(0,0,0))
    if (any(isnan_ieee(ERA_GHI))) then
        replace_ieeenan (ERA_GHI, ERA_GHI@_FillValue, 0)
    end if
    print("After replace_ieeenan: " + GHI(0,0,0))
    ;---Read in ERA_WPD, convert from W m-2 to kW m-2, and reset the default _FillValue
    ERA_WPD  = dfile->WPD
    ERA_WPD  = ERA_WPD/1000
    ERA_WPD@units = "kW m-2"
    ERA_WPD@_FillValue = default_fillvalue("float")
    if (any(isnan_ieee(ERA_WPD))) then
        replace_ieeenan (ERA_WPD, ERA_WPD@_FillValue, 0)
    end if
    ;printVarSummary(ERA_GHI)
    ;printVarSummary(ERA_WPD)

    ;---Convert to global UTC time.
    ERA_time_UTC = cd_calendar(ERA_time, 0)
    ;printVarSummary(ERA_time_UTC)

    ;---Store return information into more meaningful variables.
    year_ERA   = tointeger(ERA_time_UTC(:,0))    ; Convert to integer for
    month_ERA  = tointeger(ERA_time_UTC(:,1))    ; use sprinti
    day_ERA    = tointeger(ERA_time_UTC(:,2))
    hour_ERA   = tointeger(ERA_time_UTC(:,3))

    ;---Write out strings in the format "yyyy-mm-dd_hh:mm:ss"
    ERA_datestr = sprinti("%0.4i", year_ERA) + "-" + month_abbr(month_ERA) + "-" + sprinti("%0.2i", day_ERA) + \
                "_" + sprinti("%0.2i", hour_ERA) + ":00:00"
    print("First ERA time: " + ERA_datestr(0))
    print("Last ERA time: " + ERA_datestr(dimsizes(ERA_datestr) - 1))

    ;---Misc variables
    dq = str_get_dq()                ; double quote character
    csv_filename = WRFdir + "mae_wrfyera_" + paramstr + ".csv"
    ;---Remove potential existing mae_wrfyera_* file
    if (fileexists(csv_filename)) then
        system("rm " + csv_filename)
    end if

;---Set up regridding options
    Opt                   = True

    ;---"bilinear" is the default. "patch" and "conserve" are other options.
    Opt@InterpMethod      = "bilinear"           ;;---Change (maybe)

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
    do iwrf = 0,ntimes-1,1                      ; TIME LOOP <-------- MAKE SURE TO RESET THIS LINE TO: 0,ntimes-1,1
        ;print("The wrf time is: " + wrf_datestr(iwrf))
        iera = str_match_ind(ERA_datestr, wrf_datestr(iwrf))
        ;---Compute absoulute difference between ERA5 variable and WRF variable(s)
        GHI_diff = abs(GHI_regrid(iwrf,:,:) - ERA_GHI(iera,:,:))
        GHI_diff!0 = "lat"
        GHI_diff!1 = "lon"
        GHI_diff&lat = ERA_lat
        GHI_diff&lon = ERA_lon
        GHI_diff@_FillValue = default_fillvalue("float")
        if (any(isnan_ieee(GHI_diff))) then
            replace_ieeenan (GHI_diff, GHI_diff@_FillValue, 0)
        end if
        ;printVarSummary(GHI_diff)

        WPD_diff = abs(WPD_regrid(iwrf,:,:) - ERA_WPD(iera,:,:))
        WPD_diff!0 = "lat"
        WPD_diff!1 = "lon"
        WPD_diff&lat = ERA_lat
        WPD_diff&lon = ERA_lon
        WPD_diff@_FillValue = default_fillvalue("float")
        if (any(isnan_ieee(WPD_diff))) then
            replace_ieeenan (WPD_diff, WPD_diff@_FillValue, 0)
        end if
        ;printVarSummary(WPD_diff)

        ;---Sum all computed biases across the domain and save/print
        GHI_MAE_hr = sum(GHI_diff)
        WPD_MAE_hr = sum(WPD_diff)
        ;print("The hourly bias in GHI is: " + GHI_MAE_hr + " " + GHI@units)
        ;print("The hourly bias in WPD is: " + WPD_MAE_hr + " " + WPD@units)

        fields = (/"Date/Time", "GHI_MAE_hr", "WPD_MAE_hr"/) ; Define field names
        fields = dq + fields + dq               ; Pre/append quotes to field names
        header = [/str_join(fields,", ")/]      ; Header is field names separated by commas
        alist  = [/wrf_datestr(iwrf), GHI_MAE_hr, WPD_MAE_hr/]     ; List of variables to write
        format = "%s,%7.2f,%7.2f"                  ; Format to use for each variable
        if (fileexists(csv_filename)) then
            write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
        else
            write_table(csv_filename, "w", header, "%s")   ; Write header to CSV file.
            write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
        end if

        ;---Update the accumulated biases
        GHI_MAE := GHI_MAE + GHI_MAE_hr
        WPD_MAE := WPD_MAE + WPD_MAE_hr

        n := n + 1
    end do        ; END OF TIME LOOP

;---Compute the mean bias and save/print
    n := n - 1
    GHI_MAE := GHI_MAE/n
    WPD_MAE := WPD_MAE/n
    ;print("The mean bias in GHI is: " + GHI_MAE + " " + GHI@units)
    ;print("The mean bias in WPD is: " + WPD_MAE + " " + WPD@units)

    fields = (/"N/A","GHI_MAE", "WPD_MAE"/)   ; Define field names
    fields = dq + fields + dq           ; Pre/append quotes to field names
    header = [/str_join(fields,", ")/]  ; Header is field names separated by commas
    alist  = [/0, GHI_MAE, WPD_MAE/]       ; List of variables to write
    format = "%7.2f,%7.2f,%7.2f"              ; Format to use for each variable
    write_table(csv_filename, "a", header, "%s")   ; Write header to CSV file.
    write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.

end
