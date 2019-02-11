#!/bin/tcsh

# Write contents of nam1-0.template to namelist.input 
# (overwrites any existing namelist.input)
cat nam1-0.template > namelist.input

cat << -eof- >> namelist.input
start_hour                          = 12,   12,   12,
start_minute                        = 00,   00,   00,
start_second                        = 00,   00,   00,
end_hour                            = 24,   24,   24,
end_minute                          = 00,   00,   00,
end_second                          = 00,   00,   00,
-eof-

# Append contents of nam2-0.template to namelist.input
cat nam2-0.template >> namelist.input
