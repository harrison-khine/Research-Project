import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal

def sensorData(inputFileLoc):
    sensorData = pd.read_csv(inputFileLoc, skiprows=10)

    QuatW = sensorData["Quat_W"].to_numpy() #Quaternion values
    QuatX = sensorData["Quat_X"].to_numpy()
    QuatY = sensorData["Quat_Y"].to_numpy()
    QuatZ = sensorData["Quat_Z"].to_numpy()
    quatArr = np.stack((QuatX, QuatY, QuatZ, QuatW), axis=1)

    XPos = sensorData["Acc_X"].to_numpy() #acceleration in m/s^2
    YPos = sensorData["Acc_Y"].to_numpy()
    ZPos = sensorData["Acc_Z"].to_numpy()
    accArr = np.stack((XPos, YPos, ZPos), axis=1)

    AngX = sensorData["Gyr_X"].to_numpy() #Angular in deg/s
    AngY = sensorData["Gyr_Y"].to_numpy()
    AngZ = sensorData["Gyr_Z"].to_numpy()    
    angArr = np.stack((AngX, AngY, AngZ), axis=1)

    TimeArr = sensorData["SampleTimeFine"].to_numpy()

    return [quatArr, accArr, angArr, TimeArr]



def dataLoc(inputFileLoc):
    tempString = inputFileLoc
    tempString  = tempString.split("/")[:-1]
    tempString = "/".join(tempString)
    return tempString

def visualise2D(dataIn, inputFileLoc, dataName, fs=60, threshold=0.05, order = 10, padlen = 10, fc = 10, prom=0.4):
    
    fc_norm = fc / (threshold * fs)

    data_padded = np.pad(dataIn, (padlen, padlen), mode='edge')

    # Apply a low-pass filter to the data
    b, a = signal.butter(order, fc_norm, 'low', fs = fs)
    data_filt = signal.filtfilt(b, a, data_padded, method="gust")
    # data_filt = signal.filtfilt(b, a, data_padded)

    # Find peaks in the data
    peaks, _ = signal.find_peaks(data_filt, height=threshold, prominence = prom)
    peaks, _ = signal.find_peaks(data_filt, height=threshold)
    # print('number of peaks: ', len(peaks))
    # print(peaks)
    # print()

    calcValleys = (np.diff(np.sign(np.diff(data_filt))) > 0).nonzero()[0] + 1
    calcPeaks = (np.diff(np.sign(np.diff(data_filt))) < 0).nonzero()[0] + 1
    # print("peaks and valleys")
    # print(len(calcPeaks))
    # print(calcPeaks,)
    # print(len(calcValleys))
    # print(calcValleys, '\n')
    xAxis = np.linspace(0, len(data_filt), num = len(data_filt))

    fileLoc = dataLoc(inputFileLoc)
    imageName = fileLoc + '/' + dataName + '.png'

    plt.plot(data_padded, 'k-', label='padded')
    plt.plot(data_filt, 'b-', linewidth=4, label='filtered')
    plt.plot(xAxis[calcValleys], data_filt[calcValleys], "o", label="min", color='g')
    plt.plot(xAxis[calcPeaks], data_filt[calcPeaks], "o", label="max", color='r')
    plt.legend(loc='best')
    plt.savefig(imageName, bbox_inches='tight')
    plt.clf()

    return len(peaks)