;----------------------------------------------------------------------
; wrf_gsn_1.ncl
;----------------------------------------------------------------------
; Concepts illustrated:
;   - Using gsn_csm_contour_map to plot WRF-ARW data
;----------------------------------------------------------------------
; The key to making gsn_csm_contour_map work with WRF data is:
; 
; 1. Reading XLAT/XLONG off the file and attaching them as 
;    special "lat2d" and "lon2d" attributes of the data to 
;    be plotted.
;
; 2. Zooming in on the map (WRF data is regional and NCL
;    creates global plots by default).
;----------------------------------------------------------------------; 
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
;---Open WRF output file.
  dir      = "../wrfout/"
  filename = "wrfout_d01_2019-01-29_06:00:00"
  a = addfile(dir + filename + ".nc","r")

;---Read terrain height and lat/lon off file.
  it        = 4     ; first time step
  hgt       = wrf_user_getvar(a,"SWDOWN",it)    ; Terrain elevation
  hgt@lat2d = wrf_user_getvar(a,"XLAT",it)   ; latitude/longitude
  hgt@lon2d = wrf_user_getvar(a,"XLONG",it)  ; required for plotting

  wks = gsn_open_wks("x11","wrf_gsn")

;---Set some basic plot options
  res               = True

  res@gsnMaximize   = True   ; maximize plot in frame

  res@tiMainString  = filename

  res@cnFillOn      = True  
  res@cnFillPalette = "OceanLakeLandSnow"
  res@cnLinesOn     = False

  res@mpProjection  = "CylindricalEquidistant"    ; The default
  res@mpDataBaseVersion = "MediumRes"

  res@gsnAddCyclic      = False

;---Zoom in on plot
  res@mpMinLatF     = min(hgt@lat2d)
  res@mpMaxLatF     = max(hgt@lat2d)
  res@mpMinLonF     = min(hgt@lon2d)
  res@mpMaxLonF     = max(hgt@lon2d)

  contour = gsn_csm_contour_map(wks,hgt,res)

end