;---------------------------------------------
; regrid_1.ncl
;
; Concepts illustrated:
;   - Interpolating from one grid to another using bilinear interpolation
;   - Drawing color-filled contours over a cylindrical equidistant map
;   - Paneling two plots vertically on a page
;   - Adding a common labelbar to paneled plots
;   - Adding units attributes to lat/lon arrays
;   - Turning off the individual contour labelbar
;   - Manually creating lat/lon coordinate arrays 
;---------------------------------------------
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"  
;
; This file still has to be loaded manually
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"  

begin
;---Read in netCDF file
  in = addfile("sst.nc","r")

;---Read in data
  sst = in->TEMP(0,0,:,{0:360}); remove cyclic point
  lon = in->LON({0:360})

;---------------------------------------------
; interpolate to new grid
;---------------------------------------------

  newlat = fspan(-60.,60,24)
  newlon = fspan(0.,355.,72)
  newlat@units = "degrees_north"
  newlon@units = "degrees_east"

  newsst = linint2_Wrap(lon,sst&LAT,sst,True,newlon,newlat,0)

  newsst!0   ="lat"
  newsst!1   = "lon"
  newsst&lat = newlat
  newsst&lon = newlon

;---------------------------------------------
; start graphics
;---------------------------------------------

  wks = gsn_open_wks("png","regrid")           ; send graphics to PNG file

  res                     = True               ; plot mods desired
  res@cnFillOn            = True               ; turn on color   
  res@cnFillPalette       = "gui_default"      ; set color map
  res@cnLinesOn           = False              ; no contour lines
  res@cnLineLabelsOn      = False              ; no line labels

  res@mpMaxLatF           = 60                 ; choose map range
  res@mpMinLatF           = -60 

  res@gsnDraw             = False              ; don't draw yet
  res@gsnFrame            = False              ; don't advance frame yet

  res@cnLevelSelectionMode =  "ManualLevels"   ; manual levels
  res@cnMinLevelValF       = 4                 ; min level
  res@cnMaxLevelValF       = 32                ; max level
  res@cnLevelSpacingF      =  2                ; interval

  res@tmXBLabelFontHeightF     = 0.014         ; adjust some font heights
  res@tmYLLabelFontHeightF     = 0.014 
  res@tiMainFontHeightF        = 0.022
  res@txFontHeightF            = 0.017

  res@lbLabelBarOn             = False        ; turn off label bar

;---------------------------------------------
; create plots
;---------------------------------------------

  plot = new(2,graphic)

  res@tiMainString        = "Original Grid"
  plot(0) = gsn_csm_contour_map(wks,sst,res)  ; create the plot


  res@tiMainString        = "Grid after linint2"
  plot(1) = gsn_csm_contour_map(wks,newsst,res)  ; create the plot

;---------------------------------------------
; create panel
;---------------------------------------------

  pres                  = True
  pres@gsnPanelLabelBar = True                   ; common label bar
  gsn_panel(wks,plot,(/2,1/),pres)

end
