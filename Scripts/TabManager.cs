using UnityEngine;
using UnityEngine.UI;

public class SimpleTabManager : MonoBehaviour
{
    [System.Serializable]
    public class TabInfo
    {
        public Button tabButton;
        public GameObject panelToShow;
    }

    public TabInfo[] tabs;
    public GameObject mainMenuPanel;

    void Start()
    {
        // Set up button listeners
        for (int i = 0; i < tabs.Length; i++)
        {
            int index = i; // Capture the index for the lambda expression
            tabs[i].tabButton.onClick.AddListener(() => ShowPanel(index));
        }

        // Show the main menu panel by default
        ShowMainMenu();
    }

    void ShowPanel(int index)
    {
        // Hide all panels including main menu
        mainMenuPanel.SetActive(false);
        for (int i = 0; i < tabs.Length; i++)
        {
            tabs[i].panelToShow.SetActive(false);
        }

        // Show the selected panel
        tabs[index].panelToShow.SetActive(true);
    }

    public void ShowMainMenu()
    {
        // Hide all panels
        for (int i = 0; i < tabs.Length; i++)
        {
            tabs[i].panelToShow.SetActive(false);
        }

        // Show the main menu panel
        mainMenuPanel.SetActive(true);
    }
}