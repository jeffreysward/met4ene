;----------------------------------------------------------------------
; h_lat_6.ncl
;----------------------------------------------------------------------
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"   
;----------------------------------------------------------------------
begin
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
  u     = f->U(0,:,:,0)                             ; get u for January
  u&lev = u(:,0)
  v     = f->V(0,:,:,0)
  ;wind  = sqrt(u^2+v^2)

  wks   = gsn_open_wks ("x11", "h_lat" )          

  res                      = True                 ; plot mods desired

  res@cnLevelSelectionMode = "ManualLevels"       ; manually select levels
  res@cnLevelSpacingF      = 5.0                  ; contour spacing
  res@cnMinLevelValF       = -50.                 ; min level
  res@cnMaxLevelValF       =  50.                 ; max level
  res@cnLineLabelsOn       = True                 ; turn on line labels
  res@cnFillOn             = True                 ; turn on color fill
  res@cnFillPalette        = "BlWhRe"             ; choose colormap
  ;res@tiYAxisString        = u&lev@long_name + " (" + u&lev@units + ")"   

; Note: u is already on pressure levels. If this were model data, it
; would be necessary to interpolate from the hybrid coordinates to 
; pressure levels.
  
  plot  = gsn_csm_pres_hgt(wks, u, res )   ; place holder
  
end
