import numpy as np
import quaternion
import quaternion.quaternion_time_series as qt

# inverse a quaternion matrix - achieved by dividing the conjugate by the magnitude
# if form w + xi + yj + zk conjugate = w - xi - yj - zk
# magnitude would equal w^2 + x^2 + y^2 + z^2
# function takes an array of quaternions and returns the inverse of those arrays
def getInv(QuatArr):
    invArr = []
    for Row in QuatArr:
        Xval = Row[0]
        Yval = Row[1]
        Zval = Row[2]
        Wval = Row[3]
    
        magQuat = Xval**2 + Yval**2 + Zval**2 + Wval**2

        modX = -Xval/magQuat
        modY = -Yval/magQuat
        modZ = -Zval/magQuat
        modW = Wval/magQuat

        tempArr = [modX, modY, modZ, modW]
        invArr.append(tempArr)

    return invArr


# calculate the delta method by Booker by multiplying (product value) the hand sensor quaternions
#       by the inverse quaternion value of the wrist sensor
#     S2S1w = S2w * S1w - S2x * S1x - S2y * S1y - S2z * S1z
#     S2S1x = S2w * S1x + S2x * S1w + S2y * S1z - S2z * S1y
#     S2S1y = S2w * S1y - S2x * S1z + S2y * S1w + S2z * S1x
#     S2S1z = S2w * S1z + S2x * S1y - S2y * S1x + S2z * S1w
def calcDelta(Arr1, Arr2):
    count = 0
    deltaList = []
    while count < len(Arr1):
        W1 = Arr1[count][0]
        X1 = Arr1[count][1]
        Y1 = Arr1[count][2]
        Z1 = Arr1[count][3]

        W2 = Arr2[count][0]
        X2 = Arr2[count][1]
        Y2 = Arr2[count][2]
        Z2 = Arr2[count][3]

        modW = W2 * W1 - X2 * X1 - Y2 * Y1 - Z2 * Z1
        modX = W2 * X1 + X2 * W1 + Y2 * Z1 - Z2 * Y1
        modY = W2 * Y1 - X2 * Z1 + Y2 * W1 + Z2 * X1
        modZ = W2 * Z1 + X2 * Y1 - Y2 * X1 + Z2 * W1
        # tempArr = [modW, modX, modY, modZ]
        deltaList.append(np.quaternion(modX, modY, modZ, modW)) # convert to numpy-quaternion to use with calculate velocity
        count = count + 1
    return deltaList


# Author: Michael Boyle
# Copyright (c) 2017
# https://www.programcreek.com/python/?code=moble%2Fquaternion%2Fquaternion-master%2Fquaternion_time_series.py#
def angular_velocity(R, t):
    from scipy.interpolate import InterpolatedUnivariateSpline as spline
    R = quaternion.as_float_array(R)
    Rdot = np.empty_like(R)
    for i in range(4):
        Rdot[:, i] = spline(t, R[:, i]).derivative()(t)
    R = quaternion.from_float_array(R)
    Rdot = quaternion.from_float_array(Rdot)
    return quaternion.as_float_array(2 * Rdot / R)[:, 1:]