;----------------------------------------------------------------------
; wrf2era.ncl
;
; This is an NCL/ESMF regridding from a WRF 
; (curvilinear) grid to the ERA5 grid. It uses
; ESMF_regrid to do the regridding.
;
; This script takes the year, month, and day - so it can locate the
; wrfout file and the corresponding ERA5 data - as inputs and computes
; a single mean absolute error (MAE) across the entire domain for 
; several different meteorological variables, which are then returned 
; by this function (t2_MAE, u10_MAE, v10_MAE, u100_MAE, v100_MAE). 
;
;----------------------------------------------------------------------
;load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/esmf/ESMF_regridding.ncl"

begin
;---WRF file containing source grid
    WRFdir = "/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2011-01-16_10mp1lw1sw2lsm2pbl2cu/"
    WRFfile  = "wrfout_d03.nc"
    if (fileexists(WRFdir+WRFfile)) then
        sfile = addfile(WRFdir+WRFfile, "r")
    else
        print("")
        print("The wrfout file "+WRFdir+WRFfile+" does not exist. Check your path.")
        print("")
        exit
    end if

;---Get variable(s) to regrid
    wrf_lat = sfile->XLAT(0,:,:)              
    wrf_lon = sfile->XLONG(0,:,:)
    wrf_time = wrf_user_getvar(sfile,"times",-1)   
    t2      = wrf_user_getvar(sfile,"td2",-1) 
    ;DNI     = wrf_user_getvar(sfile,"SWDDNI",0)
    ;DHI     = wrf_user_getvar(sfile,"SWDDIF",0)
    u     = wrf_user_getvar(sfile,"ua",-1)
    v     = wrf_user_getvar(sfile,"va",-1)
    z     = wrf_user_getvar(sfile,"z",-1)

;---Interpolate winds to 10 and 100m
    u10   = wrf_user_interp_level(u,z,10,False)
    v10   = wrf_user_interp_level(v,z,10,False)
    u100  = wrf_user_interp_level(u,z,100,False)
    v100  = wrf_user_interp_level(v,z,100,False)

;---ERA data file(s)
    if (getenv("HOSTNAME") .eq. "en-cluster03.coecis.cornell.edu") then
        ERAdir   = "/share/mzhang/jas983/wrf_data/data/ERA/" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "/"
    else if (getenv("HOSTNAME") .eq. "vis01.mae.cornell.edu") then
        ERAdir   = "/magma-dirs/mzhang/jas983/wrf_data/data/ERA/" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "/"
    else
        ERAdir   = "/gpfs/fs1/collections/rda/data/ds630.0/e5.oper.an.sfc/" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "/"
    end if

    ;---2m temperature
    ERAfile  = "e5.oper.an.sfc.128_167_2t.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile1 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if 
    ;---10m U wind component
    ERAfile  = "e5.oper.an.sfc.128_165_10u.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile2 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if
    ;---10m V wind component
    ERAfile  = "e5.oper.an.sfc.128_166_10v.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile3 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if
    ;---100m U wind component
    ERAfile  = "e5.oper.an.sfc.228_246_100u.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile4 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if
    ;---100m V wind component
    ERAfile  = "e5.oper.an.sfc.228_247_100v.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile5 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if

    ;---Shortwave radiation
;    ERAfile  = "" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
;    if (fileexists(ERAdir+ERAfile)) then
;        dfile6 = addfile(ERAdir+ERAfile, "r")
;    else
;        print("")
;        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
;        print("")
;        exit
;    end if

    ;---Longwave radiation
;    ERAfile  = "" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
;    if (fileexists(ERAdir+ERAfile)) then
;        dfile7 = addfile(ERAdir+ERAfile, "r")
;    else
;        print("")
;        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
;        print("")
;        exit
;    end if

    ERA_lat  = dfile1->latitude                  
    ERA_lon  = dfile1->longitude
    ERA_time = dfile1->time
    ;---Array to hold month abbreviations. Don't store anything in index
    ; '0' (i.e. let index 1=Jan, 2=Feb, ..., index 12=Dec).
    month_abbr = (/"","01","02","03","04","05","06","07","08","09", \
                    "10","11","12"/)
    ;---Convert to UTC time.
    utc_time_ERA = cd_calendar(ERA_time, 0)
    ;---Store return information into more meaningful variables.
    year   = tointeger(utc_time_ERA(:,0))    ; Convert to integer for
    month  = tointeger(utc_time_ERA(:,1))    ; use sprinti 
    day    = tointeger(utc_time_ERA(:,2))
    hour   = tointeger(utc_time_ERA(:,3))
    ;---Write out strings in the format "yyyy-mm-dd_hh:mm:ss"
    date_str = sprinti("%0.4i", year) + "-" + month_abbr(month) + "-" + sprinti("%0.2i", day) + \
                "_" + sprinti("%0.2i", hour) + ":00:00"
    ERA_2tK  = dfile1->VAR_2T(:,:,:)
    ERA_2tC           = ERA_2tK - 273.15      ;-- convert temp from Kelvin to Celsius
    ERA_2tC@units     = "C"            		  ;-- define new units      
    ERA_u10  = dfile2->VAR_10U(:,:,:)
    ERA_v10  = dfile3->VAR_10V(:,:,:)
    ERA_u100 = dfile4->VAR_100U(:,:,:)
    ERA_v100 = dfile5->VAR_100V(:,:,:)   

;---Set up regridding options
    Opt                   = True

    ;---"bilinear" is the default. "patch" and "conserve" are other options.
    Opt@InterpMethod      = "bilinear"        ;;---Change (maybe)

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
    t2_regrid = ESMF_regrid(t2,Opt)
    u10_regrid = ESMF_regrid(u10,Opt)
    v10_regrid = ESMF_regrid(v10,Opt)
    u100_regrid = ESMF_regrid(u100,Opt)
    v100_regrid = ESMF_regrid(v100,Opt)

    ;printVarSummary(t2_regrid)
    ;printVarSummary(u10_regrid)
    ;printVarSummary(v10_regrid)
    ;printVarSummary(u100_regrid)
    ;printVarSummary(v100_regrid)

;---Loop through all the times in the WRF file to compute mean bias
    ntimes = dimsizes(wrf_time)                 ; number of times in the file
    n = 1
    t2_MAE = 0
    u10_MAE = 0
    v10_MAE = 0
    u100_MAE = 0
    v100_MAE = 0
    do iwrf = 0,ntimes-1,72                       ; TIME LOOP
        iera = str_match_ind(date_str, wrf_time(iwrf))

        ;---Compute difference between ERA5 variable and WRF variable(s)
        t2_diff = abs(t2_regrid(iwrf,:,:) - ERA_2tC(iera,:,:)) 
        t2_diff!0 = "lat"
        t2_diff!1 = "lon"
        t2_diff&lat = ERA_lat     
        t2_diff&lon = ERA_lon     
        ;printVarSummary(t2_diff)

        u10_diff = abs(u10_regrid(iwrf,:,:) - ERA_u10(iera,:,:))
        u10_diff!0 = "lat"
        u10_diff!1 = "lon"
        u10_diff&lat = ERA_lat
        u10_diff&lon = ERA_lon
        ;printVarSummary(u10_diff)

        v10_diff = abs(v10_regrid(iwrf,:,:) - ERA_v10(iera,:,:))
        v10_diff!0 = "lat"
        v10_diff!1 = "lon"
        v10_diff&lat = ERA_lat
        v10_diff&lon = ERA_lon
        ;printVarSummary(v10_diff)

        u100_diff = abs(u100_regrid(iwrf,:,:) - ERA_u100(iera,:,:))
        u100_diff!0 = "lat"
        u100_diff!1 = "lon"
        u100_diff&lat = ERA_lat
        u100_diff&lon = ERA_lon
        ;printVarSummary(u100_diff)

        v100_diff = abs(v100_regrid(iwrf,:,:) - ERA_v100(iera,:,:))
        v100_diff!0 = "lat"
        v100_diff!1 = "lon"
        v100_diff&lat = ERA_lat
        v100_diff&lon = ERA_lon
        ;printVarSummary(v100_diff)

        ;---Sum all computed biases across the domain
        ;***May need to set the missing values for all the *_diff variables.
        t2_MAE := t2_MAE + sum(t2_diff)
        u10_MAE := u10_MAE + sum(u10_diff)
        v10_MAE := v10_MAE + sum(v10_diff)
        u100_MAE := u100_MAE + sum(u100_diff)
        v100_MAE := v100_MAE + sum(v100_diff)

        n := n + 1
    end do        ; END OF TIME LOOP

;---Compute the mean bias and save/print    
    n := n - 1
    t2_MAE := t2_MAE/n
    u10_MAE := u10_MAE/n
    v10_MAE := v10_MAE/n
    u100_MAE := u100_MAE/n
    v100_MAE := v100_MAE/n
    
    dq = str_get_dq()                ; double quote character
    csv_filename = "mae_wrfyera.csv"

    fields = (/"t2_MAE", "u10_MAE", "v10_MAE", "u100_MAE", "v100_MAE"/)
    fields = dq + fields + dq                      ; Pre/append quotes to field names
    header = [/str_join(fields,", ")/]             ; Header is field names separated by commas.
    alist  = [/t2_MAE, u10_MAE, v10_MAE, u100_MAE, v100_MAE/]   ; List of variables to write.
    format = "%7.2f,%7.2f,%7.2f,%7.2f,%7.2f"       ; Format to use for each variable.

    if (fileexists(csv_filename)) then
        write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
    else
        write_table(csv_filename, "w", header, "%s")   ; Write header to CSV file.
        write_table(csv_filename, "a", alist, format)  ; Write mixed data to CSV file.
    end if

end
