using UnityEngine;
using System.IO;
using System.Collections.Generic;
using System.Linq;

public class CSVExporter : MonoBehaviour
{
    private List<string[]> rowData = new List<string[]>();

    public void AddRow(float timestamp, Quaternion sensor1Quat, Quaternion sensor2Quat, float sparc, float ldlj, float kneeAngle)
    {
        string[] row = new string[]
        {
            timestamp.ToString(),
            sensor1Quat.w.ToString(), sensor1Quat.x.ToString(), sensor1Quat.y.ToString(), sensor1Quat.z.ToString(),
            "",  // Empty column for separation
            sensor2Quat.w.ToString(), sensor2Quat.x.ToString(), sensor2Quat.y.ToString(), sensor2Quat.z.ToString(),
            sparc.ToString(), ldlj.ToString(), kneeAngle.ToString()
        };
        rowData.Add(row);
    }

    public void ExportCSV()
    {
        string folderPath = Path.Combine(Application.dataPath, "Results");
        if (!Directory.Exists(folderPath))
        {
            Directory.CreateDirectory(folderPath);
        }

        string filePath = Path.Combine(folderPath, $"sensor_data_{System.DateTime.Now:yyyyMMdd_HHmmss}.csv");

        using (StreamWriter sw = new StreamWriter(filePath))
        {
            sw.WriteLine("Timestamp,Sensor1_Quat_W,Sensor1_Quat_X,Sensor1_Quat_Y,Sensor1_Quat_Z,,Sensor2_Quat_W,Sensor2_Quat_X,Sensor2_Quat_Y,Sensor2_Quat_Z,SPARC,LDLJ,KneeAngle");

            foreach (string[] row in rowData)
            {
                sw.WriteLine(string.Join(",", row));
            }
        }

        Debug.Log($"CSV file exported to: {filePath}");
    }
}