;***************************************************************************
; narr_6.ncl
;***************************************************************************
; [1] Read NARR Grib file
; [2] Draw outlines of NARR grid + selected grid line and cross-sections
;**************************************************************
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
;**************************************************

;======================================================================
; User specifications
;======================================================================
    srcDirName   = "./"
    srcFileName  = "merged_AWIP32.1979010100.3D.NARR.grb"

    varName      = "U_GRD_221_ISBL"

    wksType      = "png"              ; ps, png, pdf, x11, ....
    wksDirName   = "./"   
    wksFileName  = "narr" 

;======================================================================
; Miscellaneous; One time settings
;======================================================================
    srcFilePath  = srcDirName + srcFileName
    wksFilePath  = wksDirName + wksFileName

    sfile        = addfile(srcFilePath,"r")    
    lat2d        = sfile->gridlat_221             ; (gridx_221, gridy_221) => (277,349)
    lon2d        = sfile->gridlon_221           

    var          = sfile->$varName$               ; ( lv_ISBL0, gridx_221, gridy_221 )
    dimvar       = dimsizes(var)
    klev         = dimvar(0)                      ; 29
    nlat         = dimvar(1)                      ; 277
    mlon         = dimvar(2)                      ; 349
;********************************************
;   Draw map background
;********************************************

   wks = gsn_open_wks(wksType, wksFilePath)       ; open workstation
   gsn_define_colormap(wks,"default")
   res            = True                          ; map resources
  ;res@gsnDraw    = False                         ; don't draw
   res@gsnFrame   = False                         ; don't advance frame
   res@mpMaxLatF  =  90.0                         ; select subregion
   res@mpMinLatF  =   0.0 
   res@mpMinLonF  = 145.0
   res@mpMaxLonF  = 360.0
   res@mpCenterLonF  = 253                        ; 0.5*(res@mpMinLonF + res@mpMaxLonF)
   res@gsnCenterString  = "NARR Lambert Conformal: Selected Grid Outlines and Cross-Sections" 

   pres                  = True                   ; polyline resources
   pres@gsLineThicknessF = 2.0                    ; line thickness
   pres@tfPolyDrawOrder  = "PostDraw"

   map = gsn_csm_map(wks,res)                     ; create map
 
;********************************************
; draw outline of the NARR grid
;********************************************
   pres@gsLineColor = "black"
   gsn_polyline(wks,map,lon2d(:,   0     ),lat2d(:,    0    ),pres)   ; leftmost grid boundary
   gsn_polyline(wks,map,lon2d(:,mlon-1   ),lat2d(:,mlon-1   ),pres)   ; rightmost
   gsn_polyline(wks,map,lon2d(     0   ,:),lat2d(      0  ,:),pres)   ; southernmost
   gsn_polyline(wks,map,lon2d(  nlat-1 ,:),lat2d(  nlat-1 ,:),pres)   ; northernmost

  ;print("lat2d(:,mlon-1)="+lat2d(:,mlon-1)+"   lon2d(:,mlon-1)="+lon2d(:,mlon-1))
 
;********************************************
; draw several user specified grid outlines that span the entire grid
;********************************************
   nlGrid       = (/100, 150, 200 /)   
   mlGrid       = (/100, 175, 250 /)       

   do i=0,dimsizes(nlGrid)-1
      pres@gsLineColor = "red"
      gsn_polyline(wks,map,lon2d(:,mlGrid(i)),lat2d(:,mlGrid(i)),pres)

      pres@gsLineColor = "blue"
      gsn_polyline(wks,map,lon2d(nlGrid(i),:),lat2d(nlGrid(i),:),pres)
   end do

;********************************************
; draw several user specified outlines 
; user must specify the start and end indices
;********************************************
      pres@gsLineThicknessF = 3.0                ; line thickness

      pres@gsLineColor = "Green"
      nlStrt =  85 
      nlLast = 160 
      mlx    = 125
      gsn_polyline(wks,map,lon2d(nlStrt:nlLast,mlx),lat2d(nlStrt:nlLast,mlx),pres)

      pres@gsLineColor = "Orange"
      mlStrt = 190 
      mlLast = 300 
      nlx    = 125
      gsn_polyline(wks,map,lon2d(nlx,mlStrt:mlLast),lat2d(nlx,mlStrt:mlLast),pres)
   frame(wks)                                         

;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
; Create resources for cross section(s)
;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   resx = True
   resx@gsnMaximize          = True  
  ;resx@gsnSpreadColors      = True            ; spread out color table [default v6.1.0]
  ;resx@lbLabelAutoStride    = True            ; default v6.1.0
  
   resx@cnFillOn             = True            ; turn on color fill
   resx@cnLinesOn            = False           ; turn lines on/off         ; True is default
   resx@cnLineLabelsOn       = False           ; turn line labels on/off   ; True is default
   resx@cnFillPalette        = "ncl_default"


   nLabels                   = 8               ; arbitrary  
   resx@tmXBLabels           = new(nLabels,"string")
   resx@tmXBMode             = "Explicit"

;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
; Draw Full S-N cross section at a specified longitude grid line
;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    ml = 200
    resx@tmXBValues         := toint( fspan(0,nlat-1,nLabels) )
    do i=0,nLabels-1
       x = lon2d(resx@tmXBValues(i),ml)
       y = lat2d(resx@tmXBValues(i),ml)
       resx@tmXBLabels(i) = sprintf("%5.1f", y)+"~C~"+sprintf("%5.1f", x)
    end do
   
    resx@tiMainString = "Full South-North Grid Line X-Section: ml="+ml
    plot  = gsn_csm_pres_hgt(wks, var(:,:,ml), resx )   ; (29, 349) at ml

;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
; Draw Full W-E  cross section at a specified latitude grid line
;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    nl = 150
    resx@tmXBValues         := toint( fspan(0,mlon-1,nLabels) )
    do i=0,nLabels-1
       x = lon2d(nl,resx@tmXBValues(i))
       y = lat2d(nl,resx@tmXBValues(i))
       resx@tmXBLabels(i) = sprintf("%5.1f", y)+"~C~"+sprintf("%5.1f", x)
    end do
    resx@tiMainString = "Full West-East Grid Line X-Section: nl="+nl
    plot  = gsn_csm_pres_hgt(wks, var(:,nl,:), resx )   ; (29, 277) at ml

;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
; Draw Subset N-S cross section at a specified longitude grid line
;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    resx@tmXBValues         := toint( fspan(0,(nlLast-nlStrt),nLabels) )
    do i=0,nLabels-1
       x = lon2d(resx@tmXBValues(i),mlx)
       y = lat2d(resx@tmXBValues(i),mlx)
       resx@tmXBLabels(i) = sprintf("%5.1f", y)+"~C~"+sprintf("%5.1f", x)
    end do
    resx@tiMainString = "Subset South-North Grid Line X-Section: ml="+mlx+" nl=["+nlStrt+":"+nlLast+"]"
    plot  = gsn_csm_pres_hgt(wks, var(:,nlStrt:nlLast,mlx), resx )   ; (29, ...) from nlStrt to nlLast

;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
; Draw Subset W-E cross section at a specified latitude grid line
;+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    resx@tmXBValues         := toint( fspan(0,(mlLast-mlStrt),nLabels) )
    do i=0,nLabels-1
       x = lon2d(nlx,resx@tmXBValues(i))
       y = lat2d(nlx,resx@tmXBValues(i))
       resx@tmXBLabels(i) = sprintf("%5.1f", y)+"~C~"+sprintf("%5.1f", x)
    end do
    plot  = gsn_csm_pres_hgt(wks, var(:,nlx,mlStrt:mlLast), resx )   ; (29, ...) from mlStrt to mlLast
    resx@tiMainString = "Subset West-East Grid Line X-Section: nl="+nlx+" ml=["+mlStrt+":"+mlLast+"]"
