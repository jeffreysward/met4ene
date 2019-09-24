;----------------------------------------------------------------------
; wrf2era.ncl
;
; This is an NCL/ESMF regridding from a WRF 
; (curvilinear) grid to the ERA5 grid. It uses
; ESMF_regrid to do the regridding.
;
; This function takes the year, month, and day - so it can locate the
; wrfout file and the corresponding ERA5 data - as inputs and computes
; a single mean absolute error (MAE) across the entire domain for 
; several different meteorological variables, which are then returned 
; by this function (t2_MAE, u10_MAE, v10_MAE, u100_MAE, v100_MAE). 
;
;----------------------------------------------------------------------
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/esmf/ESMF_regridding.ncl"
loadscript("./cd_inv_string.ncl")
loadscript("./cd_string.ncl")

;undef("wrf2era")
;function wrf2era(in_yr, in_mo, in_da, WRFdir)
begin
;---WRF file containing source grid
;    WRFdir = "/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/2011-01-16_10mp1lw1sw2lsm2pbl2cu/"
;    WRFdir   = "/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/" + sprinti("%0.4i", in_yr) + "-" + sprinti("%0.2i", in_mo) + "-" + sprinti("%0.2i", in_da) + "_10mp1lw1sw2lsm2pbl2cu/"
    WRFfile  = "wrfout_d02.nc"
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
    ERAdir   = "/share/mzhang/jas983/wrf_data/data/ERA5/" 
    ;---2m temperature
    ERAfile  = "EastUS_e5.oper.an.sfc.128_167_2t.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile1 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if 
    ;---10m U wind component
    ERAfile  = "EastUS_e5.oper.an.sfc.128_165_10u.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile2 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if
    ;---10m V wind component
    ERAfile  = "EastUS_e5.oper.an.sfc.128_166_10v.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile3 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if
    ;---100m U wind component
    ERAfile  = "EastUS_e5.oper.an.sfc.228_246_100u.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile4 = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if
    ;---100m V wind component
    ERAfile  = "EastUS_e5.oper.an.sfc.228_247_100v.regn320sc." + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) + "0100_" + sprinti("%0.4i", in_yr) + sprinti("%0.2i", in_mo) +  "3123.nc"
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
    do iwrf = 0,ntimes-1,24                       ; TIME LOOP
        iera = str_match_ind(date_str, wrf_time(iwrf))
        time_numeric = cd_inv_string( wrf_time(iwrf), "%Y-%N-%D_%H:%M:%S")  ;; will return in hours since 1800-01-01 unless specified otherwise
    	offset = 5                                  ; hours
    	time_numeric = time_numeric - offset
    	time_str = cd_string( time_numeric, "%c %D, %Y %H:%M")

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

        ;----------------------------------------------------------------------
        ; Plotting section
        ;
        ; This section creates filled contour plots of both the original
        ; data and the regridded data, and panels them.
        ;----------------------------------------------------------------------
        t2@lat2d = wrf_lat     ; Needed for plotting. "t2_regrid" 
        t2@lon2d = wrf_lon     ; already has these attrs attached.

        wks = gsn_open_wks("x11","WRF_to_curv")

        res                       = True
        res@gsnMaximize           = True
        res@gsnDraw               = False
        res@gsnFrame              = False
	
	;-- Set the center string to time
	res@gsnCenterString        = time_str           ;-- write time to center string
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
        d_res 		              = res
        d_res@lbLabelBarOn        = True

        ;--Set contour spacing interval 		Change (maybe)
        mnmxint = nice_mnmxintvl( min(t2(iwrf,:,:)), max(t2(iwrf,:,:)), 18, False)
        res@cnLevelSelectionMode  = "ManualLevels"
        res@cnMinLevelValF        = mnmxint(0)
        res@cnMaxLevelValF        = mnmxint(1)
        res@cnLevelSpacingF       = mnmxint(2)

        mnmxint = nice_mnmxintvl( min(t2_diff), max(t2_diff), 18, False)
	d_res@cnLevelSelectionMode  = "ManualLevels"
        ;d_res@cnMinLevelValF      = -mnmxint(1)
        ;d_res@cnMaxLevelValF      = mnmxint(1)
        ;d_res@cnLevelSpacingF     = mnmxint(2)
        d_res@cnMinLevelValF      = -15
        d_res@cnMaxLevelValF      = 15
        d_res@cnLevelSpacingF     = 2

        ;---Resources for plotting regridded data
        res@gsnAddCyclic  = False            ;;---Change (maybe)
        res@tiMainString  = "Curvilinear grid (" + Opt@InterpMethod + ")"

        plot_regrid = gsn_csm_contour_map(wks,t2_regrid(iwrf,:,:),res)

        ;---Resources for plotting original data
        res@gsnAddCyclic = False            ;;---Change (maybe)
        res@tiMainString = "Original WRF grid"

        plot_orig = gsn_csm_contour_map(wks,t2(iwrf,:,:),res)  

        ;---Resources for plotting difference in WRF and ERA5 data
        d_res@gsnAddCyclic           = False            ;;---Change (maybe)
        d_res@tiMainString 	     = "WRF & ERA5 Difference"
        d_res@lbTitleString          = "Temperature Difference (C)"
	d_res@lbTitleOffsetF         = -0.35	;-- move the color bar label down
        d_res@lbTitleFontHeightF     = 0.02
        d_res@lbLabelFontHeightF     = 0.012
        cmap = read_colormap_file("BlueDarkRed18")      ;-- so we can subset later
        d_res@cnFillPalette          = cmap(:,:)        ;-- subset the color map

        plot_diff = gsn_csm_contour_map(wks,t2_diff,d_res)  

        ;---Compare the plots in a panel
        pres                   = True
        pres@gsnMaximize       = True
        pres@gsnPanelLabelBar  = True

        ;gsn_panel(wks,(/plot_orig,plot_regrid/),(/2,1/),pres)

        ;---Plot the difference 
        draw(plot_diff)
        frame(wks)
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

;    return( [/ t2_MAE, u10_MAE, v10_MAE, u100_MAE, v100_MAE /] ) 
end
