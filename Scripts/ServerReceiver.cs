using System;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using UnityEngine;

namespace ServerReceiver
{
    public class ServerReceiver
    {
        private readonly Thread receiveThread;
        private bool running;
        public ServerReceiver()
        {
            // Create New Thread for Bluetooth Sensor Transmission over TCP Socket
            receiveThread = new Thread((object callback) =>
            {
                // Create new Server Socket connected to port 5555 (The Bluetooth Side is the Client)
                using (var socket = new PullSocket("@tcp://*:5555"))
                {
                    while (running)
                    {
                        // Receive the JSON and pass it back to the calling function
                        string data = socket.ReceiveFrameString();
                        ((Action<string>)callback)(data);
                    }
                }
            });
        }

        // Call this function when starting Sensor Transmission
        public void Start(Action<string> callback)
        {
            running = true;
            receiveThread.Start(callback);
        }

        // Call this function when stopping Sensor Transmission (also kills the thread)
        public void Stop()
        {
            running = false;
            receiveThread.Abort(); // Harrison Booker: Personal Communication, suggestion instead of receiveThread.Join();
        }
    }

    // This is the class that you interact with for the Bluetooth Transmission
    public class Server
    {
        private ServerReceiver receiver;
        private string sensor1;
        private string sensor2;

        public Server()
        {
            SetSensor1("{\"quaternion\":{\"w\":0,\"x\":0,\"y\":0,\"z\":0}}");
            SetSensor2("{\"quaternion\":{\"w\":0,\"x\":0,\"y\":0,\"z\":0}}");
        }

        public void Start()
        {
            AsyncIO.ForceDotNet.Force();
            receiver = new ServerReceiver();
            receiver.Start((string d) =>
            {
                Debug.Log($"Received data: {d}");
                try
                {
                    var data = JsonUtility.FromJson<SensorData>(d);
                    if (data.sensors.Length > 0)
                    {
                        SetSensor1(JsonUtility.ToJson(data.sensors[0]));
                        if (data.sensors.Length > 1)
                        {
                            SetSensor2(JsonUtility.ToJson(data.sensors[1]));
                        }
                    }
                }
                catch (Exception e)
                {
                    Debug.LogError($"Error parsing sensor data: {e.Message}");
                }
            });
        }

        public void Stop()
        {
            receiver?.Stop();
            NetMQConfig.Cleanup();
        }

        ~Server()
        {
            Stop();
        }

        private void SetSensor1(string inSensor1)
        {
            sensor1 = inSensor1;
        }

        private void SetSensor2(string inSensor2)
        {
            sensor2 = inSensor2;
        }

        public string GetSensor1()
        {
            return sensor1;
        }

        public string GetSensor2()
        {
            return sensor2;
        }
    }

    [System.Serializable]
    public class SensorData
    {
        public Sensor[] sensors;
    }

    [System.Serializable]
    public class Sensor
    {
        public string id;
        public QuaternionData quaternion;
        public EulerData euler;
    }

    [System.Serializable]
    public class QuaternionData
    {
        public float w, x, y, z;
    }

    [System.Serializable]
    public class EulerData
    {
        public float roll, pitch, yaw;
    }
}