using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class UIController : MonoBehaviour
{
    public Button startButton;
    public Button stopButton;  // Add this line
    public Button exportButton;  // Add this line
    public RectTransform gauge;
    public RectTransform window;
    public RectTransform playerIndicator;
    public TMP_Text angleText;
    public Slider difficultySlider;

    private void Start()
    {
        if (startButton == null || stopButton == null || exportButton == null ||
            gauge == null || window == null || playerIndicator == null ||
            angleText == null || difficultySlider == null)
        {
            Debug.LogError("Some UI elements are not assigned in the UIController!");
        }
    }

    public void SetStartButtonActive(bool active)
    {
        if (startButton != null)
        {
            startButton.gameObject.SetActive(active);
        }
    }

    // Add these two new methods
    public void SetStopButtonActive(bool active)
    {
        if (stopButton != null)
        {
            stopButton.gameObject.SetActive(active);
        }
    }

    public void SetExportButtonActive(bool active)
    {
        if (exportButton != null)
        {
            exportButton.gameObject.SetActive(active);
        }
    }

    public void UpdateWindowPosition(float normalizedPosition)
    {
        if (window != null && gauge != null)
        {
            float gaugeHeight = gauge.rect.height;
            float windowHeight = window.rect.height;
            float maxY = (gaugeHeight - windowHeight) / 2;
            float minY = -maxY;
            float yPosition = Mathf.Lerp(minY, maxY, normalizedPosition);
            window.anchoredPosition = new Vector2(0, yPosition);
            Debug.Log($"Updated window position: {window.anchoredPosition}");
        }
    }

    public void UpdatePlayerPosition(float normalizedPosition)
    {
        if (playerIndicator != null && gauge != null)
        {
            Vector2 position = playerIndicator.anchoredPosition;
            position.y = normalizedPosition * gauge.rect.height - gauge.rect.height / 2;
            playerIndicator.anchoredPosition = position;
        }
    }

    public void UpdateAngleText(float angle)
    {
        if (angleText != null)
        {
            angleText.text = $"{angle:F1}°";
        }
    }
}