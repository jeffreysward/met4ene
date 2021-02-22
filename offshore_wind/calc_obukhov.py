import random
import math
import numpy as np


def sat_vapor_pressure(T, T0=273.16, a1=611.21, a3=17.502, a4=32.19):
    """

    :param T: Temperature in K
    :param T0: Reference temperature set to 273.16 K (0.01 degrees C) by default
    :param a1: first Tetens formula parameter
    :param a3: third Tetens formula parameter
    :param a4: fourth Tetens formula parameter
    :return:
    """
    e_sat = a1*math.exp(a3*((T - T0)/(T - a4)))
    return e_sat


def sat_specific_humidity(T, p, epsilon=0.622):
    q_sat = epsilon*sat_vapor_pressure(T)/(p - (1 - epsilon)*sat_vapor_pressure(T))
    return q_sat


def slope_sat_specific_humidity(T, dT, p):
    # Find the two temperatures for the sat_vapor pressure calculation
    T1 = T - dT/2
    T2 = T + dT/2
    # Estimate the local slope of the saturation specific humidity curve
    dq_sat_dT = (sat_specific_humidity(T2, p) - sat_specific_humidity(T1, p))/dT
    return dq_sat_dT


def bowen_ratio(T, p, dT=0.1, c_p=1.006*10**3, lam=2.4535*10**6, alpha=1.28):
    B = (1 + (c_p/lam)/slope_sat_specific_humidity(T, dT, p))/alpha - 1
    return B


def clac_obukhov_iter(U, z, Tair, Tsea, L_initial, z0_initial, tolerance=0.05):
    # Define the constants
    g = 9.81            # acceleration due to gravity
    k = 0.4             # von Karman constant
    L = [L_initial]     # initial L (Obukhov length) value
    z0 = [z0_initial]   # initial z0 (wind speed roughness length) value
    ii = 1              # index varible
    pctdiff = 1         # initial percent difference
    while pctdiff > tolerance:
        # With an estmate for L, estimate ust and thetast
        # First, choose a form of psi_m based on the estimate for L
        if L[ii] >= 0:
            psi_m = -5*(z/L[ii])
        else:
            x = (1 - 16*(z/L[ii]))**(1/4)
            psi_m = 2*np.log((1 + x)/2) + np.log((1 + x**2)/2) - 2*np.arctan(x) + np.pi/2


        U = (ust/k) * np.log(z/z0[ii]) - psi_m(z/L[ii])
        # Using these values, recompute L
        Lnew = random.uniform(0, 1)
        print(f'L for this iteration is: {Lnew}')
        L.append(Lnew)
        # Calculate the percent difference in L from the past two iterations
        try:
            pctdiff = abs(L[ii] - L[ii - 1])/L[ii - 1]
        except ZeroDivisionError:
            pctdiff = abs(L[ii] - 10**{-10}) / 10**{-10}
        print(f'The percent difference is: {round(100*pctdiff, 1)}%')
        # Add one to the index variable
        ii += 1


if __name__ == "__main__":
    L_initial = 0.01
    z0_initial = 5*10**(-5)
    T_in_K = 298   # Temperature in K (25 degrees C)
    pres = 101325  # Atm pressure in Pa

    esat = sat_vapor_pressure(T_in_K)
    print(f'The saturation vapor pressure at {T_in_K} K is {esat}')

    qsat = sat_specific_humidity(T_in_K, pres)
    print(f'The saturation specific humidity at {T_in_K} K, {pres} Pa is {qsat}')
    print(f'The correct value should be ~ 0.02 for 25 degrees C.')

    dqsat_dT1 = slope_sat_specific_humidity(T_in_K, 0.1, pres)
    dqsat_dT2 = slope_sat_specific_humidity(T_in_K, 1, pres)
    dqsat_dT3 = slope_sat_specific_humidity(T_in_K, 10, pres)
    print(f'The slope of the saturation specif humidity curve is:\n'
          f'{dqsat_dT1} for dT=0.1 K,\n'
          f'{dqsat_dT2} for dT=1 K,\n'
          f'{dqsat_dT3} for dT=10 K,')

    Br = bowen_ratio(T_in_K, pres)
    print(f'The bowen ratio is: {Br}')

    # clac_obukhov_iter(L_initial, z0_initial, tolerance=0.05)
