using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ServerReceiver;
using System;
using Newtonsoft.Json;
using System.Net.Sockets;
using System.Text;
using System.Collections.Generic;
using System.Collections;

public class SquatGameController : MonoBehaviour
{
    //UI Components
    public TextMeshProUGUI angleText;
    public TextMeshProUGUI countdownText;
    public Button calibrateButton;
    public Button restartButton;
    public Button startButton;
    public Button stopButton;
    public Button exportButton;

    public Slider difficultySlider;
    public TextMeshProUGUI difficultyText;
    public TextMeshProUGUI calibrationText;
    public TextMeshProUGUI sparcText;
    public TextMeshProUGUI ldljText;
    public TextMeshProUGUI timerText;
    public TextMeshProUGUI pointsText;
    public TextMeshProUGUI gradeText;

    public RectTransform playerIndicator;
    public RectTransform gauge;
    public RectTransform windowTransform;
    public Image pointsProgressBar;
    public GameObject pointsPopupPrefab;
    public Canvas gameCanvas;

    // Game Settings & State
    private float difficulty = 0.5f;
    private float windowMovementSpeed = 0.2f;
    private bool isGameRunning = false;
    private float gameTimer = 0f;
    private const float GAME_DURATION = 30f;
    private int totalPoints = 0;
    private const int MAX_POINTS = 6000;
    private string currentGrade = "";

    // Sensor & Movement Variables
    private Server server;
    private float minKneeAngle = 60f;
    private float maxKneeAngle = 170f;
    private Quaternion calibratedThighRotation;
    private Quaternion calibratedShinRotation;
    private string thighSensorId;
    private string shinSensorId;
    private bool isCalibrated = false;

    // Assessment Variables
    private float assessmentTimer = 0f;
    private const float ASSESSMENT_INTERVAL = 3f;
    private const int POINTS_PER_ASSESSMENT = 600;

    // Smoothness Analysis
    private TcpClient smoothnessClient;
    private NetworkStream smoothnessStream;
    private List<QuaternionData> dataPoints = new List<QuaternionData>();
    private float lastTimestamp = 0f;
    private CSVExporter csvExporter;

    // Unity Lifecycle Methods
    private void Start()
    {
        server = new Server();
        server.Start();
        Debug.Log("SquatGameController started");

        calibrateButton.onClick.AddListener(StartCalibration);
        calibrationText.text = "Please calibrate";
        difficultySlider.onValueChanged.AddListener((_) => UpdateDifficulty());

        restartButton.onClick.AddListener(RestartGame);
        restartButton.gameObject.SetActive(false);

        ConnectToSmoothnessServer();

        csvExporter = gameObject.AddComponent<CSVExporter>();
        exportButton.onClick.AddListener(ExportData);
        SetupButtons();
        InitializeUI();
    }

    private void Update()
    {
        UpdateTimerDisplay();
        UpdateDifficulty();
        MoveWindow();

        string sensor1Data = server.GetSensor1();
        string sensor2Data = server.GetSensor2();

        if (!string.IsNullOrEmpty(sensor1Data) && !string.IsNullOrEmpty(sensor2Data))
        {
            if (isCalibrated)
            {
                float kneeAngle = CalculateKneeAngle(sensor1Data, sensor2Data);
                UpdateUI(kneeAngle);

                var thighSensor = JsonConvert.DeserializeObject<SensorData>(sensor1Data);
                var shinSensor = JsonConvert.DeserializeObject<SensorData>(sensor2Data);

                Quaternion thighQuaternion = new Quaternion(
                    thighSensor.quaternion.x,
                    thighSensor.quaternion.y,
                    thighSensor.quaternion.z,
                    thighSensor.quaternion.w
                );

                Quaternion shinQuaternion = new Quaternion(
                    shinSensor.quaternion.x,
                    shinSensor.quaternion.y,
                    shinSensor.quaternion.z,
                    shinSensor.quaternion.w
                );

                AddDataPoint(thighQuaternion, Time.time);

                if (dataPoints.Count >= 300)
                {
                    CalculateSmoothness();
                    dataPoints.Clear();
                }

                float sparc = float.Parse(sparcText.text.Split(':')[1].Trim());
                float ldlj = float.Parse(ldljText.text.Split(':')[1].Trim());
                csvExporter.AddRow(Time.time, thighQuaternion, shinQuaternion, sparc, ldlj, kneeAngle);
            }
        }
        else
        {
            Debug.LogWarning("Missing or invalid sensor data received!");
        }

        if (isGameRunning)
        {
            assessmentTimer += Time.deltaTime;
            if (assessmentTimer >= ASSESSMENT_INTERVAL)
            {
                AssessPerformance();
                assessmentTimer = 0f;
            }
        }
    }

    private void OnDestroy()
    {
        server?.Stop();
        smoothnessClient?.Close();
    }

    // Calibration Methods
    private void StartCalibration()
    {
        StartCoroutine(CalibrationProcess());
    }

    private System.Collections.IEnumerator CalibrationProcess()
    {
        calibrationText.text = "Stand straight and face the PC";
        calibrateButton.interactable = false;
        yield return new WaitForSeconds(3);

        calibrationText.text = "Calibrating...";
        yield return new WaitForSeconds(2);

        string sensor1Data = server.GetSensor1();
        string sensor2Data = server.GetSensor2();

        if (!string.IsNullOrEmpty(sensor1Data) && !string.IsNullOrEmpty(sensor2Data))
        {
            var sensor1 = JsonConvert.DeserializeObject<SensorData>(sensor1Data);
            var sensor2 = JsonConvert.DeserializeObject<SensorData>(sensor2Data);

            thighSensorId = sensor1.id;
            shinSensorId = sensor2.id;

            calibratedThighRotation = new Quaternion(
                sensor1.quaternion.x,
                sensor1.quaternion.y,
                sensor1.quaternion.z,
                sensor1.quaternion.w
            );

            calibratedShinRotation = new Quaternion(
                sensor2.quaternion.x,
                sensor2.quaternion.y,
                sensor2.quaternion.z,
                sensor2.quaternion.w
            );

            isCalibrated = true;
            calibrationText.text = "Calibration complete";
            startButton.interactable = true;
        }
        else
        {
            calibrationText.text = "Calibration failed. Please try again.";
            calibrateButton.interactable = true;
        }
    }

    // Angle Calculation
    private float CalculateKneeAngle(string sensor1Data, string sensor2Data)
    {
        try
        {
            var sensor1 = JsonConvert.DeserializeObject<SensorData>(sensor1Data);
            var sensor2 = JsonConvert.DeserializeObject<SensorData>(sensor2Data);

            Quaternion thighRotation = (sensor1.id == thighSensorId) ?
                new Quaternion(sensor1.quaternion.x, sensor1.quaternion.y, sensor1.quaternion.z, sensor1.quaternion.w) :
                new Quaternion(sensor2.quaternion.x, sensor2.quaternion.y, sensor2.quaternion.z, sensor2.quaternion.w);

            Quaternion shinRotation = (sensor1.id == shinSensorId) ?
                new Quaternion(sensor1.quaternion.x, sensor1.quaternion.y, sensor1.quaternion.z, sensor1.quaternion.w) :
                new Quaternion(sensor2.quaternion.x, sensor2.quaternion.y, sensor2.quaternion.z, sensor2.quaternion.w);

            Quaternion relativeThighRotation = Quaternion.Inverse(calibratedThighRotation) * thighRotation;
            Quaternion relativeShinRotation = Quaternion.Inverse(calibratedShinRotation) * shinRotation;

            Quaternion relativeKneeRotation = Quaternion.Inverse(relativeThighRotation) * relativeShinRotation;
            float angle = Quaternion.Angle(Quaternion.identity, relativeKneeRotation);

            float kneeAngle = 180f - angle;
            kneeAngle = Mathf.Clamp(kneeAngle, 0f, 180f);

            Debug.Log($"Calculated knee angle: {kneeAngle}");
            return kneeAngle;
        }
        catch (Exception e)
        {
            Debug.LogError($"Error calculating knee angle: {e.Message}");
            return 180f;
        }
    }

    // UI Update Methods
    private void UpdateUI(float kneeAngle)
    {
        angleText.text = $"{kneeAngle:F1}°";

        if (playerIndicator != null && gauge != null)
        {
            float normalizedPosition = Mathf.InverseLerp(minKneeAngle, maxKneeAngle, kneeAngle);
            float gaugeHeight = gauge.rect.height;
            float yPosition = normalizedPosition * gaugeHeight - gaugeHeight / 2;
            playerIndicator.anchoredPosition = new Vector2(playerIndicator.anchoredPosition.x, yPosition);
        }
    }

    private void UpdateTimerDisplay()
    {
        if (isGameRunning)
        {
            gameTimer += Time.deltaTime;
            float timeRemaining = Mathf.Max(0, GAME_DURATION - gameTimer);

            int minutes = Mathf.FloorToInt(timeRemaining / 60);
            int seconds = Mathf.FloorToInt(timeRemaining % 60);

            timerText.text = string.Format("{0:00}:{1:00}", minutes, seconds);

            if (timeRemaining <= 0)
            {
                Debug.Log("Game ending...");
                EndGame();
            }
        }
    }

    private void UpdateDifficulty()
    {
        difficulty = difficultySlider.value;
        difficultyText.text = $"Difficulty: {difficulty:F2}";

        float minSize = 20f;
        float maxSize = 100f;
        float windowSize = Mathf.Lerp(maxSize, minSize, difficulty);
        windowTransform.sizeDelta = new Vector2(windowTransform.sizeDelta.x, windowSize);
    }

    private void UpdatePointsDisplay()
    {
        pointsText.text = totalPoints.ToString();
        pointsProgressBar.fillAmount = (float)totalPoints / MAX_POINTS;
        Debug.Log($"Updated points display: {totalPoints}");
    }

    // Game Control Methods
    private void SetupButtons()
    {
        startButton.onClick.AddListener(StartGame);
        stopButton.onClick.AddListener(StopGame);

        calibrateButton.interactable = true;
        startButton.interactable = false;
        stopButton.interactable = false;
        exportButton.interactable = false;
    }

    private void InitializeUI()
    {
        countdownText.gameObject.SetActive(false);
        timerText.gameObject.SetActive(false);
    }

    private void StartGame()
    {
        if (isCalibrated)
        {
            StartCoroutine(StartGameCountdown());
        }
        else
        {
            Debug.LogWarning("Please calibrate before starting the game.");
        }
    }

    private System.Collections.IEnumerator StartGameCountdown()
    {
        countdownText.gameObject.SetActive(true);
        for (int i = 3; i > 0; i--)
        {
            countdownText.text = i.ToString();
            yield return new WaitForSeconds(1);
        }
        countdownText.text = "GO!";
        yield return new WaitForSeconds(1);
        countdownText.gameObject.SetActive(false);

        isGameRunning = true;
        gameTimer = 0f;
        assessmentTimer = 0f;
        totalPoints = 0;
        UpdatePointsDisplay();
        timerText.gameObject.SetActive(true);
        startButton.interactable = false;
        stopButton.interactable = true;
    }

    private void StopGame()
    {
        isGameRunning = false;
        timerText.gameObject.SetActive(false);
        stopButton.interactable = false;
        exportButton.interactable = true;
        EndGame();
    }

    private void RestartGame()
    {
        gameTimer = 0f;
        totalPoints = 0;
        isGameRunning = false;
        isCalibrated = false;

        calibrationText.text = "Please calibrate";
        gradeText.text = "Grade: ";
        timerText.text = "00:30";
        pointsText.text = "0";

        calibrateButton.interactable = true;
        startButton.interactable = false;
        stopButton.interactable = false;
        exportButton.interactable = false;
        restartButton.gameObject.SetActive(false);

        pointsProgressBar.fillAmount = 0f;

        Debug.Log("Game restarted");
    }

    // Game Mechanics
    private void MoveWindow()
    {
        if (isGameRunning)
        {
            float time = Time.time * windowMovementSpeed;
            float t = (Mathf.Sin(time * Mathf.PI * 2) + 1) / 2;

            float targetAngle = Mathf.Lerp(minKneeAngle, maxKneeAngle, t);
            float normalizedPosition = (targetAngle - minKneeAngle) / (maxKneeAngle - minKneeAngle);

            float gaugeHeight = gauge.rect.height;
            float windowHeight = windowTransform.rect.height;
            float maxY = gaugeHeight / 2 - windowHeight / 2;
            float minY = -maxY;

            float yPosition = Mathf.Lerp(minY, maxY, normalizedPosition);
            windowTransform.anchoredPosition = new Vector2(windowTransform.anchoredPosition.x, yPosition);
        }
    }

    private void AssessPerformance()
    {
        Debug.Log("Assessing performance...");
        float percentageInWindow = CalculatePercentageInWindow();
        int pointsEarned = Mathf.RoundToInt(POINTS_PER_ASSESSMENT * percentageInWindow);
        totalPoints += pointsEarned;
        UpdatePointsDisplay();
        ShowPointsPopup(pointsEarned);
        Debug.Log($"Points earned: {pointsEarned}, Total points: {totalPoints}");
    }

    private float CalculatePercentageInWindow()
    {
        if (windowTransform == null || playerIndicator == null)
        {
            Debug.LogError("Window transform or player indicator is null!");
            return 0f;
        }

        float windowTop = windowTransform.anchoredPosition.y + windowTransform.rect.height / 2;
        float windowBottom = windowTransform.anchoredPosition.y - windowTransform.rect.height / 2;
        float playerY = playerIndicator.anchoredPosition.y;

        Debug.Log($"Window: {windowBottom} to {windowTop}, Player: {playerY}");

        if (playerY >= windowBottom && playerY <= windowTop)
        {
            return 1f; // Fully within the window
        }
        else
        {
            float distanceOutside = Mathf.Min(Mathf.Abs(playerY - windowTop), Mathf.Abs(playerY - windowBottom));
            float percentageInside = 1f - (distanceOutside / (windowTransform.rect.height / 2));
            float result = Mathf.Clamp01(percentageInside);
            Debug.Log($"Percentage in window: {result}");
            return result;
        }
    }

    // Points and Scoring
    private void ShowPointsPopup(int points)
    {
        if (pointsPopupPrefab == null || gameCanvas == null)
        {
            Debug.LogError("Points popup prefab or game canvas is not assigned!");
            return;
        }

        GameObject popup = Instantiate(pointsPopupPrefab, gameCanvas.transform);
        RectTransform rectTransform = popup.GetComponent<RectTransform>();
        rectTransform.anchoredPosition = playerIndicator.anchoredPosition + new Vector2(0, 50);

        TextMeshProUGUI popupText = popup.GetComponent<TextMeshProUGUI>();
        if (popupText != null)
        {
            popupText.text = $"+{points}";
            StartCoroutine(FadeOutPopup(popup));
        }
        else
        {
            Debug.LogError("TextMeshProUGUI component not found on points popup prefab!");
        }
    }

    private IEnumerator FadeOutPopup(GameObject popup)
    {
        TextMeshProUGUI popupText = popup.GetComponent<TextMeshProUGUI>();
        float duration = 1f;
        float elapsedTime = 0f;

        while (elapsedTime < duration)
        {
            elapsedTime += Time.deltaTime;
            float alpha = Mathf.Lerp(1f, 0f, elapsedTime / duration);
            popupText.color = new Color(popupText.color.r, popupText.color.g, popupText.color.b, alpha);
            popup.transform.position += Vector3.up * Time.deltaTime * 50f;
            yield return null;
        }

        Destroy(popup);
    }

    private string CalculateGrade()
    {
        float percentage = (float)totalPoints / MAX_POINTS;
        if (percentage >= 0.9f) return "A";
        else if (percentage >= 0.8f) return "B";
        else if (percentage >= 0.7f) return "C";
        else if (percentage >= 0.6f) return "D";
        else return "F";
    }

    private void DisplayFinalResults()
    {
        gradeText.text = $"Grade: {currentGrade}";
    }

    // Data Export and Smoothness Analysis
    private void ExportData()
    {
        csvExporter.ExportCSV();
    }

    private void ConnectToSmoothnessServer()
    {
        try
        {
            smoothnessClient = new TcpClient("localhost", 5556);
            smoothnessStream = smoothnessClient.GetStream();
            Debug.Log("Connected to smoothness server");
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to connect to smoothness server: {e.Message}");
        }
    }

    private void AddDataPoint(Quaternion quaternion, float timestamp)
    {
        dataPoints.Add(new QuaternionData
        {
            w = quaternion.w,
            x = quaternion.x,
            y = quaternion.y,
            z = quaternion.z,
            timestamp = timestamp - lastTimestamp
        });
        lastTimestamp = timestamp;
    }

    private void CalculateSmoothness()
    {
        try
        {
            var data = new
            {
                quaternions = dataPoints,
                deltaTime = Time.deltaTime,
                time = Time.time
            };

            string jsonData = JsonConvert.SerializeObject(data);
            byte[] sendData = Encoding.ASCII.GetBytes(jsonData);

            smoothnessStream.Write(sendData, 0, sendData.Length);

            byte[] receiveData = new byte[1024];
            int bytesRead = smoothnessStream.Read(receiveData, 0, receiveData.Length);
            string jsonResponse = Encoding.ASCII.GetString(receiveData, 0, bytesRead);

            var response = JsonConvert.DeserializeObject<SmoothnessResponse>(jsonResponse);

            UpdateSmoothnessVisualFeedback(response.sparc, response.ldlj);
        }
        catch (Exception e)
        {
            Debug.LogError($"Error calculating smoothness: {e.Message}");
        }
    }

    private void UpdateSmoothnessVisualFeedback(float sparc, float ldlj)
    {
        sparcText.text = $"SPARC: {sparc:F2}";
        ldljText.text = $"LDLJ: {ldlj:F2}";
        Debug.Log($"SPARC: {sparc}, LDLJ: {ldlj}");
    }

    // Game End
    private void EndGame()
    {
        isGameRunning = false;
        currentGrade = CalculateGrade();
        restartButton.gameObject.SetActive(true);
        DisplayFinalResults();
        Debug.Log($"Game ended. Final score: {totalPoints}, Grade: {currentGrade}");
    }
}

// Data Classes
[System.Serializable]
public class SensorData
{
    public string id;
    public QuaternionData quaternion;
}

[System.Serializable]
public class QuaternionData
{
    public float w, x, y, z, timestamp;
}

[System.Serializable]
public class SmoothnessResponse
{
    public float sparc, ldlj;
}
