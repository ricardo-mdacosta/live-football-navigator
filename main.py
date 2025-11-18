# main.py (version 6 - Definitive, with Live Logging)

import asyncio
import websockets
import json
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# --- FastAPI Application Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
API_KEY = "bc69a33db01951b927e95cbdc19507eee2845cef90d3e66fec73607a228f0dff"  # Make sure your key is still here
APIFOOTBALL_WSS_URL = f"wss://wss.apifootball.com/livescore?APIkey={API_KEY}"
APIFOOTBALL_API_URL = "https://apiv3.apifootball.com/"


# --- ConnectionManager for WebSockets (no changes) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


# --- NEW: Helper function to log updates to the console ---
def log_match_update(match_data: dict):
    """Parses a match object and prints a formatted log message."""
    action = match_data.get('action', 'update')
    home_team = match_data.get('match_hometeam_name', 'N/A')
    away_team = match_data.get('match_awayteam_name', 'N/A')
    home_score = match_data.get('match_hometeam_score', '0')
    away_score = match_data.get('match_awayteam_score', '0')
    status = match_data.get('match_status', '')
    
    # Format the core info string
    info_str = f"| {status}' | {home_team} {home_score} - {away_score} {away_team}"

    if action == 'goal':
        scorer = "Unknown"
        # The goalscorer array contains all goals, the last one is the most recent
        if match_data.get('goalscorer'):
            last_goal = match_data['goalscorer'][-1]
            scorer_name = last_goal.get('home_scorer') or last_goal.get('away_scorer')
            if scorer_name:
                scorer = f"by {scorer_name}"
        
        print(f"[GOAL]   ⚽️  {info_str} ({scorer})")
    else:
        # For any other update ('match_live', etc.)
        print(f"[UPDATE] ⏱️  {info_str}")


# --- WebSocket Listener (UPDATED to use the logger) ---
async def apifootball_listener():
    while True:
        try:
            print("Connecting to APIFootball WebSocket...")
            async with websockets.connect(APIFOOTBALL_WSS_URL, ping_interval=20) as websocket:
                print("Successfully connected to APIFootball WebSocket.")
                async for message in websocket:
                    # --- LOGGING LOGIC ADDED HERE ---
                    try:
                        data = json.loads(message)
                        matches_to_process = data if isinstance(data, list) else [data]
                        
                        for match in matches_to_process:
                            if match.get("match_id"):
                                log_match_update(match)

                    except json.JSONDecodeError:
                        print(f"[ERROR] Could not decode incoming JSON: {message[:100]}...")
                    
                    # Broadcast to frontend clients regardless of logging success
                    await manager.broadcast(message)

        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as e:
            print(f"APIFootball connection closed: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


# --- WebSocket Endpoint (no changes) ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Historical Data Endpoints (no changes) ---
@app.get("/team/{team_id}")
async def get_team_details(team_id: int):
    params = {"action": "get_teams", "team_id": team_id, "APIkey": API_KEY}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(APIFOOTBALL_API_URL, params=params)
            response.raise_for_status(); data = response.json()
            return data[0] if data else {"error": "Team not found"}
        except httpx.RequestError as e: return {"error": f"Failed to fetch data: {e}"}

@app.get("/countries")
async def get_countries():
    params = {"action": "get_countries", "APIkey": API_KEY}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(APIFOOTBALL_API_URL, params=params)
            response.raise_for_status(); data = response.json()
            return data if "error" not in data else {"error": data.get("message", "API error")}
        except httpx.RequestError as e: return {"error": f"Failed to fetch data: {e}"}

@app.get("/leagues/{country_id}")
async def get_leagues(country_id: int):
    params = {"action": "get_leagues", "country_id": country_id, "APIkey": API_KEY}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(APIFOOTBALL_API_URL, params=params)
            response.raise_for_status(); data = response.json()
            return data if "error" not in data else {"error": data.get("message", "API error")}
        except httpx.RequestError as e: return {"error": f"Failed to fetch data: {e}"}

@app.get("/standings/{league_id}")
async def get_standings(league_id: int):
    params = {"action": "get_standings", "league_id": league_id, "APIkey": API_KEY}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(APIFOOTBALL_API_URL, params=params)
            response.raise_for_status(); data = response.json()
            return data if "error" not in data else {"error": data.get("message", "API error")}
        except httpx.RequestError as e: return {"error": f"Failed to fetch data: {e}"}

# --- Startup Event (no changes) ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(apifootball_listener())
    print("Backend server started. APIFootball listener task created.")