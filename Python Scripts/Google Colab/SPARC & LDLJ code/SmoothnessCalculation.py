import numpy as np
import csv
import math
from scipy import integrate as it
from smoothness import *
from SmoothnessCalculationHelper import *
from SmoothnessCalculationDataManager import *

# fileLoc1 refers to the csv file location of the sensor that would be placed on the wrist
# fileLoc2 refers to the csv file location of the sensor that would be placed on the hand
# typically file paths will be seperated with a backslash "\", these need to be replaced
#    with forward slashes "/" as seen by my own calls below

# Up one movement check
fileLoc1 = "C:/Users/james/Dropbox/Engineering/thesis/Project 2/Data/Up1/Sensor_1.csv"
fileLoc2 = "C:/Users/james/Dropbox/Engineering/thesis/Project 2/Data/Up1/Sensor_2.csv"

# Processing Sensor 1 data - return is an array containing:
#     [[quat data], [acc data], [gyro data], [time arr]]
sensor1data = sensorData(fileLoc1)

QuatArr1 = sensor1data[0]
# my sample files had garbage at the start of the recording that i trimmed
#   to get nicer data
QuatArr1 = QuatArr1[30:]

# Processing Sensor 2 data - return is an array containing:
#     [[quat data], [acc data], [gyro data], [time arr]]
sensor2data = sensorData(fileLoc2)
# seperate return data for manipulation
QuatArr2 = sensor2data[0] # Quaternion values
QuatArr2 = QuatArr2[30:]
AccArr2 = sensor2data[1] # acceleration in m/s^2
AccArr2 = AccArr2[30:]
AngArr2 = sensor2data[2] # velocity in degrees/s
AngArr2 = AngArr2[30:]

# sometimes one sensor will send more packets that the other,
#    but need the same amount of data. If the difference is positive
#    then sensor 2 has more data subtract the difference from the
#    end of array, if negative shrink sensor 1 data.
#    If 0 store time Arr.
diffArrLen = len(QuatArr2) - len(QuatArr1)
if diffArrLen == 0:
    TimeArr = sensor1data[3][30:]
elif diffArrLen > 0:
    QuatArr2 = QuatArr2[:-diffArrLen]
    AccArr2 = AccArr2[:-diffArrLen]
    AngArr2 = AngArr2[:-diffArrLen]
    TimeArr = sensor2data[3][30:-diffArrLen]
else:
    QuatArr1 = QuatArr1[:diffArrLen]
    TimeArr = sensor1data[3][30:diffArrLen]

# Get inverse of QuatArr to do the "Booker Method"
#     - dont need other sensor 1 data at the moment
InvQuatArr1 = getInv(QuatArr1)

# generate delta array
QuatDeltaList = calcDelta(InvQuatArr1, QuatArr2)

# Some of the modules need gravity data, assumed to be -9.81 z
grav = np.array([[0, 0, -9.81]]).T

#convert packet to seconds elapsed
SetToZero = TimeArr[0]
TimeArr = (TimeArr-SetToZero)/pow(10,6) 

fs = 60 # 60Hz sampling time, interval of 0.016667s

# NOTE the following call the module written by Sivakumar Balasubramanian
#      for his work on measuring movement smoothness

# raw IMU calculation - takes acceleration array, gyro array, grav array and sampling rate
LDLJ_IMU = log_dimensionless_jerk_imu(AccArr2, AngArr2, grav, fs) #takes IMU data and outputs LDLJ using acceleration
# print('IMU LDLJ: ', LDLJ_IMU, '\n')

# convert quaternion array into 2D accel array [ [x1,y1,z1], [x2,y2,z2], ...]
quatAngularVelocityArr = qt.angular_velocity(QuatDeltaList,TimeArr)

# convert 2D accel array to keep magnitude for sparc
quatAngularMagnitudeArr = []
for element in quatAngularVelocityArr:
    xComp = element[0]
    yComp = element[1]
    zComp = element[2]
    quatAngularMagnitudeArr.append(math.sqrt(math.pow(xComp, 2) 
                + math.pow(yComp, 2) + math.pow(zComp, 2)))

# outputs using the Booker Quaternion method
#     as currently stored in the output file
qamSAL = sparc(quatAngularMagnitudeArr, fs) # SAL only computes 1D array, need to use magnitude
# print('quaternion angular magnitude SAL: ', qamSAL)
qamDLJ = dimensionless_jerk(quatAngularVelocityArr, fs, rem_mean=True)
# print('quaternion angular magnitude DLJ: ', qamDLJ)
qamLDLJ = log_dimensionless_jerk(quatAngularVelocityArr, fs)
# print('quaternion angular magnitude LDLJ: ', qamLDLJ, '\n')


# create acceleration magnitude array
sensor2AccelMag = []
for element in AccArr2:
    xComp = element[0]
    yComp = element[1]
    zComp = element[2]
    sensor2AccelMag.append(math.sqrt(math.pow(xComp, 2) 
                + math.pow(yComp, 2) + math.pow(zComp, 2)))
# outputs using acceleration data
accSAL = sparc(sensor2AccelMag, fs)
# print('Sensor 2 acceleration SAL: ', accSAL)
accDLJ = dimensionless_jerk(AccArr2, fs, data_type='accl') # has option to take acceleration as input
# print('Sensor 2 acceleration DLJ: ', accDLJ)
accLDLJ = log_dimensionless_jerk(AccArr2, fs, data_type='accl')
# print('Sensor 2 acceleration LDLJ: ', accLDLJ, '\n')


# create array looking at the x axis acceleration
# seperate data into seperate axis
sensor2XAccel = []
sensor2YAccel = []
sensor2ZAccel = []
for element in AccArr2:
    sensor2XAccel.append(element[0])
    sensor2YAccel.append(element[1])
    sensor2ZAccel.append(element[2])

# SAL of x-axis
sensor2XSAL = sparc(sensor2XAccel, fs)
sensor2YSAL = sparc(sensor2YAccel, fs)
sensor2ZSAL = sparc(sensor2ZAccel, fs)
# print('Sensor 2 X acceleration SAL: ', sensor2XSAL, '\n')
# print('Sensor 2 Y acceleration SAL: ', sensor2YSAL, '\n')
# print('Sensor 2 Z acceleration SAL: ', sensor2ZSAL, '\n')


# convert acceleration into velocity
xVelSensor2 = it.cumtrapz(sensor2XAccel, TimeArr, initial=0)
yVelSensor2 = it.cumtrapz(sensor2YAccel, TimeArr, initial=0)
zVelSensor2 = it.cumtrapz(sensor2ZAccel, TimeArr, initial=0)
velArrSensor2 = np.stack((sensor2XAccel, sensor2YAccel, sensor2ZAccel), axis=1)
# get velocity magnitude for SAL
sensor2VelMag = []
for element in velArrSensor2:
    xComp = element[0]
    yComp = element[1]
    zComp = element[2]
    sensor2VelMag.append(math.sqrt(math.pow(xComp, 2) 
                + math.pow(yComp, 2) + math.pow(zComp, 2)))
# outputs using velocity data
velSAL = sparc(sensor2VelMag, fs)
# print('Sensor 2 velocity SAL: ', velSAL)
velDLJ = dimensionless_jerk(velArrSensor2, fs)
# print('Sensor 2 velocity DLJ: ', velDLJ)
velLDLJ = log_dimensionless_jerk(velArrSensor2, fs)
# print('Sensor 2 velocity LDLJ: ', velLDLJ, '\n')


sensor2GyroMag = []
for element in AngArr2:
    xComp = element[0]
    yComp = element[1]
    zComp = element[2]
    sensor2GyroMag.append(math.sqrt(math.pow(xComp, 2) 
                + math.pow(yComp, 2) + math.pow(zComp, 2)))

angSAL = sparc(sensor2GyroMag, fs)
# print('Sensor 2 angular SAL: ', angSAL)
angDLJ = dimensionless_jerk(AngArr2, fs, rem_mean=True)
# print('Sensor 2 angular DLJ: ', angDLJ)
angLDLJ = log_dimensionless_jerk(AngArr2, fs)
# print('Sensor 2 angular LDLJ: ', angLDLJ, '\n')

csvSaveLoc = dataLoc(fileLoc1)

with open((csvSaveLoc + '/smoothnessCalcs.csv'), 'w', newline='') as writeOut:
    csvHeader = [ '', 'SPARC', 'DLJ', 'LDLJ']
    writer = csv.writer(writeOut)
    writer.writerow(['IMU LDLJ', LDLJ_IMU])
    writer.writerow(csvHeader)
    writer.writerow(['Quaternion output', qamSAL, qamDLJ, qamLDLJ])
    writer.writerow(['Acceleration output', accSAL, accDLJ, accLDLJ])
    writer.writerow(['X plane acceleration', sensor2XSAL])
    writer.writerow(['Y plane acceleration', sensor2YSAL])
    writer.writerow(['Z plane acceleration', sensor2ZSAL])
    writer.writerow(['Velocity output', velSAL, velDLJ, velLDLJ])
    writer.writerow(['Angular output', angSAL, angDLJ, angLDLJ])

# print("filtering")

with open((csvSaveLoc + '/peakCountFil.csv'), 'w', newline='') as writeOut:
    writer = csv.writer(writeOut)

    writer.writerow(['time elapsed:', TimeArr[len(TimeArr)-1]])

    peakVal = visualise2D(quatAngularMagnitudeArr, fileLoc2, 'Angular Velocity Magnitude filter')
    writer.writerow(['Angular Velocity Magnitude filter peaks:', peakVal])

    peakVal = visualise2D(sensor2AccelMag, fileLoc2, 'Acceleration Magnitude filter')
    writer.writerow(['Acceleration Magnitude filter peaks:', peakVal])

    peakVal = visualise2D(sensor2XAccel, fileLoc2, 'X Acceleration filter')
    writer.writerow(['X Acceleration filter peaks:', peakVal])

    peakVal = visualise2D(sensor2YAccel, fileLoc2, 'Y Acceleration filter')
    writer.writerow(['Y Acceleration filter peaks:', peakVal])

    peakVal = visualise2D(sensor2ZAccel, fileLoc2, 'Z Acceleration filter')
    writer.writerow(['Z Acceleration filter peaks:', peakVal])

    peakVal = visualise2D(sensor2VelMag, fileLoc2, 'Velocity Magnitude filter')
    writer.writerow(['Velocity Magnitude filter peaks:', peakVal])

    peakVal = visualise2D(sensor2GyroMag, fileLoc2, 'Gyro Magnitude filter')
    writer.writerow(['Gyro Magnitude filter peaks:', peakVal])

# print("agressive filtering")

with open((csvSaveLoc + '/peakCountAgg.csv'), 'w', newline='') as writeOut:
    writer = csv.writer(writeOut)

    writer.writerow(['time elapsed:', TimeArr[len(TimeArr)-1]])

    peakVal = visualise2D(quatAngularMagnitudeArr, fileLoc2, 'Angular Velocity Magnitude agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['Angular Velocity Magnitude agressive filter peaks:', peakVal])

    peakVal = visualise2D(sensor2AccelMag, fileLoc2, 'Acceleration Magnitude agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['Acceleration Magnitude agressive filter peaks:', peakVal])

    peakVal = visualise2D(sensor2XAccel, fileLoc2, 'X Acceleration agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['X Acceleration agressive filter peaks:', peakVal])

    peakVal = visualise2D(sensor2YAccel, fileLoc2, 'Y Acceleration agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['Y Acceleration agressive filter peaks:', peakVal])

    peakVal = visualise2D(sensor2ZAccel, fileLoc2, 'Z Acceleration agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['Z Acceleration agressive filter peaks:', peakVal])

    peakVal = visualise2D(sensor2VelMag, fileLoc2, 'Velocity Magnitude agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['Velocity Magnitude agressive filter peaks:', peakVal])

    peakVal = visualise2D(sensor2GyroMag, fileLoc2, 'Gyro Magnitude agressive filter', threshold=0.2, order = 4, padlen = 4)
    writer.writerow(['Gyro Magnitude agressive filter peaks:', peakVal])

    