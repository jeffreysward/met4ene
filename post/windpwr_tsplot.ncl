
;   This script outputs a graphic depicting wind farm power output 
;   for each time included in the wrfout file.

loadscript("./cd_inv_string.ncl")
loadscript("./cd_string.ncl")

begin
;
; The WRF WFP input file.  
  WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jul21-22/wrfrun_r1bl5cu300ls2/"
  WRFfile = "wrfout_NYpvow_A5Dx3D_d03_2011-07-22_01:00:00" 
  if (fileexists(WRFdir+WRFfile)) then
        a = addfile(WRFdir+WRFfile, "r")
  else
        print("")
        print("The wrfout file "+WRFdir+WRFfile+" does not exist. Check your path.")
        print("")
        exit
  end if

  ilay = 3
  LAT2D = a->XLAT(0,:,:)  
  nlat = dimsizes(LAT2D(:,0))
  LAT2D@units = "degrees_north"
  ;printVarSummary(LAT2D)

  LON2D = a->XLONG(0,:,:)
  nlon = dimsizes(LAT2D(0,:))
  LON2D@units = "degrees_east"
  ;printVarSummary(LON2D)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; What times and how many time steps are in the data set?
  times = wrf_user_getvar(a,"times",-1)  ; get all times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
  n = 1
  do it = 0,ntimes-1,1            ; TIME LOOP
  ;it = 0

    print("Working on time: " + times(it) )
    outfile = "./pwr_plots/NYpvow_A5Dx3D/2011jul21-22/wrfrun_r1bl5cu300ls2/WFP_Pwr_ts."+sprinti("%0.3i", n)

    time_numeric = cd_inv_string( times(it), "%Y-%N-%D_%H:%M:%S")  ;; will return in hours since 1800-01-01 unless specified otherwise
    offset = 5                                  ; hours
    time_numeric = time_numeric - offset
    time_str = cd_string( time_numeric, "%c %D, %Y %H:%M")

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
  ; First get the variables we will need        

  ; We generate plots, but what kind do we prefer?
  ;  type = "x11"
    type = "png"
  ;  type = "pdf"
  ;  type = "ps"
  ;  type = "ncgm"
    wks = gsn_open_wks(type,outfile)

  ; Set some basic resources
    res = True
    res@tiMainString            = "Wind Farm Power Output"
    res@tiMainOffsetYF          = 0.02
    res@gsnDraw                 = False
    res@gsnFrame                = False

  ; Set up map resources 
    mpres = res 
    mpres@mpDataBaseVersion      = "HighRes"          ; better map outlines
    mpres@pmTickMarkDisplayMode  = "Always"             ; turn on tickmarks
    mpres@mpOutlineOn            = True                 ; turn on map outline 
    ;mpres@mpOutlineBoundarySets  = "USStates"          ; turn on state boundaries
    ;mpres@mpNationalLineColor    = "black"
    mpres@mpOutlineDrawOrder     = "PostDraw"
    mpres@mpFillDrawOrder        = "Predraw"
    ;mpres@mpOceanFillColor       = "lightskyblue1"
    ;mpres@mpLandFillColor        = "gray"
  ; Zoom in on the domain.
    mpres@mpLimitMode            = "Corners"
    mpres@mpLeftCornerLatF       = LAT2D(0,0)
    mpres@mpLeftCornerLonF       = LON2D(0,0)
    mpres@mpRightCornerLatF      = LAT2D(nlat-1,nlon-1)
    mpres@mpRightCornerLonF      = LON2D(nlat-1,nlon-1)
  ; Define the map projection you want to use
    mpres@mpProjection           = "LambertConformal";-- corresponds to 'lambert' in geogrid
    mpres@mpLambertParallel1F    = 45.               ;-- corresponds to truelat1 in geogrid
    mpres@mpLambertParallel2F    = 33.               ;-- corresponds to truelat2 in geogrid
    mpres@mpLambertMeridianF     = -97.              ;-- corresponds to stand_lon in geogrid
  
    map = gsn_csm_map(wks, mpres)

    pwr = a->POWER(it,:,:)               ; Power in W
       pwr = pwr/1000000                 ; Power in MW 
       pwr@units = "MW"
       pwr@lat2d = LAT2D
       pwr@lon2d = LON2D   
    u  = wrf_user_getvar(a,"ua",it)      ; 3D U at mass points
       u@lat2d = LAT2D
       u@lon2d = LON2D
    v  = wrf_user_getvar(a,"va",it)      ; 3D V at mass points    
       v@lat2d = LAT2D
       v@lon2D = LON2D
    tc2 = wrf_user_getvar(a,"T2",it)     ; T2 in Kelvin
       tc2 = tc2-273.16                  ; T2 in C
    u10 = wrf_user_getvar(a,"U10",it)    ; u at 10 m, mass point
       u10@lat2d = LAT2D
       u10@lon2d = LON2D
    v10 = wrf_user_getvar(a,"V10",it)    ; v at 10 m, mass point
       v10@lat2d = LAT2D
       v10@lon2d = LON2D
    ;printVarSummary(pwr)
    ;printVarSummary(u)
    ;printVarSummary(u10)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    ; Plotting options for power contour plot
      cmap = read_colormap_file("WhiteGreen")               
      
      cnres                      = res                   
      cnres@cnFillOn             = True 
      cnres@cnFillMode           = "RasterFill"  ; individually assign colors to grid cells 
      cnres@cnFillPalette        = cmap          ; subset the color map if you like
      cnres@gsnLeftString        = ""            ; leave left string blank
      cnres@gsnRightString       = ""            ; leave right string blank
      cnres@gsnCenterString      = time_str      ; write time to center string
      cnres@gsnCenterStringOrthogonalPosF = 0.02 ; move center string upwards
      cnres@cnLinesOn            = False         ; turn off contour lines
      cnres@cnLineLabelsOn       = False         ; turn off contour line labels               
      cnres@lbTitleString        = "Power Output (MW)"
      cnres@lbTitleOffsetF	 = -0.2          ; move colorbar title down 
      cnres@lbTitleFontHeightF   = 0.02          ; set colorbar title font height
      cnres@lbLabelFontHeightF   = 0.015         ; set colorbar labels font height
    ; Define contour levels
      cnres@cnLevelSelectionMode = "ManualLevels"; use manual colorbar levels
      cnres@cnMinLevelValF       = 1
      cnres@cnMaxLevelValF       = 19
      cnres@cnLevelSpacingF      = 1
      cnres@cnFillDrawOrder      = "Predraw"     ; draw contours in "Predraw" phase
      contour_pwr = gsn_csm_contour(wks,pwr,cnres)
      delete(cnres)

    ; Plotting options for Wind Vectors                 
      vcres                      = res
      vcres@gsnLeftString        = ""
      vcres@gsnRightString       = ""      
      vcres@vcRefMagnitudeF      = 10.0          ; define vector ref mag
      vcres@vcRefLengthF         = 0.025         ; define length of vec ref
      vcres@vcMinDistanceF       = 0.03
      vcres@vcMinFracLengthF     = 0.6
      vcres@vcLineArrowThicknessF= 1.0           ; change vector thickness
      vcres@vcLevelSelectionMode     = "ManualLevels"
      vcres@vcMinLevelValF           = 2.0
      vcres@vcMaxLevelValF           = 20.
      vcres@vcLevelSpacingF          = 2.0
      vcres@vcVectorDrawOrder        = "Predraw"
      ;vector = gsn_csm_vector(wks,u10,v10,vcres)
      vector = gsn_csm_vector(wks,u(ilay,:,:),v(ilay,:,:),vcres)
      delete(vcres)
      delete(res)

    ; MAKE OVERLAY PLOTS
      overlay(map, contour_pwr)
      overlay(map, vector)
      draw(map)
      frame(wks)
      ;maximize_output(wks,True)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
      n := n + 1
  end do        ; END OF TIME LOOP

end
