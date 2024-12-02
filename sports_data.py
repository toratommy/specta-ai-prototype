import requests
import streamlit as st

# Base URL for the SportsDataIO Replay API
BASE_URL = "https://replay.sportsdata.io/api/v3/nfl/scores/json/"

def get_nfl_schedule():
    """
    Fetches the NFL schedule for the 2023 postseason from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}SchedulesBasic/2023POST"
    headers = {"Ocp-Apim-Subscription-Key": st.secrets["api_keys"]["sportsdataio"]}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch NFL schedule: {e}")
        return None

def get_game_details(game_key):
    """
    Fetches detailed information for a specific NFL game from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}BoxScore/{game_key}"
    headers = {"Ocp-Apim-Subscription-Key": st.secrets["api_keys"]["sportsdataio"]}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch game details for {game_key}: {e}")
        return None

