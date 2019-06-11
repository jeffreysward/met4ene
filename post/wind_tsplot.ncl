;-----------------------------------------------------------------
;  Wind time series plot - outputs a png for displaying the 10m wind 
;  across the entire domain for each time slice contained withinin
;  the given wrfout file.
;
;  JAS 6.6.2019
;-----------------------------------------------------------------

loadscript("./cd_inv_string.ncl")
loadscript("./cd_string.ncl")

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
u  = wrf_user_getvar(a,"ua",-1)        ; u averaged to mass points
v  = wrf_user_getvar(a,"va",-1)        ; v averaged to mass points
z  = wrf_user_getvar(a, "z",-1)        ; grid point height
u_plane  = wrf_user_intrp3d( u,z,"h",100.,0.,False)
v_plane  = wrf_user_intrp3d( v,z,"h",100.,0.,False)
wspd = sqrt(u_plane^2 + v_plane^2)
wspd@long_name  = "Wind Speed at 100m"
wspd@short_name = "100wind"
wspd@units      = "m/s"
wspd@_FillValue = -999                 ; sets _FillValue to -999

;-----------------------------------------------------------------

n = 1
do it = 0,ntimes-1,1             ; TIME LOOP
  ;it = 0

   print("Working on time: " + times(it) )
   outfile = "./met_plots/NYpvow_A5Dx3D/2011jan23-24/wrfrun_r1bl5cu300ls2/100mWind_ts."+sprinti("%0.3i", n)

   time_numeric = cd_inv_string( times(it), "%Y-%N-%D_%H:%M:%S")  ;; will return in hours since 1800-01-01 unless specified otherwise
   offset = 5    			       ; hours
   time_numeric = time_numeric - offset
   time_str = cd_string( time_numeric, "%c %D, %Y %H:%M")

   ;---Set the workstation (x11, png, eps, ps, pdf, ncgm)
   wks  = gsn_open_wks("png",outfile)              ;-- open a workstation
   cmap = read_colormap_file("MPL_YlGn")         ;-- so we can subset later

   ;---Set plot resources
   res                        = True               ;-- plot mods desired
   res@cnFillOn               = True               ;-- color fill  
   res@cnSpanFillPalette      = True
   res@cnLevelSelectionMode   = "ManualLevels"
   res@cnMinLevelValF         = 1.               ;-- set min contour level
   res@cnMaxLevelValF         = 10.              ;-- set max contour level
   res@cnLevelSpacingF        = 1.
   ;res@cnMaxLevelCount        = 30                ;-- maximum contour level count  
   ;res@cnLevelSelectionMode   = "EqualSpacedLevels"  ;-- color fill  
   res@cnFillPalette          = cmap(:,:)          ;-- subset the color map
   res@cnLinesOn              = False              ;-- no contour lines
   res@cnLineLabelsOn         = False              ;-- no contour labels
   res@cnInfoLabelOn          = False              ;-- no contour info label
   res@lbTitleString          = "Wind Speed (m/s)"
   res@lbTitleOffsetF         = -0.2
   res@lbTitleFontHeightF     = 0.02
   res@lbLabelFontHeightF     = 0.015
   res@gsnLeftString          = ""                 ;-- do not draw the left sub-title (otherwise automatically set)
   res@gsnRightString         = ""                 ;-- do not draw the right sub-title (otherwise automatically set)
   res@gsnCenterString        = time_str	   ;-- write time to center string
   res@gsnCenterStringOrthogonalPosF = 0.02        ;-- move center string upwards
          
   res@mpDataBaseVersion      = "MediumRes"        ;-- better map outlines
   res@pmTickMarkDisplayMode  = "Always"           ;-- turn on tickmarks
   res@mpOutlineOn           = True                ;-- turn on map outline 
   res@mpOutlineBoundarySets = "USStates"          ;-- turn on state boundaries (but only in MediumRes)
         
   res@tiMainString           = "100 Meter Wind Speed"
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
   plot = gsn_csm_contour_map(wks,wspd(it,:,:),res)     ; Draw contours over a map.


   n := n + 1
  end do        ; END OF TIME LOOP

end
