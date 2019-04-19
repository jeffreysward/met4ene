#!/bin/csh
#set verbose

#  set the prefix to the NAMANL filesi
set dir = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/"
#set fileprfx = "namanl_218_201012"
#set fileprfx = "namanl_218_201101"
#set fileprfx = "namanl_218_201102"
#set fileprfx = "namanl_218_201103"
set fileprfx = "namanl_218_201104"
#set fileprfx = "namanl_218_201105"
#set fileprfx = "namanl_218_201106"
#set fileprfx = "namanl_218_201107"
#set fileprfx = "namanl_218_201108"
#set fileprfx = "namanl_218_201109"
#set fileprfx = "namanl_218_201110"
#set fileprfx = "namanl_218_201111"
#set fileprfx = "namanl_218_201112"

#  (Here is a sample name /hp1/npl/wrf/data_ds608/NARR/merged_AWIP32.2008012915.3D )
#set namprfx="/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201012"
#set namprfx = "nam_218_201101"
#set namprfx = "nam_218_201102"
#set namprfx = "nam_218_201103"
set namprfx = "nam_218_201104"
#set namprfx = "nam_218_201105"
#set namprfx = "nam_218_201106"
#set namprfx = "nam_218_201107"
#set namprfx = "nam_218_201108"
#set namprfx = "nam_218_201109"
#set namprfx = "nam_218_201110"
#set namprfx = "nam_218_201111"
#set namprfx = "nam_218_201112"

set fpath = $dir$namprfx"01_0000_000.grb2"
echo $fpath

if ( -f $fpath ) then
	echo These grib 2 files have already been unacrchived.
else
	echo This grib 2 files have NOT been unarchived! 
endif
