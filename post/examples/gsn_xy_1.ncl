;*************************************************
; gsn_xy_1.ncl
;*************************************************
;
; This file is loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
;*************************************************
begin
;---data.asc has 6 columns and 500 rows of data.
  data  = asciiread("./data.asc",(/500,6/),"float")
  x     = data(:,1)    ; Read the second column of data (indexing starts at 0)
  y     = data(:,4)    ; Read the fifth column of data
;**************************************************
; create plot
;**************************************************
  wks = gsn_open_wks("png","gsn_xy")         ; send graphics to PNG file
  plot = gsn_xy(wks,x,y,False)               ; Draw an XY plot with 1 curve.
  
end
