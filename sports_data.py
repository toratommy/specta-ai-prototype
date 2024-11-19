import requests
import streamlit as st

def get_nfl_schedule():
    """
    Fetches the NFL schedule for the current season using SportsDataIO.
    """
    api_key = st.secrets["api_keys"]["sportsdataio"]
    url = "https://api.sportsdata.io/v3/nfl/scores/json/Schedules/2024"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch NFL schedule: {e}")
        return []

def get_game_details(game_key):
    """
    Fetches detailed information for a specific NFL game using SportsDataIO.
    Handles 404 errors gracefully.
    """
    api_key = st.secrets["api_keys"]["sportsdataio"]
    url = f"https://api.sportsdata.io/v3/nfl/scores/json/BoxScore/{game_key}"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            st.warning(f"No details available for GameKey: {game_key}. Please select a different game.")
        else:
            st.error(f"Failed to fetch game details for {game_key}: {e}")
        return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to SportsDataIO: {e}")
        return {}

