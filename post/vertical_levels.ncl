;-------------------------------------------------------------------------------------------------------
; vertical_levels.ncl
;-------------------------------------------------------------------------------------------------------
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
;-------------------------------------------------------------------------------------------------------
begin
 WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/wrfrun_z36r1bl5cu300ls2/"
; WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_A5Dx3D/2011jan23-24/err.wrfrun_z46r1bl5cu300ls2/"
 WRFfile = "wrfout_d03_2011-01-24_01:00:00"
; WRFfile = "wrfinput_d03"

 if (fileexists(WRFdir+WRFfile)) then
         f = addfile(WRFdir+WRFfile, "r")
 else
         print("")
         print("The WRF file "+WRFdir+WRFfile+" does not exist. Check your path.")
         print("")
	 exit
 end if

;-------------------------------------------------------------------------------------------------------
 Z = wrf_user_getvar(f,"height", -1)    ;Model Height (m)
 Zter = wrf_user_getvar(f,"ter" , -1)   ;Terrain Height (m)
 dsizes_x = dimsizes(Z)
 ntim     = dsizes_x(0)
 klev     = dsizes_x(1)
 nlat     = dsizes_x(2)
 mlon     = dsizes_x(3)
 Zcat = Z(:,0:klev-1,:,:)

 do kk = 0, klev-1
    Zcat(:,kk,:,:) = Zcat(:,kk,:,:) - Zter
 end do
print(Zcat(0,:,10,10))
print(Zcat(0,:,20,20))
print(Zcat(0,:,30,30))
print(Zcat(0,:,40,40))
;--------------------------------------------------------------------------------------------------------

end
