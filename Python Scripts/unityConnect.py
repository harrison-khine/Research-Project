#####################################################
# Eve Cooper 19780207
# Project 1 - MXEN40001
# Calculating the Ranges for movement Smoothness
####################################################

import socket
import json

import numpy as np
import pandas as pd
import math
import quaternion
import struct  # Import struct module to pack and unpack data


####################################################################################################################

# FUNCTIONS

# https://www.programcreek.com/python/example/125385/numpy.quaternion   Ex 17
def angular_velocity(R, t):
    from scipy.interpolate import InterpolatedUnivariateSpline as spline
    R = quaternion.as_float_array(R)
    # create array of same size as R
    Rdot = np.empty_like(R)
    for i in range(4):  # as .as_float_array, extracts the quarternion to 4 individual numbers
        # create spline (connect all points to create a function, then take the derivative with respect to time
        # ==> velocity (Rdot)
        Rdot[:, i] = spline(t, R[:, i]).derivative()(t)
    R = quaternion.from_float_array(R)  # ber ack to quarternion array
    Rdot = quaternion.from_float_array(Rdot)  # back to quarternion array
    return quaternion.as_float_array(2 * Rdot / R)[:, 1:]  # (2 * ds/dt) / s

def angular_velocity2(R, t):
    # this method was used to validate the angular velocity method
    # as this method was from the quaternion.quaternion_time_series
    # this is the qt.angular_velocity(R,t) function that has been used
    # i have left it here so that we know what is going on in the function
    from scipy.interpolate import CubicSpline

    R = quaternion.as_float_array(R)
    Rdot = CubicSpline(t, R).derivative()(t)
    R = quaternion.from_float_array(R)
    Rdot = quaternion.from_float_array(Rdot)
    return quaternion.as_float_array(2 * Rdot / R)[:, 1:]


def spectral_arclength(movement, fs, padlevel=4, fc=10.0, amp_th=0.05):
    """
    Calcualtes the smoothness of the given speed profile using the modified spectral
    arc length metric.
    Parameters
    ----------
    movement : np.array
               The array containing the movement speed profile.
    fs       : float
               The sampling frequency of the data.
    padlevel : integer, optional
               Indicates the amount of zero padding to be done to the movement
               data for estimating the spectral arc length. [default = 4]
    fc       : float, optional
               The max. cut off frequency for calculating the spectral arc
               length metric. [default = 10.]
    amp_th   : float, optional
               The amplitude threshold to used for determing the cut off
               frequency upto which the spectral arc length is to be estimated.
               [default = 0.05]
    Returns
    -------
    sal      : float
               The spectral arc length estimate of the given movement's
               smoothness.
    (f, Mf)  : tuple of two np.arrays
               This is the frequency(f) and the magntiude spectrum(Mf) of the
               given movement data. This spectral is from 0. to fs/2.
    (f_sel, Mf_sel) : tuple of two np.arrays
                      This is the portion of the spectrum that is selected for
                      calculating the spectral arc length.
    Notes
    -----
    This is the modfieid spectral arc length metric, which has been tested only
    for discrete movements.
    It is suitable for movements that are a few seconds long, but for long
    movements it might be slow and results might not make sense (like any other
    smoothness metric).
    Examples
    --------
    >>> t = np.arange(-1, 1, 0.01)
    >>> move = np.exp(-5*pow(t, 2))
    >>> sal, _, _ = spectral_arclength(move, fs=100.)
    >>> '%.5f' % sal
    '-1.41403'
    """
    # Number of zeros to be padded.
    nfft = int(pow(2, np.ceil(np.log2(len(movement))) + padlevel))

    # Frequency
    f = np.arange(0, fs, fs / nfft)
    # Normalized magnitude spectrum
    Mf = abs(np.fft.fft(movement, nfft))
    Mf = Mf / max(Mf)

    # Indices to choose only the spectrum within the given cut off frequency Fc.
    # NOTE: This is a low pass filtering operation to get rid of high frequency
    # noise from affecting the next step (amplitude threshold based cut off for
    # arc length calculation).
    fc_inx = ((f <= fc) * 1).nonzero()
    f_sel = f[fc_inx]
    Mf_sel = Mf[fc_inx]

    # Choose the amplitude threshold based cut off frequency.
    # Index of the last point on the magnitude spectrum that is greater than
    # or equal to the amplitude threshold.
    inx = ((Mf_sel >= amp_th) * 1).nonzero()[0]
    fc_inx = range(inx[0], inx[-1] + 1)
    f_sel = f_sel[fc_inx]
    Mf_sel = Mf_sel[fc_inx]

    # Calculate arc length
    new_sal = -sum(np.sqrt(pow(np.diff(f_sel) / (f_sel[-1] - f_sel[0]), 2) +
                           pow(np.diff(Mf_sel), 2)))
    return new_sal, (f, Mf), (f_sel, Mf_sel)

def dimensionless_jerk(movement, fs):
    """
    Calculates the smoothness metric for the given speed profile using the dimensionless jerk
    metric.

    Parameters
    ----------
    movement : np.array
               The array containing the movement speed profile.
    fs       : float
               The sampling frequency of the data.
    Returns
    -------
    dl       : float
               The dimensionless jerk estimate of the given movement's smoothness.
    Notes
    -----

    Examples
    --------
    >>> t = np.arange(-1, 1, 0.01)
    >>> move = np.exp(-5*pow(t, 2))
    >>> dl = dimensionless_jerk(move, fs=100.)
    >>> '%.5f' % dl
    '-335.74684'
    """
    # first enforce data into an numpy array.
    movement = np.array(movement)

    # calculate the scale factor and jerk.
    movement_peak = max(abs(movement))
    dt = 1. / fs
    movement_dur = len(movement) * dt
    jerk = np.diff(movement, 2) / pow(dt, 2)
    scale = pow(movement_dur, 3) / pow(movement_peak, 2)

    # estimate dj
    return - scale * sum(pow(jerk, 2)) * dt


def log_dimensionless_jerk(movement, fs):
    """
    Calculates the smoothness metric for the given speed profile using the log dimensionless jerk
    metric.

    Parameters
    ----------
    movement : np.array
               The array containing the movement speed profile.
    fs       : float
               The sampling frequency of the data.
    Returns
    -------
    ldl      : float
               The log dimensionless jerk estimate of the given movement's smoothness.
    Notes
    -----

    Examples
    --------
    >>> t = np.arange(-1, 1, 0.01)
    >>> move = np.exp(-5*pow(t, 2))
    >>> ldl = log_dimensionless_jerk(move, fs=100.)
    >>> '%.5f' % ldl
    '-5.81636'
    """
    return -np.log(abs(dimensionless_jerk(movement, fs)))


# Function to receive data with a variable size
def receive_data_with_length(socket_conn):
    # Receive the length of the incoming data (as a 4-byte integer)
    data_length_bytes = socket_conn.recv(4)
    if not data_length_bytes:
        return None  # No data received, return None

    # Unpack the length as an unsigned 32-bit integer
    data_length = struct.unpack("!I", data_length_bytes)[0]

    # Receive the actual data
    received_data = b''
    while len(received_data) < data_length:
        chunk = socket_conn.recv(min(1024, data_length - len(received_data)))
        if not chunk:
            return None  # No more data to receive
        received_data += chunk

    return received_data


####################################################################################################################

HOST = 'localhost'  # Localhost
PORT = 5556       # Choose a port number

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Server listening on {HOST}:{PORT}")

    connection, address = server_socket.accept()
    with connection:
        print(f"Connected by {address}")

        while True:
            data = connection.recv(60000)
            print("data receiving...")
            if not data:
                break

            try:
                received_data_str = data.decode("utf-8")
                the_data = json.loads(received_data_str)

                print("Received data:", the_data)  # Print the received data

                quaternions = the_data['quaternions']
                deltaTime = the_data['deltaTime']
                total_time = the_data['time']

                print('received data')

                WQuat = []
                XQuat = []
                YQuat = []
                ZQuat = []
                timestamps = []

                for quaternion_entry in quaternions:
                    WQuat.append(quaternion_entry["w"])
                    XQuat.append(quaternion_entry["x"])
                    YQuat.append(quaternion_entry["y"])
                    ZQuat.append(quaternion_entry["z"])
                    timestamps.append(quaternion_entry["timestamp"])

                WQuat = np.array(WQuat)
                XQuat = np.array(XQuat)
                YQuat = np.array(YQuat)
                ZQuat = np.array(ZQuat)
                timestamps = np.array(timestamps)

                Quat_Array = []
                for w, x, y, z in zip(WQuat, XQuat, YQuat, ZQuat):
                    Quat_Array.append(np.quaternion(w, x, y, z))

                Quat_Array = np.array(Quat_Array)

                # Use the timestamps from the quaternion data
                time_array = np.cumsum(timestamps)

                AngularVelocity2D = angular_velocity2(Quat_Array, time_array)  # produces 2d array
                # [[xVel,yVel,zVel],[xVel,yVel,zVel],[xVel,yVel,zVel]...]  Assuming it is angular velocity in x,y,z planes

                AngularVelocityX = []
                AngularVelocityY = []
                AngularVelocityZ = []
                for Vel in AngularVelocity2D:  # Split into 3 Arrays of x,y,z
                    # Vel = [xVel,yVel,zVel]
                    AngularVelocityX.append(Vel[0])
                    AngularVelocityY.append(Vel[1])
                    AngularVelocityZ.append(Vel[2])

                AngularVelocity = []
                for x, y, z in zip(AngularVelocityX, AngularVelocityY, AngularVelocityZ):
                    dx = math.pow(x, 2)
                    dy = math.pow(y, 2)
                    dz = math.pow(z, 2)
                    AngularVelocity.append(math.sqrt(dx + dy + dz))  # square root of velocities

                # CALCULATE SMOOTHNESS MEASURES

                sparc_Angular, _, _ = spectral_arclength(AngularVelocity, fs=9, padlevel=4, fc=10.0, amp_th=0.05)
                ldlj_Angular = log_dimensionless_jerk(AngularVelocity, fs=9)

                print("SPARC: ")
                print(sparc_Angular)
                print("LDLJ: ")
                print(ldlj_Angular)

                # Send a response (if needed)
                # Create a response dictionary with the data you want to send back
                response_data = {
                    "message": "Data received successfully",
                    "SPARC": sparc_Angular,  # Add your additional data here
                    "LDLJ": ldlj_Angular
                }

                connection.sendall(json.dumps(response_data).encode("utf-8"))
                print("Data Sent")
            except json.decoder.JSONDecodeError as e:
                # Handle the case where the received data is not valid JSON
                print("Error decoding JSON:", e)
            except Exception as e:
                print(f"An error occurred: {e}")
                # You may choose to close the connection or take other appropriate action

            # Close the server socket (outside the loop)
connection.close()

    #        # Process the received data (deserialize if it's JSON)
    #        received_data = json.loads(data.decode())
    #        # Perform some actions with received_data
    #        print(received_data)

    #        # Send a response (if needed)
    #        response_data = {"message": "Data received successfully"}
    #        connection.sendall(json.dumps(response_data).encode())