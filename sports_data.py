import requests
import streamlit as st
from datetime import datetime
import re

# Base URL for the SportsDataIO Replay API
BASE_URL = "https://replay.sportsdata.io/api/v3/nfl/"

def extract_season_code(replay_api_key):
    try:
        url = f"https://replay.sportsdata.io/api/metadata?key={replay_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        # Extract season codes from AvailableEndpoints
        endpoints = response.json().get("AvailableEndpoints", [])
        season_codes = set(re.findall(r"/(\d{4}(?:post|pre|reg))/", " ".join(endpoints)))
        return season_codes.pop() if season_codes else None
    except Exception as e:
        st.error(f"Error fetching metadata: {e}")
        return None
    
def get_nfl_schedule(replay_api_key, season_code):
    """
    Fetches the NFL schedule from the SportsDataIO Replay API.
    """
    url = f"{BASE_URL}scores/json/schedulesbasic/{season_code}"
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
    url = f"{BASE_URL}pbp/json/playbyplay/{game_id}"
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
    if last_sequence is None:
        return []
    
    all_plays = play_data.get("Plays", [])

    # Filter out plays with None Sequence or compare safely
    new_plays = [
        play for play in all_plays 
        if play.get("Sequence") is not None and play["Sequence"] > last_sequence
    ]
    return new_plays

def get_current_replay_time(replay_api_key):
    try:
        url = f"https://replay.sportsdata.io/api/metadata?key={replay_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        current_time = response.json().get("CurrentTime")
        return datetime.fromisoformat(current_time.split("Z")[0]) if current_time else None
    except Exception as e:
        st.error(f"Error fetching current replay time: {e}")
        return None

def check_games_in_progress(replay_api_key):
    """
    Checks if any NFL games are currently in progress.
    Returns True if games are in progress, otherwise False.
    """
    url = f"{BASE_URL}scores/json/areanygamesinprogress?key={replay_api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()  # True if games are in progress, False otherwise
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to check games in progress: {e}")
        return None

def get_player_box_scores(score_id, player_ids, replay_api_key):
    """
    Fetches player box scores from the API and filters relevant players.
    """
    url = f"{BASE_URL}stats/json/boxscorebyscoreidv3/{score_id}"
    params = {"key": replay_api_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Parse response as dictionary
        box_scores = response.json()

        # Ensure the structure contains player statistics
        if "PlayerGames" not in box_scores:
            st.error("Player statistics not found in the response.")
            return {}

        # Filter relevant players from the correct key
        return {
            player["PlayerID"]: player 
            for player in box_scores["PlayerGames"] 
            if player["PlayerID"] in player_ids
        }

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch player box scores: {e}")
        return {}


def get_player_season_stats(player_ids, replay_api_key, season_code):
    """
    Fetches player season stats from the API and filters relevant players.

    Parameters:
        player_ids (list): List of player IDs to filter.
        replay_api_key (str): API key for authentication.

    Returns:
        dict: Dictionary of player stats keyed by PlayerID.
    """
    url = f"{BASE_URL}stats/json/playerseasonstats/{season_code}"
    params = {"key": replay_api_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Parse response as a list of player stats
        season_stats = response.json()

        # Ensure the response is a list
        if not isinstance(season_stats, list):
            st.error("Unexpected format received from the API.")
            return {}

        # Filter relevant players based on provided IDs
        filtered_stats = {
            player["PlayerID"]: player 
            for player in season_stats if player["PlayerID"] in player_ids
        }

        return filtered_stats

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch player season stats: {e}")
        return {}

def get_latest_in_game_odds(score_id, replay_api_key):
    """
    Fetches the most recent in-game betting odds for each sportsbook for a given ScoreId
    from the SportsDataIO Replay API.

    Parameters:
        score_id (int): The ScoreId of the game.
        replay_api_key (str): API key for authenticating with the SportsDataIO Replay API.

    Returns:
        list: A list of dictionaries containing the latest odds for each sportsbook,
              or None if no odds are available.
    """
    url = f"https://replay.sportsdata.io/api/v3/nfl/odds/json/livegameoddslinemovement/{score_id}"
    params = {"key": replay_api_key}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        odds_data = response.json()

        if not odds_data or "LiveOdds" not in odds_data[0]:
            return None

        live_odds = odds_data[0]["LiveOdds"]

        # Group odds by SportsbookId and filter for the most recent odds for each sportsbook
        latest_odds_by_sportsbook = {}
        for odd in live_odds:
            sportsbook_id = odd["SportsbookId"]
            if (
                sportsbook_id not in latest_odds_by_sportsbook or
                odd["Updated"] > latest_odds_by_sportsbook[sportsbook_id]["Updated"]
            ):
                latest_odds_by_sportsbook[sportsbook_id] = odd

        # Convert the dictionary to a list for easier use
        return list(latest_odds_by_sportsbook.values())

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch in-game betting odds for ScoreId {score_id}: {e}")
        return None



