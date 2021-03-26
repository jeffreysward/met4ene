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
; ncl in_yr=2011 in_mo=01 in_da=10 \
; 'WRFdir="/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2011-01-10_10mp1lw1sw2lsm2pbl2cu/"' \
; 'ERAdir = "/share/mzhang/jas983/wrf_data/data/ERA5/"' 'paramstr="10mp1lw1sw2lsm2pbl2cu"' wrf2era_error_wspd100m.ncl
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
    wrf_lat = sfile->lat
    wrf_lon = sfile->lon
    wrf_time_raw = sfile->Times
    ;---The Times variable from wrf in datetime64 python format; NCL requires integer
    wrf_time = toint(wrf_time_raw)
    ;---Assign the units and calendar attributes to the integer time variable
    wrf_time@units = wrf_time_raw@units
    wrf_time@calendar = wrf_time_raw@calendar
    ;---Read in the 100m wind speed
    wspd_100 = sfile->wspd_100
    ;printVarSummary(wspd_100)

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
    ;print("First WRF time: " + wrf_datestr(0))
    ;print("Last WRF time: " + wrf_datestr(dimsizes(wrf_datestr) - 1))

;---ERA data file(s)
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
    ERA_time = dfile->Time
    ;---Read in ERA_WPD,
    ERA_wspd_100  = dfile->wspd_100
    ;printVarSummary(ERA_wspd_100)

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
    ;print("First ERA time: " + ERA_datestr(0))
    ;print("Last ERA time: " + ERA_datestr(dimsizes(ERA_datestr) - 1))

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
    Opt@InterpMethod      = "conserve"           ;;---Change (maybe)

    Opt@WgtFileName       = "WRF_to_ERA5.nc"

    Opt@SrcGridLat        = wrf_lat           ; source grid
    Opt@SrcGridLon        = wrf_lon
    Opt@SrcRegional       = True              ;;--Change (maybe)
    Opt@SrcInputFileName  = sfile             ; optional, but good idea

    Opt@DstGridLat        = ERA_lat           ; destination grid
    Opt@DstGridLon        = ERA_lon
    Opt@DstGridType       = "rectilinear"
    Opt@DstRegional       = True              ;;--Change (maybe)
;    Opt@DstMask2D = where(.not.ismissing(ERA_lat).and.\
;                          .not.ismissing(ERA_lon),1,0) ; Necessary if lat/lon
;                                                       ; has missing values.
    ;---Use the following 3 options if you want to reuse EXISTING weight files.
    Opt@SkipSrcGrid = True
    Opt@SkipDstGrid = True
    Opt@SkipWgtGen = True
    ;---Use the following 5 options if you want to regenerate the weight file every time (HIGH MEMORY!!!)
    ;Opt@SrcForceOverwrite = True
    ;Opt@DstForceOverwrite = True
    ;Opt@RemoveSrcFile     = True
    ;Opt@RemoveDstFile     = True
    ;Opt@RemoveWgtFile     = True
    ;Opt@RemovePETLog      = True
    ;Opt@PrintTimings      = True
    ;Opt@Debug             = True

;---Do the regridding
    wspd_100_regrid = ESMF_regrid(wspd_100,Opt)
    ;printVarSummary(wspd_100_regrid)

;---Loop through all the times in the WRF file to compute total bias
    ntimes = dimsizes(wrf_time)                 ; number of times in the file
    n = 1
    do iwrf = 0,ntimes-1,1                      ; TIME LOOP <-------- MAKE SURE TO RESET THIS LINE TO: 0,ntimes-1,1
        ;print("The wrf time is: " + wrf_datestr(iwrf))
        iera = str_match_ind(ERA_datestr, wrf_datestr(iwrf))
        ;printVarSummary(iera)
        if (iwrf .eq. 0) then
            if (isatt(iera,"_FillValue")) then
                if (ismissing(iera)) then
                    iera := 0
                end if
            end if
        end if

        ;---Compute absoulute difference between ERA5 variable and WRF variable(s)
        ;print("The ERA5 index is: " + iera)
        ;print("The ERA5 time is: " + ERA_datestr(iera))

        wspd_100_diff = abs(wspd_100_regrid(iwrf,:,:) - ERA_wspd_100(iera,:,:))
        wspd_100_regrid!0 = "lat"
        wspd_100_regrid!1 = "lon"
        wspd_100_regrid&lat = ERA_lat
        wspd_100_regrid&lon = ERA_lon
        if (any(isnan_ieee(wspd_100_regrid))) then
            replace_ieeenan (wspd_100_regrid, default_fillvalue("float"), 0)
        end if
        wspd_100_regrid@_FillValue = default_fillvalue("float")
        ;printVarSummary(wspd_100_regrid)

        ;---Sum all computed biases across the domain and save/print
        wspd_100_MAE_hr = sum(wspd_100_regrid)
        ;print("The hourly bias in 100m wind speed is: " + wspd_100_MAE_hr + " " + wspd_100@units)

        fields = (/"Date/Time", "wspd_100_MAE_hr"/) ; Define field names
        fields = dq + fields + dq               ; Pre/append quotes to field names
        header = [/str_join(fields,", ")/]      ; Header is field names separated by commas
        alist  = [/wrf_datestr(iwrf), wspd_100_MAE_hr/]     ; List of variables to write
        format = "%s,%7.2f"                  ; Format to use for each variable
        if (fileexists(csv_filename)) then
            write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
        else
            write_table(csv_filename, "w", header, "%s")   ; Write header to CSV file.
            write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
        end if

        ;---Update the accumulated biases
        if (n .eq. 1) then
            wspd_100_MAE = wspd_100_MAE_hr
        else
            wspd_100_MAE := array_append_record(wspd_100_MAE, wspd_100_MAE_hr, 0)
        end if

        n := n + 1
    end do        ; END OF TIME LOOP

;---Compute the total bias and save/print
    wspd_100_MAE := sum(wspd_100_MAE)
    ;print("The mean bias in 100m wind speed is: " + wspd_100_MAE + " " + wspd_100@units)

    fields = (/"N/A","wspd_100_MAE"/)              ; Define field names
    fields = dq + fields + dq                      ; Pre/append quotes to field names
    header = [/str_join(fields,", ")/]             ; Header is field names separated by commas
    alist  = [/0, wspd_100_MAE/]                   ; List of variables to write
    format = "%7.2f,%7.2f"                         ; Format to use for each variable
    write_table(csv_filename, "a", header, "%s")   ; Write header to CSV file.
    write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.

end
