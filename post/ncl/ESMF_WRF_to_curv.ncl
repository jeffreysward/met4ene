;----------------------------------------------------------------------
; ESMF_WRF_to_curv.ncl
;
; This is an NCL/ESMF template file for regridding from a WRF 
; (curvilinear) grid to a different curvilinear grid. It uses
; ESMF_regrid to do the regridding.
;
; Both grids are assumed to be contained in separate NetCDF files.
; 
; Search for lines with ";;---Change (likely)" or ";;---Change (maybe)".
; These are the lines you will likely or maybe have to change.
;
; Of course, you'll probably want to change other aspects of this
; code, like the options for plotting (titles, colors, etc).
;
; For more information on ESMF_regrid, see: 
;
;    http://www.ncl.ucar.edu/Document/Functions/ESMF/ESMF_regrid.shtml
;----------------------------------------------------------------------
; This example uses the ESMF application "ESMF_RegridWeightGen" to 
; generate the weights.
;
; For more information about ESMF:
;
;        http://www.earthsystemmodeling.org/
;
; This script uses built-in functions that are only available in 
; NCL V6.1.0-beta and later.
;----------------------------------------------------------------------
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/esmf/ESMF_regridding.ncl"

begin
;---WRF file containing source grid
    src_file = "wrfout_xxxxx.nc"              ;;---Change (likely)
    sfile    = addfile(src_file,"r")

;---Get variable to regrid
    var     = wrf_user_getvar(sfile,"td2",0)  ;;---Change (likely)
    src_lat = sfile->XLAT(0,:,:)              ;;---Change (maybe)
    src_lon = sfile->XLONG(0,:,:)             ;;---Change (maybe)

;---Data file containing destination grid
    dst_file = "YYYY.nc"                      ;;---Change (likely)
    dfile    = addfile(dst_file,"r")
    dst_lat  = dfile->TLAT                    ;;---Change (likely)
    dst_lon  = dfile->TLON                    ;;---Change (likely)

;---Set up regridding options
    Opt                   = True

;---"bilinear" is the default. "patch" and "conserve" are other options.
    Opt@InterpMethod      = "bilinear"        ;;---Change (maybe)

    Opt@WgtFileName       = "WRF_to_curv.nc"

    Opt@SrcGridLat        = src_lat           ; source grid
    Opt@SrcGridLon        = src_lon
    Opt@SrcRegional       = True              ;;--Change (maybe)
    Opt@SrcInputFileName  = src_file          ; optional, but good idea

    Opt@DstGridLat        = dst_lat           ; destination grid
    Opt@DstGridLon        = dst_lon
    Opt@DstRegional       = True              ;;--Change (maybe)
    Opt@DstMask2D = where(.not.ismissing(dst_lat).and.\
                          .not.ismissing(dst_lon),1,0) ; Necessary if lat/lon
                                                       ; has missing values.
    Opt@ForceOverwrite    = True
    Opt@PrintTimings      = True
    Opt@Debug             = True

    var_regrid = ESMF_regrid(var,Opt)     ; Do the regridding

    printVarSummary(var_regrid)

;----------------------------------------------------------------------
; Plotting section
;
; This section creates filled contour plots of both the original
; data and the regridded data, and panels them.
;----------------------------------------------------------------------
    var@lat2d = src_lat     ; Needed for plotting. "var_regrid" 
    var@lon2d = src_lon     ; already has these attrs attached.

    wks = gsn_open_wks("ps","WRF_to_curv")

    res                       = True

    res@gsnMaximize           = True

    res@gsnDraw               = False
    res@gsnFrame              = False

    res@cnFillOn              = True
    res@cnLinesOn             = False
    res@cnLineLabelsOn        = False
    res@cnFillMode            = "RasterFill"

    res@lbLabelBarOn          = False    ; Turn on later in panel

    res@mpMinLatF             = min(src_lat)
    res@mpMaxLatF             = max(src_lat)
    res@mpMinLonF             = min(src_lon)
    res@mpMaxLonF             = max(src_lon)

;;--Change (maybe)
    mnmxint = nice_mnmxintvl( min(var), max(var), 18, False)
    res@cnLevelSelectionMode = "ManualLevels"
    res@cnMinLevelValF       = mnmxint(0)
    res@cnMaxLevelValF       = mnmxint(1)
    res@cnLevelSpacingF      = mnmxint(2)

;---Resources for plotting regridded data
    res@gsnAddCyclic  = False            ;;---Change (maybe)
    res@tiMainString  = "Curvilinear grid (" + Opt@InterpMethod + ")"

    plot_regrid = gsn_csm_contour_map(wks,var_regrid,res)

;---Resources for plotting original data
    res@gsnAddCyclic = False            ;;---Change (maybe)
    res@tiMainString = "Original WRF grid"

    plot_orig = gsn_csm_contour_map(wks,var,res)  

;---Compare the plots in a panel
    pres                   = True
    pres@gsnMaximize       = True
    pres@gsnPanelLabelBar  = True

    gsn_panel(wks,(/plot_orig,plot_regrid/),(/2,1/),pres)
end
