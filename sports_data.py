import requests
import streamlit as st

# Base URL for the SportsDataIO Replay API
BASE_URL = "https://replay.sportsdata.io/api/v3/nfl/"

def get_nfl_schedule():
    """
    Fetches the NFL schedule for the 2023 postseason from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}scores/json/schedulesbasic/2023post"
    params = {"key": st.secrets["api_keys"]["sportsdataio"]}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch NFL schedule: {e}")
        return None

def get_game_details(score_id):
    """
    Fetches detailed box score information for a specific game from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}stats/json/boxscorebyscoreidv3/{score_id}"
    params = {"key": st.secrets["api_keys"]["sportsdataio"]}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch game details for ScoreID {score_id}: {e}")
        return None

def get_players_by_team(team):
    """
    Fetches players for a specific team from the SportsDataIO Replay API.
    The team parameter must be in lowercase.
    """
    team_lower = team.lower()  # Ensure the team name is lowercase
    url = f"{BASE_URL}scores/json/playersbasic/{team_lower}"
    params = {"key": st.secrets["api_keys"]["sportsdataio"]}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch players for team {team}: {e}")
        return None

def get_play_by_play_delta(season, week, minutes):
    """
    Fetches live play-by-play data for a given season, week, and time window (minutes)
    using the SportsDataIO Play-by-Play Delta API.

    Parameters:
        season (int): The NFL season year.
        week (int): The NFL week.
        minutes (int): The time window in minutes to fetch recent play-by-play data.

    Returns:
        list: A list of play-by-play data updates.
    """
    url = f"{BASE_URL}pbp/json/PlayByPlayDelta/{season}/{week}/{minutes}"
    params = {"key": st.secrets["api_keys"]["sportsdataio"]}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch play-by-play data: {e}")
        return None
