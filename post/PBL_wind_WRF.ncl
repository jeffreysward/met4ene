; Example script to produce plots for a WRF real-data run,
; with the ARW coordinate dynamics option.
; Plot data on a cross section
; This script will plot data at a set angle through a specified point
; This script adds lon/lat info along X-axis

loadscript("./cd_inv_string.ncl")
loadscript("./cd_string.ncl")
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
	; Set the experiment date and params
	expr = "NYpvow_A9Dx5D"
	dates = "2011jan23-24"
	params = "z36r1bl5cu300ls2"
	; The WRF ARW input file.
	WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/"+expr+"/"+dates+"/wrfrun_"+params+"/"
	WRFfile = "wrfout_d03_2011-01-24_01:00:00"

	if (fileexists(WRFdir+WRFfile)) then
        a = addfile(WRFdir+WRFfile, "r")
	else
        print("")
        print("The WRF file "+WRFdir+WRFfile+" does not exist. Check your path.")
        print("")
     	exit
	end if

	; We generate plots, but what kind do we prefer?
	;type = "x11"
	type = "png"
	;type = "pdf"
	;type = "ps"
	;type = "ncgm"

	; Set some basic resources
	res = True
	res@MainTitle = "Wind within the PBL"
	res@NoHeaderFooter = True
	pltres = True

	;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
	;
	; Pull the necessary variables off the file.
	;

	FirstTime = True
	FirstTimeMap = True
	times = wrf_user_getvar(a,"times",-1)   ; get times in the file
	ntimes = dimsizes(times)                ; number of times in the file
	mdims = getfilevardimsizes(a,"P")       ; get some dimension sizes for the file
	nd = dimsizes(mdims)

	XLAT = wrf_user_getvar(a, "XLAT",0)
	xlat = XLAT(south_north|:,west_east|0)
	;printVarSummary(xlat)
	XLONG = wrf_user_getvar(a, "XLONG",0)
	xlon = XLONG(south_north|0,west_east|:)
	;printVarSummary(xlon)
	z = wrf_user_getvar(a, "z",0)          ; grid point height
	z&south_north  = xlat
	z&west_east    = xlon
	;printVarSummary(z)
	ter = wrf_user_getvar(a, "HGT",0)
  

	;---------------------------------------------------------------
	n = 1
	do it = 0,ntimes-1,1                    ; TIME LOOP
	print("Working on time: " + times(it) )
	res@TimeLabel = times(it)               ; Set Valid time to use on plots
	outdir = "./met_plots/"+expr+"/"+dates+"/wrfrun_"+params
	outfile = "/PBL_Wind_ts."+sprinti("%0.3i", it+1)
	ret = systemfunc("test -d "+outdir+"; echo $?")
    	if(ret .eq. 0) then
        	;-- the directory already exists
    	else 
        	system("mkdir -p "+outdir)      ;-- create the directory    
    	end if
	wks = gsn_open_wks(type,outdir+outfile)

	u  = wrf_user_getvar(a,"ua",it)          ; U wind component
	;printVarSummary(u)
	v  = wrf_user_getvar(a,"va",it)          ; V wind component
	;printVarSummary(v)
	wind = sqrt(u^2+v^2)                    ; horizontal wind

	;
	; Name the dimensions of "wind" and assign a coordinate
	; variable and some attributes.
	;
	wind!0                 = "bottom_top"
	;wind&bottom_top        = z
	wind!1                 = "south_north"
	wind&south_north       = xlat
	wind!2                 = "west_east"
	wind&west_east         = xlon
	wind@long_name = "horizontal wind"
	wind@units     = "m s-1"
	;printVarSummary(wind)

	; Format the time to EST
	time_numeric = cd_inv_string( times(it), "%Y-%N-%D_%H:%M:%S")  ;; will return in hours since 1800-01-01 unless specified otherwise
	offset = 5                                  ; hours
	time_numeric = time_numeric - offset
	time_str = cd_string( time_numeric, "%c %D, %Y %H:%M")

	if ( FirstTime ) then                   ; get height info for labels
		zmin = 0.
		zmax = 1.                               ; We are only interested in the first 1km
		;nz = floattoint(zmax + 5)
		nz = 5 
	end if
	;---------------------------------------------------------------
	;do ip = 1, 3 ; we are doing 3 plots
	ip = 1
	; all with the pivot point (plane) in the center of the domain
	; at angles 0, 45 and 90
	;
	; |
	; angle=0 is |
	; |
	;
	plane = new(2,float)
	plane = (/ mdims(nd-1)/2, mdims(nd-2)/2 /) ; pivot point is center of domain (x,y)
	;print(plane)
	opts = False
	if(ip .eq. 1) then
		angle = 90.
		X_plane = wrf_user_intrp2d(XLONG,plane,angle,opts)
		X_desc = "longitude"
	end if
	if(ip .eq. 2) then
		angle = 0.
		X_plane = wrf_user_intrp2d(XLAT,plane,angle,opts)
		X_desc = "latitude"
	end if
	if(ip .eq. 3) then
		angle = 45.
		X_plane = wrf_user_intrp2d(XLONG,plane,angle,opts)
		X_desc = "longitude"
	end if


	; Find the index where zmax km is located - only need to do this once
	if ( FirstTime ) then
		b = ind(z(:,0,0) .gt. zmax*1000. )
		zmax_pos = b(0) - 1
		levs4lb = z(0:zmax_pos,0,0)
		lon4lb = z(0,0,:)
		if ( abs(z(zmax_pos,0,0)-zmax*1000.) .lt. abs(z(zmax_pos+1,0,0)-zmax*1000.) ) then
			zspan = b(0) - 1
		else
			zspan = b(0)
		end if
		delete(b)
		FirstTime = False
	end if

	; X-axis lables
	dimsX = dimsizes(X_plane)
	xmin = X_plane(0)
	xmax = X_plane(dimsX(0)-1)
	xspan = dimsX(0)-1
	nx = floattoint( (xmax-xmin)/2 + 1)


	;---------------------------------------------------------------
	; Options for XY Plots
	opts_xy = res
	;opts_xy@tiXAxisString = X_desc
	opts_xy@tiYAxisString = ""
	opts_xy@cnMissingValPerimOn = True
	opts_xy@cnMissingValFillColor = 0
	opts_xy@cnMissingValFillPattern = 11
	;opts_xy@tiXAxisFontHeightF 	 	 = 0.04
	;opts_xy@tiYAxisFontHeightF 		 = 0.04
	opts_xy@tmXBMajorLengthF 		 = 0.02
	opts_xy@tmYLMajorLengthF 		 = 0.02
	opts_xy@tmYLLabelFontHeightF 	 = 0.015

	; Plotting options for wind
	cmap = read_colormap_file("MPL_YlGnBu")               ;-- so we can subset later
	opts_wind 						 = opts_xy
	opts_wind@sfXArray               = xlon
	opts_wind@sfYArray               = levs4lb
	opts_wind@cnFillOn               = True 
	opts_wind@cnSpanFillPalette      = True
	opts_wind@cnLevelSelectionMode   = "ManualLevels"
	opts_wind@cnMinLevelValF         = 1.               ;-- set min contour level
	opts_wind@cnMaxLevelValF         = 10.              ;-- set max contour level
	opts_wind@cnLevelSpacingF        = 1		    ;-- set contour level spacing
	;opts_wind@cnMaxLevelCount        = 30                      ;-- maximum contour level count  
	;opts_wind@cnLevelSelectionMode   = "EqualSpacedLevels"     ;-- color fill  
	opts_wind@cnFillPalette          = cmap(:,:)          ;-- subset the color map
	opts_wind@tiXAxisString 		 = "Longitude"
	opts_wind@tiYAxisString 		 = "Height (m)"
	opts_wind@tiXAxisFontHeightF 	 = 0.02
	opts_wind@tiYAxisFontHeightF 	 = 0.02
	opts_wind@pmLabelBarOrthogonalPosF = 0.0
	;opts_wind@lbOrientation 		 = "vertical"
	;opts_wind@pmLabelBarSide 		 = "right"
	opts_wind@lbTitleString          = "Wind Speed (m/s)"
	opts_wind@lbTitleOffsetF         = -0.3
	opts_wind@lbTitleFontHeightF     = 0.03
	opts_wind@lbLabelFontHeightF     = 0.02
	opts_wind@FieldTitle             = ""       		;-- write time to center string
	opts_wind@UnitLabel				 = time_str       

	; Get the contour info for the wind and temp
	;contour_wind = wrf_contour(a,wks,wind_plane(0:zmax_pos,:),opts_wind)
	contour_wind = wrf_contour(a,wks,wind(bottom_top|0:zmax_pos,south_north|72,west_east|:),opts_wind)
	;contour_wind = wrf_contour(a,wks,wind_plane,opts_wind)

	;---------------------------------------------------------------
	; MAKE PLOTS
	if (FirstTimeMap) then
		outfile1 = "/PBL_Wind_location"
		wks1 = gsn_open_wks(type,outdir+outfile1)

		lat_plane = wrf_user_intrp2d(XLAT,plane,angle,opts)
		lon_plane = wrf_user_intrp2d(XLONG,plane,angle,opts)
		mpres 						 = True
		pltres 						 = True
		pltres@FramePlot 			 = False

		optsM 						 = res
		optsM@cnFillOn 				 = True
		optsM@lbTitleOn 			 = False
		optsM@lbLabelBarOn 			 = False
		optsM@FieldTitle             = ""       		;-- turn off field title
		optsM@UnitLabel				 = ""      
		;optsM@lbLabelOffsetF 	     = -0.4
		optsM@lbTitleString          = ""
		optsM@lbTitleOffsetF         = -0.6
		;optsM@lbTitleFontHeightF     = 0.02
		;optsM@lbLabelFontHeightF     = 0.015
		contour = wrf_contour(a,wks1,ter,optsM)
		plot = wrf_map_overlays(a,wks1,(/contour/),pltres,mpres)

		lnres = True
		lnres@gsLineThicknessF = 3.0
		lnres@gsLineColor = "Red"
		do ii = 0,dimsX(0)-2
			gsn_polyline(wks1,plot,(/lon_plane(ii),lon_plane(ii+1)/),(/lat_plane(ii),lat_plane(ii+1)/),lnres)
		end do
		frame(wks1)
		delete(lon_plane)
		delete(lat_plane)
		pltres@FramePlot = True
	end if
	plot = wrf_overlays(a,wks,(/contour_wind/),pltres) ; plot x-section

	; Delete options and fields, so we don't have carry over
	delete(opts_xy)
	delete(opts_wind)
	delete(X_plane)

	;end do ; make next cross section

	;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
	FirstTimeMap = False
	n := n + 1
	end do ; END OF TIME LOOP

end
