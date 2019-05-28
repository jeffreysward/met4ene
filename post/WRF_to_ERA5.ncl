;----------------------------------------------------------------------
; WRF_to_ERA5.ncl
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
    WRFdir   = "/glade/scratch/sward/tmp/2012-08-10_00-00-00/"
    WRFfile  = "wrfout_d03_2012-08-10_00:00:00"
    if (fileexists(WRFdir+WRFfile)) then
        sfile = addfile(WRFdir+WRFfile, "r")
    else
        print("")
        print("The wrfout file "+WRFdir+WRFfile+" does not exist. Check your path.")
        print("")
        exit
    end if

;---Get variable to regrid
    var     = wrf_user_getvar(sfile,"td2",0)  ;;---Change (likely)
    src_lat = sfile->XLAT(0,:,:)              ;;---Change (maybe)
    src_lon = sfile->XLONG(0,:,:)             ;;---Change (maybe)

;---Data file containing destination grid
    ERAdir   = "/gpfs/fs1/collections/rda/data/ds630.0/e5.oper.an.sfc/201208/"
    ERAfile  = "e5.oper.an.sfc.128_167_2t.regn320sc.2012080100_2012083123.nc"
    if (fileexists(ERAdir+ERAfile)) then
        dfile = addfile(ERAdir+ERAfile, "r")
    else
        print("")
        print("The wrfout file "+ERAdir+ERAfile+" does not exist. Check your path.")
        print("")
        exit
    end if 

    dst_lat  = dfile->latitude                    ;;---Change (likely)
    dst_lon  = dfile->longitude                   ;;---Change (likely)
    dst_2t   = dfile->VAR_2T(0,:,:)
    printVarSummary(dst_2t)

;---Set up regridding options
    Opt                   = True

;---"bilinear" is the default. "patch" and "conserve" are other options.
    Opt@InterpMethod      = "bilinear"        ;;---Change (maybe)

    Opt@WgtFileName       = "WRF_to_ERA5.nc"

    Opt@SrcGridLat        = src_lat           ; source grid
    Opt@SrcGridLon        = src_lon
    Opt@SrcRegional       = True              ;;--Change (maybe)
    Opt@SrcInputFileName  = WRFfile           ; optional, but good idea

    Opt@DstGridLat        = dst_lat           ; destination grid
    Opt@DstGridLon        = dst_lon
    Opt@DstRegional       = True              ;;--Change (maybe)
;    Opt@DstMask2D = where(.not.ismissing(dst_lat).and.\
;                          .not.ismissing(dst_lon),1,0) ; Necessary if lat/lon
;                                                       ; has missing values.
    Opt@ForceOverwrite    = True
    Opt@PrintTimings      = True
    Opt@Debug             = True

    var_regrid = ESMF_regrid(var,Opt)     ; Do the regridding

    printVarSummary(var_regrid)

;---Compute difference between ERA5 variable and WRF variable
    var_diff = dst_2t - var_regrid


;----------------------------------------------------------------------
; Plotting section
;
; This section creates filled contour plots of both the original
; data and the regridded data, and panels them.
;----------------------------------------------------------------------
    var@lat2d = src_lat     ; Needed for plotting. "var_regrid" 
    var@lon2d = src_lon     ; already has these attrs attached.

    wks = gsn_open_wks("x11","WRF_to_curv")

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

;;--Set contour spacing interval 		Change (maybe)
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
