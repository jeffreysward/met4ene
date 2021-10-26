
;   Script display location of model domains
;   Only works for ARW domains
;   Reads namelist file directly

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
;load "./WRFUserARW.ncl"

begin
;

; We generate plots, but what kind do we prefer?
  type = "x11"
;  type = "pdf"
;  type = "ps"
;  type = "ncgm"
  wks = gsn_open_wks(type,"wps_show_dom")

; Set the colors to be used
  colors = (/"white","black","White","ForestGreen","DeepSkyBlue","Red","Blue"/)
  gsn_define_colormap(wks, colors)  


; Set some map information ; line and text information
  mpres = True
  mpres@mpFillOn = True
  mpres@mpFillColors  = (/"background","DeepSkyBlue","ForestGreen","DeepSkyBlue", "transparent"/)
  mpres@mpGeophysicalLineColor      = "Black"
  mpres@mpGridLineColor             = "Black"
  mpres@mpLimbLineColor             = "Black"
  mpres@mpNationalLineColor         = "Black"
  mpres@mpPerimLineColor            = "Black"
  mpres@mpUSStateLineColor          = "Black"
  mpres@mpGridSpacingF              = 1
  mpres@tiMainString                = " WPS Domain Configuration  "

  lnres = True 
  lnres@gsLineThicknessF = 2.5
  lnres@domLineColors    = (/ "white", "Red" , "Red" , "Blue" /)

  txres = True
  txres@txFont = "helvetica-bold"
  ;txres@txJust = "BottomLeft"
  txres@txJust = "TopLeft"
  txres@txPerimOn = False
  txres@txFontHeightF = 0.015

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
DOMS = 3
DX = 9.
;DX = 12.
;DX = 36.
MAP = "lambert"
;MAP = "mercator"
LAT1 = (/ 37., 38., 39.3 /)		; original lambert grids
LAT2 = (/ 46., 42., 40.9 /)
LON1 = (/ -82., -78., -74.5 /)
LON2 = (/ -70., -71., -72.3 /)
;LAT1 = (/ 37., 38., 39.3 /)		; original lambert grids
;LAT2 = (/ 46., 42., 40.9 /)
;LON1 = (/ -82., -78., -74.5 /)
;LON2 = (/ -70., -71., -72.3 /)
;LAT1 = (/ -50., -45., -27. /)		; modified mercator grids
;LAT2 = (/ -11., -20., -23. /)
;LON1 = (/ 113., 121., 125./)
;LON2 = (/ 163., 159., 131./)
;LAT1 = (/ -35.0, -45., -27. /)		; Yasi Domains
;LAT2 = (/   0., -20., -23. /)
;LON1 = (/ 131., 121., 125./)
;LON2 = (/ 171., 159., 131./)
;LAT1 = (/ -43.0, -45., -27. /)		; Yasi Domains
;LAT2 = (/   5., -20., -23. /)
;LON1 = (/  95., 121., 125./)
;LON2 = (/ 179., 159., 131./)
parent_id = (/ 0, 1, 2 /)
parent_grid_ratio = (/ 1, 3, 3 /)

std_truelats = False

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Do not change anything between the ";;;;;" lines

  mpres@max_dom   = DOMS
  mpres@map_proj  = MAP
  mpres@dx        = DX*1000.
  mpres@dy        = DX*1000.
  mpres@ref_lat   = LAT1(0) + (LAT2(0)-LAT1(0))/2.
  mpres@ref_lon   = LON1(0) + (LON2(0)-LON1(0))/2.
  mpres@stand_lon = mpres@ref_lon
  
  if (MAP .eq. "lambert") then
    if ( std_truelats ) then
      if (LAT1(0) .gt. 0.) then
        mpres@truelat1 = 30.
        mpres@truelat2 = 60.
      else
        mpres@truelat1 = -30.
        mpres@truelat2 = -60.
      end if
    else
      truelat1 = floattoint(LAT1(0) + (LAT2(0)-LAT1(0))/3)
      truelat2 = floattoint(truelat1 + (LAT2(0)-LAT1(0))/3)
      mpres@truelat1 = int2flt(truelat1)
      mpres@truelat2 = int2flt(truelat2)
    end if
  end if
  if (MAP .eq. "mercator") then
    mpres@truelat2 = 0.
    if ( std_truelats ) then
      mpres@truelat1 = 0.
    else
      truelat1 = floattoint(mpres@ref_lat)
      mpres@truelat1 = int2flt(truelat1)
    end if
  end if

  e_we = new ( DOMS, integer ) 
  e_sn = new ( DOMS, integer ) 
  e_we(0) = floattoint((LON2(0)-LON1(0))*111./DX)
  e_sn(0) = floattoint((LAT2(0)-LAT1(0))*111./DX)
  centeri = e_we(0)/2 + 1
  centerj = e_sn(0)/2 + 1

  i_parent_start = new ( DOMS, integer ) 
  j_parent_start = new ( DOMS, integer ) 
  i_parent_start(0) = 1
  j_parent_start(0) = 1

  ;print(mpres)
  ;print("Number of grid points " + e_we(0) + " " + e_sn(0) )


  if ( DOMS .gt. 1 ) then

    mpres@parent_id         = parent_id
    mpres@parent_grid_ratio = parent_grid_ratio

    res = True
    if (MAP .eq. "lambert") then
      res@MAP_PROJ  = 1
    end if
    if (MAP .eq. "mercator") then
      res@MAP_PROJ  = 3
    end if
    res@TRUELAT1  = mpres@truelat1
    res@TRUELAT2  = mpres@truelat2
    res@STAND_LON = mpres@stand_lon
    res@DX        = mpres@dx
    res@DY        = mpres@dy
    res@REF_LAT   = mpres@ref_lat
    res@REF_LON   = mpres@ref_lon
    res@KNOWNI    = centeri
    res@KNOWNJ    = centerj

    ratio = 1
    ratio_start = 1
    istart = 1
    jstart = 1
    do ii=1,DOMS-1
      ratio = ratio * parent_grid_ratio(ii)
      loc = wrf_ll_to_ij (LON1(ii),LAT1(ii),res)
      loci1 = new(dimsizes(loc),integer)
      loci1 = tointeger(loc + .5)
      loci1!0 = loc!0
      ;print("DOM="+ii + "  start " + loci1)
      loc = wrf_ll_to_ij (LON2(ii),LAT2(ii),res)
      loci2 = new(dimsizes(loc),integer)
      loci2 = tointeger(loc + .5)
      loci2!0 = loc!0
      ;print("DOM="+ii + "    end " + loci2)
      e_we(ii) = (loci2(0)-loci1(0))*ratio + 1
      e_sn(ii) = (loci2(1)-loci1(1))*ratio + 1
      istart = (loci1(0) - istart + 1)*ratio_start
      jstart = (loci1(1) - jstart + 1)*ratio_start
      i_parent_start(ii) = istart
      j_parent_start(ii) = jstart
      ;print("Number of grid points " + e_we(ii) + " " + e_sn(ii) )
      ;print("Start locations " + istart + " " + jstart)
      ratio_start = ratio
    end do
   
  end if

  print("Suggested namelist options")
  xxx = "parent_id ="
  do ii=0,DOMS-1
    xxx = xxx + " " + parent_id(ii) + ","
  end do
  print(" " + xxx)
  xxx = "parent_grid_ratio ="
  do ii=0,DOMS-1
    xxx = xxx + " " + parent_grid_ratio(ii) + ","
  end do
  print(" " + xxx)
  xxx = "i_parent_start ="
  do ii=0,DOMS-1
    xxx = xxx + " " + i_parent_start(ii) + ","
  end do
  print(" " + xxx)
  xxx = "j_parent_start ="
  do ii=0,DOMS-1
    xxx = xxx + " " + j_parent_start(ii) + ","
  end do
  print(" " + xxx)
  xxx = "e_we ="
  do ii=0,DOMS-1
    xxx = xxx + " " + e_we(ii) + ","
  end do
  print(" " + xxx)
  xxx = "e_sn ="
  do ii=0,DOMS-1
    xxx = xxx + " " + e_sn(ii) + ","
  end do
  print(" " + xxx)
  print(" dx = " + mpres@dx + ",")
  print(" dy = " + mpres@dy + ",")
  print(" map_proj = '" + mpres@map_proj + "',")
  print(" ref_lat = " + sprintf("%7.2f",mpres@ref_lat) + ",")
  print(" ref_lon = " + sprintf("%7.2f",mpres@ref_lon) + ",")
  print(" truelat1 = " + sprintf("%7.2f",mpres@truelat1) + ",")
  print(" truelat2 = " + sprintf("%7.2f",mpres@truelat2) + ",")
  print(" stand_lon = " + sprintf("%7.2f",mpres@stand_lon) + ",")
  
  mpres@e_we = e_we
  mpres@e_sn = e_sn
  mpres@i_parent_start = i_parent_start
  mpres@j_parent_start = j_parent_start

  mp = wrf_wps_dom (wks,mpres,lnres,txres)
  pmres = True
  pmres@gsMarkerColor = "White"
  pmres@gsMarkerIndex = 16
  pmres@gsMarkerSizeF = 0.01
  gsn_polymarker(wks,mp,128.00,-25.00,pmres)
  frame(wks)   

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;



end
