
;  This script calculates the wind speed from the u and v 
;  components at a specified height (in meters). A plot is 
;  produced as a rough check.
;  As of now, the script will not work if the WSPD100 
;  variable already exists.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
;
; The WRF ARW input file.  
; This needs to have a ".nc" appended, so just do it.
  WRFdir = "/magma-dirs/jas983/wrf_data/eas5555/wrfwrk/ARW/NYpvow_D5Dx3D/2011sept13-14/wrfrun_z46r1bl5cu300ls2/"
  WRFfile = "wrfout_d03_2011-09-14_01:00:00"
  if (fileexists(WRFdir+WRFfile)) then
  	a = addfile(WRFdir+WRFfile, "w")
  else
        print("")
        print("The WRF file "+WRFdir+WRFfile+" does not exist. Check your path.")
        print("")
        exit
  end if


; We generate plots, but what kind do we prefer?
  type = "x11"
; type = "pdf"
; type = "ps"
; type = "ncgm"
  wks = gsn_open_wks(type,"Wind at 100m")


; Set some basic resources
  res = True
  res@MainTitle = "REAL-TIME WRF"
  res@Footer = False

  pltres = True
  mpres = True
  mpres@mpGeophysicalLineColor = "Black"
  mpres@mpNationalLineColor    = "Black"
  mpres@mpUSStateLineColor     = "Black"
  mpres@mpGridLineColor        = "Black"
  mpres@mpLimbLineColor        = "Black"
  mpres@mpPerimLineColor       = "Black"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; What times and how many time steps are in the data set?
  times = wrf_user_getvar(a,"times",-1)  ; get all times in the file
  ntimes = dimsizes(times)         ; number of times in the file

; The specific height levels that we want the data interpolated to.
  height_levels = (/ 100./)   ; height levels to plot - in meter
  nlevels       = dimsizes(height_levels)     ; number of height levels

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; First get the variables we will need        

    u  = wrf_user_getvar(a,"ua",-1)        ; u averaged to mass points
    v  = wrf_user_getvar(a,"va",-1)        ; v averaged to mass points
    z  = wrf_user_getvar(a, "z",-1)        ; grid point height

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    do level = 0,nlevels-1                 ; LOOP OVER LEVELS

      height = height_levels(level) 

      u_plane  = wrf_user_intrp3d( u,z,"h",height,0.,False)
      v_plane  = wrf_user_intrp3d( v,z,"h",height,0.,False)

      wspd = sqrt(u_plane^2 + v_plane^2)
      wspd@long_name  = "Wind Speed at 100m"
      wspd@short_name = "100wind"
      wspd@units      = "m/s"
      wspd@_FillValue = -999           ; sets _FillValue to -999

      ; Plotting options for Wind Speed                
      opts = res                          
      opts@cnFillOn = True  
      opts@ContourParameters = (/ 1., 9., 1./)
      opts@cnFillColors = (/"White","White","White", \
                            "Chartreuse","Chartreuse","Green",\
                            "Green3","Green4", \
                            "ForestGreen","PaleGreen4"/)
      contour_w = wrf_contour(a,wks,wspd(20,:,:),opts)
      delete(opts)

      ; MAKE PLOTS                                       
      plot = wrf_map_overlays(a,wks,(/contour_w/),pltres,mpres)

      filevardef(a, "WSPD100", "float", (/"Time", "south_north", "west_east"/))
      a->WSPD100 = wspd                      ; write new variable


    end do      ; END OF LEVEL LOOP

end
