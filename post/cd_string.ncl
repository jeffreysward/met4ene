undef("cd_string")

function cd_string( time[*]:numeric, inFormat:string )
;******************************************************************************
; Purpose: Convert a time into a string
;
; Arguments:
; time: The variable containing the values of time. This variable should
; have an attribute named "units". 
;
; inFormat: (OPTIONAL) a string specifying the format of the tick labels.
; This string is parsed as follows: the '%' acts as
; the escape character. The single character after every
; '%' is formatted according to the rule:
; Y => 4-digit year (e.g., 2007).
; y => 2-digit year (e.g., 07).
; C => CAPITAL month abbreviation (e.g., JUN).
; c => Small month abbreviation (e.g., Jun).
; F => CAPITAL full month (e.g., JUNE).
; f => Small full month (e.g., June).
; N => 2-digit month (e.g., 06).
; n => 1 or 2 digit month (e.g., 6 for June, 12 for December).
; D => 2-digit day (e.g., 04).
; d => 1 or 2 digit day (e.g., 4)
; J => 3-digit day-of-year (e.g., 091)
; j => 1, 2, or 3 digit day-of-year (e.g., 4, 91, or 181)
; H => 2-digit hour (e.g., 09).
; h => 1 or 2 digit hour (e.g., 9 or 11).
; M => 2 digit minute (e.g., 08).
; m => 1 or 2 digit minute (e.g., 07 or 56).
; S => 2 digit second (e.g., 02).
; s => 1 or 2 digit second (e.g., 2 or 23).
;
;   New Added by abrammer
; t=> 1 digit day with superscript suffix.  (e.g.(w/o supers) 7th, 1st, 2nd ) returns 7~S~th~N~
; a=> Weekday 3 letter abbrev.
; A=> Weekday full name
;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;
; Any character at any other place in the format string
; is drawn as is.
; NOTE: a '%' can be drawn using "%%".
; In case Format is absent, a minimal algorithm exists
; which tries to determine the format string depending
; on the length and values of the date-time.
;
; If inFormat is "", it will default to "%H%M UTC %d %c %Y"
; e.g., 1800 UTC 4 Jul 1776
;
; Return value:
;  a string represent the time(s) in the specified format
;
; Exmple 1:
;  timeDouble = cd_inv_calendar( 1776, 07, 04, 18, 00, 00,  "hours since 1800-01-01 00:00", 0 )
;  print( (/ cd_string( timeDouble, "" ) /) )
;  print( (/ cd_string( timeDouble, "%Y-%N-%D %H:%M:%S" ) /) )
;
;  The above will output:
; (0)     1800 UTC 4 Jul 1776
; (0)     1776-07-04 18:00:00
;
;******************************************************************************

local chFormat,doy,fmonths,i,inside,j,monAvg,monNum,month,months,nt,num_lat,num_lev,num_lon,num_months,num_points,num_time,retVal,stFormat,x_dims,x_rank,ymdhms0,ymdhms1i

begin

  if( inFormat.eq."" ) then
    stFormat = "%H%M UTC %d %c %Y"
  else
    stFormat = inFormat
  end if

  months = (/"","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"/)
  fmonths = (/"","January","February","March","April","May","June","July","August","September","October","November","December"/)
  wdy = (/"Sun","Mon","Tue","Wed","Thu","Fri","Sat"/)
  weekday = (/"Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"/) 

  ; check input
  if (.not. isatt(time,"units")) then
    print("cd_string: The variable containing time values must have a 'units' attribute.")
    return
  end if

  ymdhms0 = cd_calendar(time,0)
  nt = dimsizes(time)

  if (typeof(ymdhms0) .eq. "float") then
    ymdhms1i = floattointeger(ymdhms0)
  else
    ymdhms1i = ymdhms0
  end if

  retVal = new(nt,"string")

  chFormat = stringtochar(stFormat)

  do i = 0, dimsizes(time)-1
    retVal(i) = ""
    inside = False
    if( .not.ismissing(time(i)) ) then
      doy = day_of_year( ymdhms1i(i,0), ymdhms1i(i,1), ymdhms1i(i,2) )
    else
      doy = default_fillvalue("integer")
    end if
    j = 0
    do while(j .lt. dimsizes(chFormat))
      if (chFormat(j) .eq. "%") then
        inside = True
        j = j + 1
      end if

      if (.not. inside) then
        retVal(i) = retVal(i)+chFormat(j)
      else
        if (chFormat(j) .eq. "Y") then
          retVal(i) = retVal(i)+sprinti("%04d",ymdhms1i(i,0))
          inside = False
        end if
        if (chFormat(j) .eq. "y") then
          retVal(i) = retVal(i)+sprinti("%02d",ymdhms1i(i,0)%100)
          inside = False
        end if
        if (chFormat(j) .eq. "C") then
          if( .not.ismissing(time(i)) ) then
            retVal(i) = retVal(i)+str_upper(months(ymdhms1i(i,1)))
          else
            retVal(i) = retVal(i)+default_fillvalue("integer")
          end if
          inside = False
        end if
        if (chFormat(j) .eq. "c") then
          if( .not.ismissing(time(i)) ) then
            retVal(i) = retVal(i)+months(ymdhms1i(i,1))
          else
            retVal(i) = retVal(i)+default_fillvalue("integer")
          end if
          inside = False
        end if
        if (chFormat(j) .eq. "F") then
          if( .not.ismissing(time(i)) ) then
            retVal(i) = retVal(i)+str_upper(fmonths(ymdhms1i(i,1)))
          else
            retVal(i) = retVal(i)+default_fillvalue("integer")
          end if
          inside = False
        end if
        if (chFormat(j) .eq. "f") then
          if( .not.ismissing(time(i)) ) then
            retVal(i) = retVal(i)+fmonths(ymdhms1i(i,1))
          else
            retVal(i) = retVal(i)+default_fillvalue("integer")
          end if
          inside = False
        end if
        if (chFormat(j) .eq. "N") then
          retVal(i) = retVal(i)+sprinti("%02d",ymdhms1i(i,1))
          inside = False
        end if
        if (chFormat(j) .eq. "n") then
          retVal(i) = retVal(i)+sprinti("%d",ymdhms1i(i,1))
          inside = False
        end if
        if (chFormat(j) .eq. "D") then
          retVal(i) = retVal(i)+sprinti("%02d",ymdhms1i(i,2))
          inside = False
        end if
        if (chFormat(j) .eq. "d") then
          retVal(i) = retVal(i)+sprinti("%d",ymdhms1i(i,2))
          inside = False
        end if
        if (chFormat(j) .eq. "J") then
          retVal(i) = retVal(i)+sprinti("%03d",doy)
          inside = False
        end if
        if (chFormat(j) .eq. "j") then
          retVal(i) = retVal(i)+sprinti("%d",doy)
          inside = False
        end if
        if (chFormat(j) .eq."a") then
            if(.not.ismissing(time(i)))
              dow = day_of_week( ymdhms1i(i,0), ymdhms1i(i,1), ymdhms1i(i,2) )
              retVal(i) = retVal(i)+wdy(dow)
            end if
            inside = False
        end if
        if (chFormat(j) .eq."A") then
            if(.not.ismissing(time(i)))
              dow = day_of_week( ymdhms1i(i,0), ymdhms1i(i,1), ymdhms1i(i,2) )
              retVal(i) = retVal(i)+weekday(dow)
            end if
            inside = False
        end if
        if (chFormat(j) .eq. "t") then
          suff = "th"
          if(any( (/1,21,31/).eq.ymdhms1i(i,2)))then
             suff = "st"
          end if
          if(any( (/2,22/).eq.ymdhms1i(i,2)))then
              suff = "nd"
          end if
          if( any( (/3,23/).eq.ymdhms1i(i,2)))then
              suff = "rd"
          end if
          retVal(i) = retVal(i)+sprinti("%d",ymdhms1i(i,2))+"~S~"+suff+"~N~"
          inside = False
        end if
        if (chFormat(j) .eq. "H") then
          retVal(i) = retVal(i)+sprinti("%02d",ymdhms1i(i,3))
          inside = False
        end if
        if (chFormat(j) .eq. "h") then
          retVal(i) = retVal(i)+sprinti("%d",ymdhms1i(i,3))
          inside = False
        end if
        if (chFormat(j) .eq. "M") then
          retVal(i) = retVal(i)+sprinti("%02d",ymdhms1i(i,4))
          inside = False
        end if
        if (chFormat(j) .eq. "m") then
          retVal(i) = retVal(i)+sprinti("%d",ymdhms1i(i,4))
          inside = False
        end if
        if (chFormat(j) .eq. "S") then
          retVal(i) = retVal(i)+sprinti("%02d",ymdhms1i(i,5))
          inside = False
        end if
        if (chFormat(j) .eq. "s") then
          retVal(i) = retVal(i)+sprinti("%d",ymdhms1i(i,5))
          inside = False
        end if
        if (chFormat(j) .eq. "%") then
          retVal(i) = retVal(i)+"%"
          inside = False
        end if
      end if

      j = j + 1
    end do

  end do

  return( retVal )
end 
