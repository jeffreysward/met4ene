;-----------------------------------------------------------------
;  DHI time series plot - outputs a png for displaying the DHI     
;  across the entire domain for each time slice contained withinin
;  the given wrfout file.
;
;  JAS 2.25.2018
;-----------------------------------------------------------------

begin

; Load the WRF input file.  
WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/solar_wfp/wrfprd_jan01-05/"
WRFfile = "wrfout_d03_2010-12-31_12:00:00"
  
if (fileexists(WRFdir+WRFfile)) then
   a = addfile(WRFdir+WRFfile, "r")
else
   print("")
   print("The wrfout file "+WRFdir+WRFfile+" does not exist. Check your path.")
   print("")
   exit
end if

ilay = 0
LAT2D = a->XLAT(0,:,:)  
nlat = dimsizes(LAT2D(:,0))
LAT2D@units = "degrees_north"
;printVarSummary(LAT2D)

LON2D = a->XLONG(0,:,:)
nlon = dimsizes(LAT2D(0,:))
LON2D@units = "degrees_east"
;printVarSummary(LON2D)

;-----------------------------------------------------------------

; What times and how many time steps are in the data set?
times = wrf_user_getvar(a,"times",-1)  ; get all times in the file
ntimes = dimsizes(times)               ; number of times in the file

;-----------------------------------------------------------------

n = 1
do it = 0,ntimes-1,1             ; TIME LOOP
  ;it = 0

   print("Working on time: " + times(it) )
   outfile = "./pwr_plots/2010dec31/DHI_Time_Series."+sprinti("%0.3i", n)

   ;---Variables from wrfout file
   DNI  = a->SWDDNI(it,:,:)      
   DHI  = a->SWDDIF(it,:,:)    
   GHI = DNI+DHI
   GHI@long_name = "Global Horizontal Irradiance"
   ;printVarSummary(GHI)


   ;---Set the workstation (x11, png, eps, ps, pdf, ncgm)
   wks  = gsn_open_wks("png",outfile)              ;-- open a workstation
   cmap = read_colormap_file("MPL_YlOrRd")         ;-- so we can subset later

   ;---Set plot resources
   res                        = True               ;-- plot mods desired
   res@cnFillOn               = True               ;-- color fill  
   res@cnSpanFillPalette      = True
   res@cnLevelSelectionMode   = "ManualLevels"
   res@cnMinLevelValF         = 40.                ;-- set min contour level
   res@cnMaxLevelValF         = 400.               ;-- set max contour level
   res@cnLevelSpacingF        = 40.
   ;res@cnMaxLevelCount        = 30                ;-- maximum contour level count  
   ;res@cnLevelSelectionMode   = "EqualSpacedLevels"  ;-- color fill  
   res@cnFillPalette          = cmap(:,:)          ;-- subset the color map
   res@cnLinesOn              = False              ;-- no contour lines
   res@cnLineLabelsOn         = False              ;-- no contour labels
   res@cnInfoLabelOn          = False              ;-- no contour info label
   res@lbTitleString          = "Irradiance (W/m~S~2~N~)"
   res@lbTitleOffsetF         = -0.2
   res@lbTitleFontHeightF     = 0.02
   res@lbLabelFontHeightF     = 0.015
   res@gsnLeftString          = ""                 ;-- do not draw the left sub-title (otherwise automatically set)
   res@gsnRightString         = ""                 ;-- do not draw the right sub-title (otherwise automatically set)
   res@gsnCenterString        = times(it)          ;-- write time to center string
   res@gsnCenterStringOrthogonalPosF = 0.02        ;-- move center string upwards
          
   res@mpDataBaseVersion      = "HighRes"          ;-- better map outlines
   res@pmTickMarkDisplayMode  = "Always"           ;-- turn on tickmarks
   res@mpOutlineOn           = True                ;-- turn on map outline 
   res@mpOutlineBoundarySets = "USStates"          ;-- turn on state boundaries
         
   res@tiMainString           = "Diffuse Horizontal Irradiance"
   res@tiMainFontHeightF      = 0.025              ;-- smaller title
   res@tiMainOffsetYF         = -0.005             ;-- move title down
               
   res@gsnAddCyclic           = False              ;-- regional data
   res@gsnMaximize            = True               ;-- enlarge image  

   res@mpLimitMode            = "Corners"          ;-- choose region of map
   res@mpLeftCornerLatF       = LAT2D(0,0)
   res@mpLeftCornerLonF       = LON2D(0,0)
   res@mpRightCornerLatF      = LAT2D(nlat-1,nlon-1)
   res@mpRightCornerLonF      = LON2D(nlat-1,nlon-1)

; The following 4 pieces of information are REQUIRED to properly display
; data on a native lambert conformal grid.  This data should be specified
; somewhere in the model itself, but in this case, it was not.
     
   res@mpProjection           = "LambertConformal" ;-- define the map projection (corresponds to 'lambert' in geogrid)
   res@mpLambertParallel1F    = 45.                ;-- corresponds to truelat1 in geogrid
   res@mpLambertParallel2F    = 33.                ;-- corresponds to truelat2 in geogrid
   res@mpLambertMeridianF     = -97.               ;-- corresponds to stand_lon in geogrid

; Usually, when data is placed onto a map, it is TRANSFORMED to the specified
; projection. Since this model is already on a native lambert conformal grid,
; we want to turn OFF the transformation.
     
   res@tfDoNDCOverlay = "NDCViewport"

;---Creat the plot       
   plot = gsn_csm_contour_map(wks,DHI(:,:),res)     ; Draw contours over a map.


   n := n + 1
  end do        ; END OF TIME LOOP

end
