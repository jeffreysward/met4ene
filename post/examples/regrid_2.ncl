load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/esmf/ESMF_regridding.ncl"

begin
    sfile = addfile("sst.nc","r")
    temp  = sfile->TEMP(0,0,:,:)

    Opt                = True

    Opt@SrcFileName    = "src_SCRIP.nc"
    Opt@DstFileName    = "dst_SCRIP.nc"
    Opt@WgtFileName    = "NCEP_2_Rect.nc"
    Opt@ForceOverwrite = True

    Opt@SrcGridMask    = where(.not.ismissing(temp),1,0)   ; use SrcMask2D in NCL V6.2.1 and earlier

    Opt@DstGridType    = "5x5"
    Opt@DstLLCorner    = (/ -60.d,   0.d/)
    Opt@DstURCorner    = (/  60.d, 355.d/)

    temp_regrid = ESMF_regrid(temp,Opt)
    printVarSummary(temp_regrid)
end
