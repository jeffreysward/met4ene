;-----------------------------------------------------------------
;  GHI plot for single timestep in wrfout
;
;  JAS 4.20.2019
;-----------------------------------------------------------------

loadscript("cd_inv_string.ncl")
begin
;--Open WRF files (do not append with .nc) 
   WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/wrfrun_z46r1bl5cu300ls2/"
   WRFfile = "wrfout_d03_2011-01-24_01:00:00"
  
   if (fileexists(WRFdir+WRFfile)) then
	   fwrf = addfile(WRFdir+WRFfile, "r")
   else
	   print("")
	   print("The ACONC file "+WRFdir+WRFfile+" does not exist. Check your path.")
	   print("")
	   exit
   end if

;---Just look at first time step.
   it = 19
   lay = 0
   times = wrf_user_getvar(fwrf,"times",-1) 
   print("Working on time: " + times(it) )

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

   time_numeric = cd_inv_string( times(it), "%Y%N%D%H%M")  ;; will return in hours since 1800-01-01 unless specified otherwise
   offset = -8    ; hours
   time_numeric = time_numeric - offset

;---Set the workstation (x11, png, eps, ps, pdf, ncgm)
   wks  = gsn_open_wks("x11","Solar Plot")            ;-- open a workstation
   cmap = read_colormap_file("MPL_YlOrRd")            ;-- so we can subset later

;---Set plot resources
   cnres                         = True               ; plot mods desired
   mpres                         = True
   pltres                        = True
   cnres@cnFillOn                = True               ; color fill  
   cnres@cnSpanFillPalette       = True
   cnres@cnLevelSelectionMode    = "ManualLevels"
   cnres@cnMinLevelValF          = 100.               ; set min contour level
   cnres@cnMaxLevelValF          = 1000.              ; set max contour level
   cnres@cnLevelSpacingF         = 100.
   ;cnres@cnMaxLevelCount         = 30                 ; maximum contour level count  
   ;cnres@cnLevelSelectionMode    = "EqualSpacedLevels"; color fill  
   cnres@cnFillPalette           = cmap(:,:)          ; subset the color map
   cnres@cnLinesOn               = False              ; no contour lines
   cnres@cnLineLabelsOn          = False              ; no contour labels
   cnres@cnInfoLabelOn           = False              ; no contour info label
   pltres@lbTitleString          = "Irradiance (W/m~S~2~N~)"
   pltres@lbTitleOffsetF         = -0.2
   pltres@lbTitleFontHeightF     = 0.02
   pltres@lbLabelFontHeightF     = 0.015
   pltres@gsnLeftString          = ""                 ; do not draw the left sub-title (otherwise automatically set)
   pltres@gsnRightString         = ""                 ; do not draw the right sub-title (otherwise automatically set
          
   mpres@mpDataBaseVersion       = "MediumRes"        ; better map outlines
   mpres@pmTickMarkDisplayMode   = "Always"           ; turn on tickmarks
   mpres@mpOutlineOn             = True               ; turn on map outline 
   mpres@mpOutlineBoundarySets   = "USStates"         ; turn on state boundaries
         
   pltres@tiMainString           = "One Hour GHI"
   pltres@tiMainFontHeightF      = 0.025              ; smaller title
   pltres@tiMainOffsetYF         = -0.005             ; move title down
               
   pltres@gsnAddCyclic           = False              ; regional data
   pltres@gsnMaximize            = True               ; enlarge image  

   ;mpres@mpLimitMode            = "Corners"          ; choose region of map
   ;mpres@mpLeftCornerLatF       = LAT2D(0,0)
   ;mpres@mpLeftCornerLonF       = LON2D(0,0)
   ;mpres@mpRightCornerLatF      = LAT2D(nlat-1,nlon-1)
   ;mpres@mpRightCornerLonF      = LON2D(nlat-1,nlon-1)

; The following 4 pieces of information are REQUIRED to properly display
; data on a native lambert conformal grid.  This data should be specified
; somewhere in the model itself, but in this case, it was not.
     
   ;mpres@mpProjection           = "LambertConformal" ;-- define the map projection (corresponds to 'lambert' in geogrid)
   ;mpres@mpLambertParallel1F    = 45.       ;-- corresponds to truelat1 in geogrid
   ;mpres@mpLambertParallel2F    = 33.       ;-- corresponds to truelat2 in geogrid
   ;mpres@mpLambertMeridianF     = -97.         ;-- corresponds to stand_lon in geogrid

; Usually, when data is placed onto a map, it is TRANSFORMED to the specified
; projection. Since this model is already on a native lambert conformal grid,
; we want to turn OFF the transformation.
     
   pltres@tfDoNDCOverlay = "NDCViewport"

;---Creat the plot 
   contour = wrf_contour(fwrf,wks,GHI(:,:),cnres)
   plot = wrf_map_overlays(fwrf,wks,(/contour/),pltres,mpres)      
   ;plot = gsn_csm_contour_map(wks,GHI(:,:),res)     ; Draw contours over a map.

end
