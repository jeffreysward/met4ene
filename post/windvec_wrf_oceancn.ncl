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

;---Open netCDF file
  a = addfile("/magma-dirs/jas983/wrf_data/solar_wfp/wrfprd_jan01-05/wrfout_d03_2010-12-31_12:00:00","r")
  
;
; Read in Sea Surface Temperature Anomalies
; Read in U and V at 1000 mb [subscript 0]
; Determine the subscripts corresponding to Jan 88
;
  it       = 0
  ilay	   = 2

  u        = wrf_user_getvar(a, "ua", it) ;This will be a three dim array [LAY, XLAT, XLONG]
  ;printVarSummary(u)

  v        = wrf_user_getvar(a, "va", it) ;This will be a three dim array [LAY, XLAT, XLONG]
  ;printVarSummary(v)

  LAT2D = a->XLAT(it,:,:)  
  nlat = dimsizes(LAT2D(:,0))
  LAT2D@units = "degrees_north"
  ;printVarSummary(LAT2D)

  LON2D = a->XLONG(it,:,:)
  nlon = dimsizes(LAT2D(0,:))
  LON2D@units = "degrees_east"
  ;printVarSummary(LON2D)

  speed    = sqrt(u(ilay,:,:)^2+v(ilay,:,:)^2)  ;This will be a two dim array [XLAT, XLONG]
  speed@long_name = "Wind Speed"
  speed!0  = "south_north"
  speed!1  = "west_east"
  speed&south_north = LAT2D(:,0)
  speed&west_east = LON2D(0,:)
  ;printVarSummary(speed)


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

;  res@tfDoNDCOverlay           = True             
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
  res@tiMainString         = "Winds near Turbine Hub Height"
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

  ;res@gsnDraw          = False                    ; turn off draw and frame
  ;res@gsnFrame         = False                    ; b/c this is an overlay plot
  plot=gsn_csm_vector_scalar_map(wks,u(ilay,:,:),v(ilay,:,:),speed(:,:),res)


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
  ;draw(plot)
  ;frame(wks)
end
