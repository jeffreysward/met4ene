
; Example series of plotting meteograms with WRF ARW model data
; First let's just get and plot t2 at a point
; Add some inrfto to the plot
; Add slp to the plot
; Add a time-Z plot above slp and t2
; Use wrf_user_ll_to_ij to get the point of interest


;***********************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
;***********************************************
begin
;***********************************************

; The WRF ARW input file.
WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/err.wrfrun_z46r1bl5cu300ls2/"
WRFfile = "wrfout_d03_2011-01-24_01:00:00"

if (fileexists(WRFdir+WRFfile)) then
         a = addfile(WRFdir+WRFfile, "r")
else
         print("")
         print("The WRF file "+WRFdir+WRFfile+" does not exist. Check your path.")
	 print("")
         exit
end if

;-----------------------------------------------------------------------

; Find the ij location for the point if interest
  llres = True
  llres@ReturnInt = True   ; Return integer values
  locij = wrf_user_ll_to_ij(a, -87., 32.5, llres)
  locij = locij - 1        ; array pointers in NCL space
  locX = locij(0)
  locY = locij(1)

  taus = (/ 1., 2., 3., 4., 5. /)       ; create a time reference

; get time information and strip out the day and hour
  times_in_file = a->Times
  dims = dimsizes(times_in_file)
  times = new(dims(0),string)
  do i=0,dims(0)-1
    times(i) = chartostring(times_in_file(i,8:12))
  end do

  wks = gsn_open_wks("x11","meteo4")    ; open a workstation

;-----------------------------------------------------------------------

  t2    = wrf_user_getvar(a,"T2",-1)    ; get t2 for all times
  slp   = wrf_user_getvar(a,"slp",-1)   ; get slp for all times
  tc    = wrf_user_getvar(a,"tc",-1)    ; get tc for all times
  uvmet = wrf_user_getvar(a,"uvmet",-1) ; get rotated u and v comp of wind

  umet = uvmet(0,:,:,:,:)
  vmet = uvmet(1,:,:,:,:)

  t2_point  = t2(:,locY,locX)           ; extract a time series at a point
  slp_point  = slp(:,locY,locX)
  tc_point  = tc(:,:,locY,locX)
  u_point   = umet(:,:,locY,locX)
  v_point   = vmet(:,:,locY,locX)

; Swap the dimensions as we want to plot time on the X axis later
  tt        = tc_point(bottom_top|:,Time|:)
  ugrid     = u_point(bottom_top|:,Time|:)
  vgrid     = v_point(bottom_top|:,Time|:)

;-----------------------------------------------------------------------

  res2D = True                            ; Set basic resources 
  res2D@gsnDraw              = False      ; Don't draw individual plot.
  res2D@gsnFrame             = False      ; Don't advance frame.
  res2D@vpXF                 = 0.15       ; x location
  res2D@vpYF                 = 0.90       ; y location
  res2D@vpWidthF             = 0.70       ; width
  res2D@vpHeightF            = 0.40       ; height
  res2D@tiXAxisString        = "Day_Time"
  res2D@tiXAxisFontHeightF   = 0.016
  res2D@tmXBMode             = "Explicit"
  res2D@tmXBValues           = taus
  res2D@tmXBLabels           = times
  res2D@tmXBLabelJust        = "CenterCenter"
  res2D@tmXBLabelFontHeightF = .012



  tt_res = res2D
  tt_res@sfXArray         = taus
  tt_res@gsnSpreadColors  = True          ; use full range of colors
  tt_res@cnFillOn         = True          ; turns on color fill


  uv_res = res2D
  uv_res@vfXArray         = taus
  uv_res@vcRefAnnoOn      = False         ; turns off the ref vector
  uv_res@vcRefLengthF     = 0.040         ; set length of ref vector
  uv_res@vcGlyphStyle     = "WindBarb"    ; turn on wind barbs


;-----------------------------------------------------------------------

  res1D = True                            ; Set basic resources both will use
  res1D@vpXF              = 0.15          ; The left side of the box location
  res1D@vpWidthF          = 0.70          ; The Width of the plot box
  res1D@vpHeightF         = 0.10          ; The height of the plot box
  res1D@tmXBMode          = "Explicit"    ; Define own tick mark labels.
  res1D@tmXBValues        = taus          ; location of explicit labels
  res1D@tmXBLabels        = times         ; labels are the locations
  res1D@tmXTOn            = False         ; turn off the top tick marks
  res1D@xyLineThicknesses = 2             ; increase line thickness
  res1D@gsnDraw           = False         ; Don't draw individual plot.
  res1D@gsnFrame          = False         ; Don't advance frame.
  

  slp_res = res1D
  slp_res@vpYF            = 0.35          ; The top side of the plot box loc
  slp_res@xyLineColor     = "red"         ; set line color


  t2_res = res1D
  t2_res@vpYF             = 0.20          ; The top side of the plot box loc
  t2_res@xyLineColor      = "blue"        ; set line color

;-----------------------------------------------------------------------

  ttfill    = gsn_contour(wks,tt,tt_res)
  windlayer = gsn_vector(wks,ugrid,vgrid,uv_res)
  overlay(ttfill,windlayer)

  slp_plot  = gsn_csm_xy(wks,taus,slp_point,slp_res)
  t2_plot  = gsn_csm_xy(wks,taus,t2_point,t2_res)

  draw(ttfill) 
  draw(slp_plot) 
  draw(t2_plot) 

  frame(wks)                            ; now frame the plot   

;-----------------------------------------------------------------------

end
