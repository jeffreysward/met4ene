;----------------------------------------------------------------------
; offshore_wind_plot.ncl
;
; Concepts illustrated:
;   - Overlaying line contours, vectors, and filled contours on a map
;   - Manually attaching lat/lon coordinate arrays to a variable
;   - Changing the length of the smallest vector as a fraction of the reference vector
;   - Drawing curly vectors
;   - Setting the color for vectors
;   - Moving the vector reference annotation to the top right of the plot
;   - Making the labelbar be vertical
;   - Increasing the thickness of vectors
;----------------------------------------------------------------------
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"  

begin
; Load the WRF input file.  
WRFdir = "/magma-dirs/jas983/wrf_data/met4ene/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/wrfrun_z46r1bl5cu300ls2/"
WRFfile = "wrfout_d02_2011-01-24_01:00:00"

if (fileexists(WRFdir+WRFfile)) then
	a = addfile(WRFdir+WRFfile, "r")
else
	print("")
	print("The wrfout file "+WRFdir+WRFfile+" does not exist. Check your path.")
	print("")
	exit
end if
  
  u  = wrf_user_getvar(a,"ua",-1)        ; u averaged to mass points
  v  = wrf_user_getvar(a,"va",-1)        ; v averaged to mass points
  z  = wrf_user_getvar(a, "z",-1)        ; grid point height
  u_plane  = wrf_user_intrp3d( u,z,"h",100.,0.,False)
  printVarSummary(u_plane)
  v_plane  = wrf_user_intrp3d( v,z,"h",100.,0.,False)
  printVarSummary(v_plane)
  wspd = sqrt(u_plane^2 + v_plane^2)
  wspd@long_name  = "Wind Speed at 100m"
  wspd@short_name = "100wind"
  wspd@units      = "m/s"
  wspd@_FillValue = -999           	 ; sets _FillValue to -999
  printVarSummary(wspd)
  

  it       = 0

  LAT2D = a->XLAT(it,:,:)  
  nlat = dimsizes(LAT2D(:,0))
  LAT2D@units = "degrees_north"
  ;printVarSummary(LAT2D)

  LON2D = a->XLONG(it,:,:)
  nlon = dimsizes(LAT2D(0,:))
  LON2D@units = "degrees_east"
  ;printVarSummary(LON2D)


;---Create plot
  wks = gsn_open_wks("x11","vector")                ; send graphics to PNG file
  cmap = read_colormap_file("wind_17lev")

  res                        = True                 ; plot mods desired
  res@gsnMaximize            = True                 ; Maximize plot in frame
  res@gsnAddCyclic           = False
  res@cnFillOn               = True                 ; turn on color for contours
  res@cnLinesOn              = False                ; turn off contour lines
  res@cnLineLabelsOn         = False                ; turn off contour line labels
  res@cnFillPalette          = cmap                 ; subset the color map if you like 
  res@gsnScalarContour       = True                 ; contours desired

  res@mpLandFillColor        = "gray"               ; set land to be gray
  res@mpDataBaseVersion      = "HighRes"            ; better map outlines
  res@pmTickMarkDisplayMode  = "Always"             ; turn on tickmarks
  res@mpOutlineOn            = True                 ; turn on map outline 
  res@mpOutlineBoundarySets  = "USStates"           ; turn on state boundaries


  res@mpLimitMode            = "Corners"
  res@mpLeftCornerLatF       = LAT2D(0,0)
  res@mpLeftCornerLonF       = LON2D(0,0)
  res@mpRightCornerLatF      = LAT2D(nlat-1,nlon-1)
  res@mpRightCornerLonF      = LON2D(nlat-1,nlon-1)

  res@mpProjection           = "LambertConformal";-- define the map projection (corresponds to 'lambert' in geogrid)
  res@mpLambertParallel1F    = 45.               ;-- corresponds to truelat1 in geogrid
  res@mpLambertParallel2F    = 33.               ;-- corresponds to truelat2 in geogrid
  res@mpLambertMeridianF     = -97.              ;-- corresponds to stand_lon in geogrid

  ;res@lbOrientation            = "Vertical"     ; vertical label bar
  ;res@pmLabelBarOrthogonalPosF = -0.01          ; move label bar closer

; Usually, when data is placed onto a map, it is TRANSFORMED to the
; specified projection. Since this model is already on a native lambert
; conformal grid, we want to turn OFF the transformation. THIS IS VERY
; IMPORTANT!!!
;

  res@tfDoNDCOverlay           = "NDCViewport"    ; NCL V6.5.0 or later

; note, when doing a subregion, NCL determines the range of the data from
; the full domain. If you wish to just consider the domain you are plotting,
; you must manually set those levels.

  res@cnLevelSelectionMode = "ManualLevels"       ; set manual contour levels
  res@cnMinLevelValF       = 1.0                 ; set min contour level
  res@cnMaxLevelValF       = 10.0                   ; set max contour level
  res@cnLevelSpacingF      = 1.0                 ; set contour spacing
  res@lbTitleString          = "Wind Speed (m/s)"
  res@lbTitleOffsetF         = -0.2
  res@lbTitleFontHeightF     = 0.02
  res@lbLabelFontHeightF     = 0.015
  res@tiMainString         = "100m Winds"
  res@gsnLeftString        = ""                   ; do not draw the left sub-title (otherwise automatically set)
  res@gsnRightString       = ""                   ; do not draw the right sub-title (otherwise automatically set
  
  res@vcRefMagnitudeF           = 5.0             ; define vector ref mag
  res@vcRefLengthF              = 0.035           ; define length of vec ref
  res@vcMinDistanceF            = 0.03
  res@vcMinFracLengthF          = 0.6
  res@vcRefAnnoOrthogonalPosF   = -1.0            ; move ref vector
  res@vcRefAnnoArrowLineColor   = "black"         ; change ref vector color
  res@vcRefAnnoArrowUseVecColor = False

  res@vcGlyphStyle            = "FillArrow"       ; turn on filled arrows
  res@vcFillArrowEdgeColor    = "black"           ; change vector edge color
  res@vcLineArrowColor        = "black"           ; change vector color
  res@vcLineArrowThicknessF   = 1.0               ; change vector thickness
  res@vcVectorDrawOrder       = "PostDraw"        ; draw vectors last

  res@gsnDraw          = False                    ; turn off draw and frame
  res@gsnFrame         = False                    ; b/c this is an overlay plot
  plot=gsn_csm_vector_scalar_map(wks,u_plane(it,:,:),v_plane(it,:,:),wspd(it,:,:),res)


;---Add contours of wind speed to plot
  ;delete(res)
  ;res                 = True
  ;res@gsnDraw         = False
  ;res@gsnFrame        = False
  ;res@gsnLeftString   = ""
  ;res@gsnRightString  = ""
  ;res@gsnCenterString = ""
  ;res@cnInfoLabelOrthogonalPosF = 0.15  ; move info label down

  ;cplot = gsn_csm_contour(wks,speed,res)
  ;overlay(plot,cplot)
  draw(plot)
  frame(wks)
end
