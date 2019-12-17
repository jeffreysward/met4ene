;----------------------------------------------------------------------
; WRF_cn_3.ncl
;
; Concepts illustrated:
;   - Plotting WRF data
;   - Plotting a cross section
;   - Using "sprintf" to create nicely formatted text strings
;----------------------------------------------------------------------
; WRF: latitude-z cross section.
;----------------------------------------------------------------------
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"   
; load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
;---Open file; substitute your own WRF output file here
  WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/wrfrun_r1bl5cu300ls2/"
 WRFfile = "wrfout_NYpvow_A5Dx3D_d03_2011-01-24_01:00:00"

 if (fileexists(WRFdir+WRFfile)) then
         f = addfile(WRFdir+WRFfile, "r")
 else
         print("")
         print("The WRF file "+WRFdir+WRFfile+" does not exist. Check your path.")
         print("")
   exit
 end if

  times = wrf_user_getvar(f,"times",-1)  ; get all time values on file

;
; Read variables at given time and lon indexes
; Read W(bottom_top_stag,west_east) at Time=2, lon=70
; Read associated levels and latitudes
;
  ntim = 0
  nlon = 70
  times = wrf_user_getvar(f,"times",-1)  ; get all time values on file
  w       = f->W(ntim,:,:,nlon)          ; W(bottom_top_stag,south_north)
  lat     = f->XLAT(ntim,:,nlon)         ; lon(west_east)    
  ;znw     = f->ZNW(ntim,:)               ; znw(bottom_top_stag)
  znw     = wrf_user_getvar(f,"z",1)               ; znw(bottom_top_stag)

;---Add/change meta data to conform to netCDF convention standards
  lat@units = "degrees_north"           ; CF recommended units
  w!0       = "lev"                     ; name dimensions
  w&lev     =  znw                      ; assign values to named dimensions
  w!1       = "lat"
  w&lat     =  lat
;---Use simple array syntax [like f90] to change units
  w         = w*100.                    ; for demo change units
  w@units   = "cm/s"                                             
;
; For labeling purposes only, determine the average 
; latitude of the cross section
;
  lon_avg = avg(f->XLONG(ntim,:,nlon))      ; avg is a built in function
;
; The "symMinMaxPlt" procedure determines contour limits that
; are symmetric.
; 
  wks = gsn_open_wks("png","WRF_cn")
  gsn_define_colormap(wks,"BlAqGrYeOrReVi200"); select color map

  res                       = True            ; plot mods desired
  res@gsnMaximize           = True            ; maximize plot size
  res@cnFillOn              = True            ; turn on color
  res@cnLinesOn             = False           ; turn off contour lines
  res@trYReverse            = True            ; reverse y axis
  res@tmXBTickSpacingF      = 10.             ; plot every 10th degree
  symMinMaxPlt(w, 14, False, res)             ; contributed.ncl

  res@tiMainString = times(ntim)+" avg(lon)=" + \
                     sprintf("%5.2f", lon_avg)  
  plot             = gsn_csm_contour(wks,w,res)
end

