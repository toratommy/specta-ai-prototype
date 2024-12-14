import requests
import streamlit as st

# Base URL for the SportsDataIO Replay API
BASE_URL = "https://replay.sportsdata.io/api/v3/nfl/"

def get_nfl_schedule(replay_api_key):
    """
    Fetches the NFL schedule for the 2023 postseason from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}scores/json/schedulesbasic/2023post"
    params = {"key": replay_api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch NFL schedule: {e}")
        return None

def get_game_details(score_id, replay_api_key):
    """
    Fetches detailed box score information for a specific game from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}stats/json/boxscorebyscoreidv3/{score_id}"
    params = {"key": replay_api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch game details for ScoreID {score_id}: {e}")
        return None

def get_players_by_team(team, replay_api_key):
    """
    Fetches players for a specific team from the SportsDataIO Replay API.
    The team parameter must be in lowercase.
    """
    team_lower = team.lower()  # Ensure the team name is lowercase
    url = f"{BASE_URL}scores/json/playersbasic/{team_lower}"
    params = {"key": replay_api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch players for team {team}: {e}")
        return None

def get_current_season(replay_api_key):
    """
    Fetches the current NFL season using the SportsDataIO API.
    """
    url = f"{BASE_URL}scores/json/currentseason"
    params = {"key": replay_api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch the current season: {e}")
        return None

def get_current_week(replay_api_key):
    """
    Fetches the current NFL week using the SportsDataIO API.
    """
    url = f"{BASE_URL}scores/json/currentweek"
    params = {"key": replay_api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch the current week: {e}")
        return None

def get_play_by_play(game_id, replay_api_key):
    """
    Fetches all plays for a specific game from the SportsDataIO Replay API.

    Parameters:
        game_id (int): Global Game ID.

    Returns:
        dict: Play-by-play data for the game.
    """
    url = f"{BASE_URL.lower()}pbp/json/playbyplay/{game_id}"
    params = {"key": replay_api_key}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch play-by-play data for game ID {game_id}: {e}")
        return None


def filter_new_plays(play_data, last_sequence):
    """
    Filters new plays that have occurred since the last sequence number.

    Parameters:
        play_data (dict): Complete play-by-play data for the game.
        last_sequence (int): The last processed play sequence number.

    Returns:
        list: A list of new plays that occurred after the last sequence.
    """
    all_plays = play_data.get("Plays", [])
    new_plays = [play for play in all_plays if play["Sequence"] > last_sequence]
    return new_plays
