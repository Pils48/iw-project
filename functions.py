import numpy as np
import matplotlib


# Функции для элемента DRIFT-0.8
#
# Вам нужны функции:
# I_static, U_I, U_static Tcrit

# сопротивление элемента Пельтье
R = 1.674

# напряжение на источнике, на котором мы работаем
Usource = 5

# максимум температуры как для Tc, так и для Th
Tmax = 273.15+120


def Qc0(I, Th):
    return -19.87484 - 0.8696*I**2 - 0.00015243*Th**2 + 0.081474*I*Th + 0.378*I + 0.111153*Th


def QdT_ang(I, Th):
    return 0.7912773222 + 0.0024136606*I**2 - 7.0777e-06*Th**2 + 2.1352e-05*I*Th + 0.0558703568*I + 0.0048359032*Th

# ток, который нужен для поддержания мощности охлаждения Q на dT = 0
# def I_static_0(Q, Th):
#     return 1.14995e-6*(189000. + 40737.*Th -
#     np.sqrt(-1.72474e13 - 8.696e11*Q + 1.12057e11*Th +
#     1.52695e9*Th**2))


def I_static(Q, Th, Tc):
    a = -0.8696 - 0.0024136606*(Th - Tc)
    b =  0.081474*Th + 0.378 - 2.1352*10**-5*Th*(Th - Tc) - 0.0558703568*(Th - Tc)
    c = -19.87484 - 0.00015243*Th**2 + 0.111153*Th - (0.7912773222 - 7.0777*1e-6*Th**2 + 0.0048359032*Th)*(Th - Tc) - Q
    D = b**2 - 4*a*c
    return (-b + np.sqrt(D))/2/a


def U_static(Q, Th, Tc):
    return U_I(I_static(Q, Th, Tc), Th, Tc)


def Wp_static(Q, Th, Tc):
    return U_static(Q, Th, Tc)*I_static(Q, Th, Tc)


def Tcrit(I, Th):
    return -1.785531 - 1.0139*I**2 + 2.4353e-5*Th**2 + 0.039053*I*Th + 3.66113*I - 0.0021225*Th


def U_I(I, Th, Tc):
    return -4.75656 - 8.25859e-5*(Th-Tc)**2 - 4.41036e-5*Th**2 + 2.00587e-5*(Th-Tc)*Th + 0.078608948*(Th-Tc) + 0.029240229*Th + I*R


def I_U(U, Th, Tc):
    return -(-4.75656 - 8.25859e-5*(Th-Tc)**2 - 4.41036e-5*Th**2 + 2.00587e-5*(Th-Tc)*Th + 0.078608948*(Th-Tc) + 0.029240229*Th)/R + U/R


def coolingPower(I, Th, Tc):
    return Qc0(I, Th) - (Th - Tc)*QdT_ang(I, Th)