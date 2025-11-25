# Live Football Navigator ⚽

A real-time football livescore dashboard and historical data extraction tool. This project uses the **APIFootball** API to provide a low-latency, WebSocket-powered interface with a distinct **Brutalist UI** design.

## 🚀 Features

### 1. Live Navigator (`index.html`)
*   **Real-time Updates:** Powered by WebSockets for instant score, time, and event updates.
*   **Brutalist UI:** A high-contrast, utilitarian interface designed for clarity and efficiency.
*   **Live Sorting:** Matches are automatically ordered by kick-off time. Finished games move to the bottom.
*   **Detailed Match Inspector:** Click any match to open a graphical modal featuring:
    *   Scoreboard with team logos.
    *   Events timeline (Goals, Assists, Cards, Substitutions).
    *   Full Team Lineups (Starting XI, Subs, Coaches, Formations).
    *   Match Statistics.

### 2. Historical Navigator (`history.html`)
*   Browse football data hierarchically.
*   Select **Country** -> Select **League** -> View **League Standings**.

### 3. Data Downloader CLI (`downloader.py`)
*   A robust command-line tool to download match history.
*   **Modes:** Download by Competition or by Specific Team.
*   **Smart Chunking:** Automatically breaks large date ranges into yearly chunks to bypass API limits.
*   **Export Formats:**
    *   **JSON:** Full raw data.
    *   **CSV:** Optimized goal/scorer report (includes competition names).

## 🛠️ Tech Stack

*   **Backend:** Python, FastAPI, Uvicorn
*   **Protocols:** WebSockets, HTTPX (Async requests)
*   **Frontend:** Vanilla HTML, CSS (Brutalist styling), JavaScript

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/live-football-navigator.git
    cd live-football-navigator
    ```

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install fastapi uvicorn[standard] websockets httpx
    ```

## ⚙️ Configuration

You need an API Key from [APIFootball](https://apifootball.com/).

1.  Open `main.py` and replace the placeholder:
    ```python
    API_KEY = "YOUR_API_KEY_HERE"
    ```
2.  Open `downloader.py` and replace the placeholder:
    ```python
    API_KEY = "YOUR_API_KEY_HERE"
    ```

## ▶️ Usage

### Running the Live Dashboard & Backend

1.  Start the FastAPI server:
    ```bash
    uvicorn main:app --reload
    ```
2.  Open `index.html` in your web browser to view the **Live Dashboard**.
3.  Open `history.html` in your web browser to browse **Historical Data**.

### Running the Data Downloader

1.  Ensure your virtual environment is active.
2.  Run the script:
    ```bash
    python downloader.py
    ```
3.  Follow the interactive on-screen prompts to select teams/leagues and download data.

## 📝 License

This project is open-source and available under the MIT License.