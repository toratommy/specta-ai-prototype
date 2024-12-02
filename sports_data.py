import requests
import streamlit as st

# Base URL for the SportsDataIO Replay API
BASE_URL = "https://replay.sportsdata.io/v3/nfl/scores/json/"

def get_nfl_games_by_date(date):
    """
    Fetches NFL games for a specific date from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}BoxScoresByDate/{date}"
    headers = {"Ocp-Apim-Subscription-Key": st.secrets["api_keys"]["sportsdataio"]}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch NFL games for {date}: {e}")
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