import time
import json
import zmq
import numpy as np
from pynput import keyboard
import movelladot_pc_sdk
from xdpchandler import XdpcHandler

# Global variables
waitForConnections = True
is_streaming = False
last_sensor_data = {"sensors": []}

def on_press(key):
    global waitForConnections
    waitForConnections = False

class SensorManager:
    def __init__(self):
        self.xdpcHandler = XdpcHandler()
        self.connected_dots = []

    def initialize_and_sync(self):
        if not self.xdpcHandler.initialize():
            print("Failed to initialise XdpcHandler.")
            return False

        print("Scanning for devices...")
        self.xdpcHandler.scanForDots()
        if len(self.xdpcHandler.detectedDots()) < 2:
            print("Less than two Movella DOT devices found. Aborting.")
            return False

        print("Connecting to DOTs...")
        self.xdpcHandler.connectDots()
        self.connected_dots = self.xdpcHandler.connectedDots()
        if len(self.connected_dots) < 2:
            print("Could not connect to at least two Movella DOT devices. Aborting.")
            return False

        print("Synchronising DOTs...")
        manager = self.xdpcHandler.manager()
        if not manager.startSync(self.connected_dots[-1].bluetoothAddress()):
            print(f"Could not start sync. Reason: {manager.lastResultText()}")
            return False

        print("Synchronisation successful.")
        return True

    def configure_dots(self, output_rate=60):
        for device in self.connected_dots:
            print(f"Configuring device {device.portInfo().bluetoothAddress()}")
            
            if device.setOnboardFilterProfile("General"):
                print("Successfully set profile to General")
            else:
                print("Failed to set filter profile!")

            if device.setOutputRate(output_rate):
                print(f"Successfully set output rate to {output_rate} Hz")
            else:
                print("Failed to set output rate!")

            device.setLogOptions(movelladot_pc_sdk.XsLogOptions_Quaternion)

    def start_measurement(self):
        for device in self.connected_dots:
            if not device.startMeasurement(movelladot_pc_sdk.XsPayloadMode_ExtendedQuaternion):
                print(f"Could not put device into measurement mode. Reason: {device.lastResultText()}")
                return False
        return True

    def restart_measurement(self):
        self.stop_measurement()
        time.sleep(1)  # Wait a second before restarting
        return self.start_measurement()

    def stop_measurement(self):
        for device in self.connected_dots:
            if not device.stopMeasurement():
                print(f"Could not stop measurement on device. Reason: {device.lastResultText()}")

    def cleanup(self):
        self.xdpcHandler.cleanup()

    def get_sensor_data(self):
        data = {"sensors": [], "time": time.time()}
        for i, device in enumerate(self.connected_dots):
            if self.xdpcHandler.packetsAvailable():
                packet = self.xdpcHandler.getNextPacket(device.portInfo().bluetoothAddress())
                if packet.containsOrientation():
                    quat = packet.orientationQuaternion()
                    sensor_data = {
                        "id": f"sensor{i+1}",  # Explicitly assign sensor1 and sensor2
                        "quaternion": {
                            "w": float(quat[0]),
                            "x": float(quat[1]),
                            "y": float(quat[2]),
                            "z": float(quat[3])
                        }
                    }
                    data["sensors"].append(sensor_data)
        return data

def main():
    global is_streaming, last_sensor_data
    
    # Setup ZeroMQ Socket (PUSH)
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect('tcp://localhost:5555')

    sensor_manager = SensorManager()

    if not sensor_manager.initialize_and_sync():
        sensor_manager.cleanup()
        return

    sensor_manager.configure_dots()

    print("Starting measurement...")
    if sensor_manager.start_measurement():
        is_streaming = True
        print("Measurement started. Streaming data to Unity...")
    else:
        print("Failed to start measurement. Exiting...")
        sensor_manager.cleanup()
        return

    try:
        while True:
            if is_streaming:
                data = sensor_manager.get_sensor_data()
                if data["sensors"]:
                    last_sensor_data = data
                    print(f"Sensor Data: {data}")
                    json_data = json.dumps(data)
                    socket.send_string(json_data)
                elif last_sensor_data["sensors"]:
                    print("No new data, sending last known data")
                    json_data = json.dumps(last_sensor_data)
                    socket.send_string(json_data)
                else:
                    print("No sensor data available")
            else:
                print("Streaming is not active")

            time.sleep(0.01)  # Small delay to prevent busy-waiting

    except KeyboardInterrupt:
        print("\nInterrupt received, stopping measurements...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nStopping measurement...")
        sensor_manager.stop_measurement()
        sensor_manager.cleanup()
        print("Successful exit.")

if __name__ == "__main__":
    main()