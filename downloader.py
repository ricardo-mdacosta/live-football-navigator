# downloader.py (version 6 - Definitive, with score_info_time in CSV)

import httpx
import json
import sys
import asyncio
import csv
from datetime import datetime, timedelta

# --- Configuration ---
API_KEY = "bccfb046935cd2b3f927c1c73ccbe3deafd36c156cf47816ffb84cc35cbd7aec"  # <-- IMPORTANT: PUT YOUR API KEY HERE
APIFOOTBALL_API_URL = "https://apiv3.apifootball.com/"

# --- Helper Functions (no changes) ---

async def fetch_data(params: dict):
    params["APIkey"] = API_KEY
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(APIFOOTBALL_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "error" in data:
                print(f"\nAPI Error: {data.get('message', 'Unknown error')}")
                return None
            return data
        except httpx.RequestError as e:
            print(f"\nNetwork Error: Could not connect to the API. {e}")
            return None
        except json.JSONDecodeError:
            print("\nError: Could not decode the response from the API.")
            return None

def select_from_list(items: list, display_key: str, id_key: str, prompt: str) -> dict | None:
    print(f"\n--- {prompt} ---")
    if not items:
        print("No items available to select.")
        return None
    for i, item in enumerate(items):
        print(f"{i + 1}. {item[display_key]}")
    while True:
        try:
            choice = input(f"Enter the number of your choice (1-{len(items)}), or 'q' to quit: ")
            if choice.lower() == 'q': return None
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(items):
                return items[choice_index]
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt: return None

def get_date_input(prompt: str) -> str:
    while True:
        date_str = input(f"{prompt} (YYYY-MM-DD): ")
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            print("Invalid format. Please use YYYY-MM-DD.")

async def fetch_events_in_chunks(base_params: dict, from_date_str: str, to_date_str: str) -> list:
    all_matches = []
    try:
        start_date = datetime.strptime(from_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(to_date_str, '%Y-%m-%d')
    except ValueError:
        print("Invalid date format provided.")
        return []
    print("\nCalculating date ranges for download...")
    current_start = start_date
    while current_start <= end_date:
        chunk_end = min(current_start + timedelta(days=90), end_date)
        chunk_params = base_params.copy()
        chunk_params['from'] = current_start.strftime('%Y-%m-%d')
        chunk_params['to'] = chunk_end.strftime('%Y-%m-%d')
        print(f"Fetching data from {chunk_params['from']} to {chunk_params['to']}...")
        matches_chunk = await fetch_data(chunk_params)
        if matches_chunk:
            all_matches.extend(matches_chunk)
            print(f"  > Found {len(matches_chunk)} matches in this period.")
        else:
            print("  > No matches found in this period.")
        current_start = chunk_end + timedelta(days=1)
        await asyncio.sleep(1)
    return all_matches

# --- Saving Functions (CSV function is updated) ---

def save_as_json(data: list, filename: str):
    try:
        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Full data saved to '{filename}.json'")
    except IOError as e:
        print(f"❌ Error saving JSON file. {e}")

# --- THIS IS THE UPDATED FUNCTION ---
def save_as_csv(data: list, filename: str):
    """Saves extracted goal data to a CSV file, including the competition and score info time."""
    # Added 'score_info_time' to the headers
    headers = ['match_date', 'competition_name', 'home_team', 'away_team', 'final_score', 'goal_minute', 'score_info_time', 'scoring_team', 'scorer_name']
    
    try:
        with open(f"{filename}.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for match in data:
                match_date = match.get('match_date', 'N/A')
                competition_name = match.get('league_name', 'N/A')
                home_team = match.get('match_hometeam_name', 'N/A')
                away_team = match.get('match_awayteam_name', 'N/A')
                final_score = f"{match.get('match_hometeam_score')} - {match.get('match_awayteam_score')}"
                
                goalscorers = match.get('goalscorer', [])
                if not goalscorers:
                    # Added an empty placeholder for the new column in goal-less matches
                    writer.writerow([match_date, competition_name, home_team, away_team, final_score, '', '', '', ''])
                else:
                    for goal in goalscorers:
                        scorer = goal.get('home_scorer') or goal.get('away_scorer', 'N/A')
                        scoring_team = home_team if goal.get('home_scorer') else away_team
                        goal_minute = goal.get('time', 'N/A')
                        # Extract the new field
                        score_info = goal.get('score_info_time', 'N/A') 
                        # Add the new field to the row
                        writer.writerow([match_date, competition_name, home_team, away_team, final_score, goal_minute, score_info, scoring_team, scorer])
        
        print(f"✅ Goal data saved to '{filename}.csv'")
    except IOError as e:
        print(f"❌ Error saving CSV file. {e}")

def prompt_and_save(data: list, base_filename: str):
    while True:
        print("\n--- Save Options ---")
        print("1. Save as JSON (full data)")
        print("2. Save as CSV (goal data only)")
        print("3. Save as Both")
        choice = input("Enter your choice: ")
        if choice in ['1', '2', '3']:
            if choice == '1': save_as_json(data, base_filename)
            elif choice == '2': save_as_csv(data, base_filename)
            elif choice == '3':
                save_as_json(data, base_filename)
                save_as_csv(data, base_filename)
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


# --- Download Processes (no changes) ---

async def run_team_download_process():
    print("\nTo find a team, you first need to select its primary country and league.")
    countries = await fetch_data({"action": "get_countries"})
    if not countries: return
    country_choice = select_from_list(countries, 'country_name', 'country_id', "Select the Team's Country")
    if not country_choice: return
    leagues = await fetch_data({"action": "get_leagues", "country_id": country_choice['country_id']})
    if not leagues: return
    league_choice = select_from_list(leagues, 'league_name', 'league_id', "Select the Team's Primary League")
    if not league_choice: return
    teams = await fetch_data({"action": "get_standings", "league_id": league_choice['league_id']})
    if not teams: 
        print("Could not fetch teams for this league.")
        return
    team_choice = select_from_list(teams, 'team_name', 'team_id', "Select the Team")
    if not team_choice: return
    team_id, team_name = team_choice['team_id'], team_choice['team_name']
    print(f"\nSelected Team: {team_name}")
    print("\nEnter the date range for the match history.")
    from_date = get_date_input("Start date")
    to_date = get_date_input("End date")
    base_event_params = {"action": "get_events", "team_id": team_id}
    matches = await fetch_events_in_chunks(base_event_params, from_date, to_date)
    if matches:
        print(f"\nTotal: Found {len(matches)} matches across all competitions.")
        filename = input(f"Enter a base filename for '{team_name}' history (e.g., '{team_name.lower().replace(' ', '_')}_history'): ")
        prompt_and_save(matches, filename)
    else:
        print("\nNo matches found for this team in the selected date range.")

async def run_competition_download_process():
    countries = await fetch_data({"action": "get_countries"})
    if not countries: return
    country_choice = select_from_list(countries, 'country_name', 'country_id', "Select a Country")
    if not country_choice: return
    leagues = await fetch_data({"action": "get_leagues", "country_id": country_choice['country_id']})
    if not leagues: return
    league_choice = select_from_list(leagues, 'league_name', 'league_id', "Select a League")
    if not league_choice: return
    league_id, league_name = league_choice['league_id'], league_choice['league_name']
    print("\nEnter the date range for the match history.")
    from_date = get_date_input("Start date")
    to_date = get_date_input("End date")
    base_event_params = {"action": "get_events", "league_id": league_id}
    matches = await fetch_events_in_chunks(base_event_params, from_date, to_date)
    if matches:
        print(f"\nTotal: Found {len(matches)} matches.")
        filename = input(f"Enter a base filename for {league_name} history (e.g., '{league_name.lower().replace(' ', '_')}_history'): ")
        prompt_and_save(matches, filename)
    else:
        print("\nNo matches found for this league in the selected date range.")


# --- Main Application Loop (no changes) ---

async def main():
    print("="*30)
    print(" APIFootball History Downloader ")
    print("="*30)
    while True:
        print("\n--- Main Menu ---")
        print("1. Download by Competition")
        print("2. Download by Team")
        print("3. Exit")
        choice = input("Enter your choice: ")
        if choice == '1': await run_competition_download_process()
        elif choice == '2': await run_team_download_process()
        elif choice == '3':
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nScript interrupted. Exiting.")
        sys.exit(0)