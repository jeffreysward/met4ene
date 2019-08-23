load "./ncar_wrf2era.ncl"

begin
    MAE = wrf2era(2011,1,16)
    t2_MAE = MAE[0]
    u10_MAE = MAE[1]
    v10_MAE = MAE[2]
    u100_MAE = MAE[3]
    v100_MAE = MAE[4]
    print(t2_MAE)
    print(u10_MAE)
    print(v10_MAE)
    print(u100_MAE)
    print(v100_MAE)
end
