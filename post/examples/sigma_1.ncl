;************************************
; sigma_1.ncl
;************************************
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
;************************************
begin
;************************************
; open netcdf file and read in data
; this dataset is a 2D shelf model with the 
; y-axis being distance in m from the bottom 
; of the shelf to the surface, and the
; x-axis being distance along the shelf
;***********************************
 WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/wrfrun_r1bl5cu300ls2/"
 WRFfile = "wrfout_NYpvow_A5Dx3D_d03_2011-01-24_01:00:00"

 if (fileexists(WRFdir+WRFfile)) then
         in = addfile(WRFdir+WRFfile, "r")
 else
         print("")
         print("The WRF file "+WRFdir+WRFfile+" does not exist. Check your path.")
         print("")
	 exit
 end if
 y   = wrf_user_getvar(in,"z",0)                          ; dimensioned (dist,sigma)
 d   = wrf_user_getvar(in,"pres",0)
;************************************
; create new depth array
; we will interpolate the sigma coords 
; to these values
;***********************************
 depth         = new(120,"float")
 depth(0:19)   = ispan(0,99,5)
 depth(20:119) = ispan(100,199,1)
;************************************
; interpolate y (sigma) to depth
; arguments (sigma values for column,data values for column,
;***********************************
 nosigma = new((/4000,dimsizes(depth)/),"float")
; because each column has a unique set of coordinates, we
; must interpolate them individually. The total number of
; interpolations here (4000) slows the execution down a bit.

 nosigma             = linint1(y,d,False,depth,0)
 nosigma!0           = "dist"
 nosigma!1           = "depth"
 nosigma_s           = nosigma(depth|:,dist|:)
 nosigma_s@long_name = d@long_name     ; long_name used auto by plot template
;************************************
; create plot
;***********************************
 wks = gsn_open_wks("png","sigma")        ; send graphics to PNG file

 res                      = True          ; plot mods desired

 res@cnFillOn             = True          ; turn on color fill
 res@cnFillPalette        = "gui_default" ; set color map
 res@cnLinesOn            = False         ; turn off contour lines
 res@lbOrientation        = "vertical"    ; vertical label bar

 res@sfXArray             = y&dist        ; x axis array
 res@sfYArray             = depth         ; y axis array

 res@tiYAxisString        = "Dist from bottom to surface (m)"
 res@tiXAxisString        = "Dist from origin (km)"

 res@tiMainString              = "Data now in regular coordinates"

 plot = gsn_csm_contour(wks,nosigma_s,res); create plot
;************************************
end
