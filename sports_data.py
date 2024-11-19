# Handles sports data ingestion

import requests
from utils.auth import load_config

def get_nfl_schedule():
    config = load_config()
    api_key = config["api_keys"]["sportsdataio"]
    url = "https://api.sportsdata.io/v3/nfl/scores/json/Schedules/2024"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def get_game_details(game_key):
    config = load_config()
    api_key = config["api_keys"]["sportsdataio"]
    url = f"https://api.sportsdata.io/v3/nfl/scores/json/BoxScore/{game_key}"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}
