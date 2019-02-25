;-----------------------------------------------------------------
;  GHI plot for single timestep in wrfout
;
;  JAS 11.07.2018
;-----------------------------------------------------------------

begin
;Open MAP and ACONC files (do not append with .nc) 
   WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/solar_wfp/wrfprd_jan01-05/"
   WRFfile = "wrfout_d03_2010-12-31_12:00:00"
  
   if (fileexists(WRFdir+WRFfile)) then
	   fwrf = addfile(WRFdir+WRFfile, "r")
   else
	   print("")
	   print("The ACONC file "+WRFdir+WRFfile+" does not exist. Check your path.")
	   print("")
	   exit
   end if

;--------------------------------------------------
   ; Open file and read in data. The arrays
   ; are dimensioned (time x xcoord x ycoord)
   ; (time x lon x lon), so we must reorder
   ; to (time x ycoord x xcoord).
   ;--------------------------------------------------
;   f     = addfile ("pre.8912.mon.nc", "r")
;   p     = f->pre(time|:,ycoord|:,xcoord|:)
;   lat2d = f->lat(ycoord|:,xcoord|:)
;   lon2d = f->lon(ycoord|:,xcoord|:)

;---Just look at first time step.
   it = 1
   lay = 2
   ;print("Working on time: " + times(it) )

;---Variables from wrfout file
   LAT2D = fwrf->XLAT(it,:,:)
   ;LAT2D = LAT2D(it,:,:)
   ;LAT2D@units = "degrees_north"
   nlat = dimsizes(LAT2D(:,0))
   ;print(nlat)
   ;printVarSummary(LAT2D)
   LON2D = fwrf->XLONG(it,:,:)
   ;LON2D = LON2D(it,:,:)
   ;LON2D@units = "degrees_east"
   nlon = dimsizes(LAT2D(0,:))
   ;print(nlon)
   ;printVarSummary(LON2D)

   DNI  = fwrf->SWDDNI(it,:,:)      
   DHI  = fwrf->SWDDIF(it,:,:)    
   GHI = DNI+DHI
   GHI@long_name = "Global Horizontal Irradiance"
   printVarSummary(GHI)

;---Set the workstation (x11, png, eps, ps, pdf, ncgm)
   wks  = gsn_open_wks("x11","Solar Plot")            ;-- open a workstation
   cmap = read_colormap_file("MPL_YlOrRd")         ;-- so we can subset later

;---Set plot resources
   res                        = True               ; plot mods desired
   res@cnFillOn               = True               ; color fill  
   res@cnSpanFillPalette      = True
   res@cnLevelSelectionMode   = "ManualLevels"
   res@cnMinLevelValF         = 30.                 ; set min contour level
   res@cnMaxLevelValF         = 300.                ; set max contour level
   res@cnLevelSpacingF        = 30.
   ;res@cnMaxLevelCount        = 30                 ; maximum contour level count  
   ;res@cnLevelSelectionMode   = "EqualSpacedLevels"  ; color fill  
   res@cnFillPalette          = cmap(:,:)         ; subset the color map
   res@cnLinesOn              = False              ; no contour lines
   res@cnLineLabelsOn         = False              ; no contour labels
   res@cnInfoLabelOn          = False              ; no contour info label
   res@lbTitleString          = "Irradiance (W/m~S~2~N~)"
   res@lbTitleOffsetF         = -0.2
   res@lbTitleFontHeightF     = 0.02
   res@lbLabelFontHeightF     = 0.015
   res@gsnLeftString = ""                      ; do not draw the left sub-title (otherwise automatically set)
   res@gsnRightString = ""                      ; do not draw the right sub-title (otherwise automatically set
          
   res@mpDataBaseVersion      = "MediumRes"        ; better map outlines
   res@pmTickMarkDisplayMode  = "Always"           ; turn on tickmarks
   res@mpOutlineOn           = True                ; turn on map outline 
   res@mpOutlineBoundarySets = "USStates"          ; turn on state boundaries
         
   res@tiMainString           = "One Hour GHI"
   res@tiMainFontHeightF      = 0.025              ; smaller title
   res@tiMainOffsetYF         = -0.005             ; move title down
               
   res@gsnAddCyclic           = False              ; regional data
   res@gsnMaximize            = True               ; enlarge image  

   res@mpLimitMode            = "Corners"          ; choose region of map
   res@mpLeftCornerLatF       = LAT2D(0,0)
   res@mpLeftCornerLonF       = LON2D(0,0)
   res@mpRightCornerLatF      = LAT2D(nlat-1,nlon-1)
   res@mpRightCornerLonF      = LON2D(nlat-1,nlon-1)

; The following 4 pieces of information are REQUIRED to properly display
; data on a native lambert conformal grid.  This data should be specified
; somewhere in the model itself, but in this case, it was not.
     
   res@mpProjection           = "LambertConformal" ;-- define the map projection (corresponds to 'lambert' in geogrid)
   res@mpLambertParallel1F    = 45.       ;-- corresponds to truelat1 in geogrid
   res@mpLambertParallel2F    = 33.       ;-- corresponds to truelat2 in geogrid
   res@mpLambertMeridianF     = -97.         ;-- corresponds to stand_lon in geogrid

; Usually, when data is placed onto a map, it is TRANSFORMED to the specified
; projection. Since this model is already on a native lambert conformal grid,
; we want to turn OFF the transformation.
     
   res@tfDoNDCOverlay = "NDCViewport"

;---Creat the plot       
   plot = gsn_csm_contour_map(wks,GHI(:,:),res)     ; Draw contours over a map.

end
