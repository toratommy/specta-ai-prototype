import requests
import streamlit as st
from dateutil import parser
import pytz
from datetime import datetime
import re

def get_api_config():
    """
    Dynamically selects the API base URL and API key based on the selected mode.

    Returns:
        tuple: (base_url, api_key)
    """
    api_mode = st.session_state.get("api_mode", "Replay")
    if api_mode == "Live":
        return "https://api.sportsdata.io/v3/nfl/", st.secrets["api_keys"]["sportsdataio_live"]
    # Use user-provided Replay API key if available, otherwise fall back to default
    api_key = st.session_state.get("replay_api_key", st.secrets["api_keys"]["sportsdataio_replay"])
    return "https://replay.sportsdata.io/api/v3/nfl/", api_key


def extract_season_code():
    base_url, api_key = get_api_config()
    if st.session_state.api_mode == "Replay":
        try:
            url = f"https://replay.sportsdata.io/api/metadata?key={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            # Extract season codes from AvailableEndpoints
            endpoints = response.json().get("AvailableEndpoints", [])
            season_codes = set(re.findall(r"/(\d{4}(?:post|pre|reg))/", " ".join(endpoints)))
            return season_codes.pop() if season_codes else None
        except Exception as e:
            st.error(f"Error fetching metadata: {e}")
            return None
    else:
        try:
            url = f"{base_url}/scores/json/currentseason"
            params = {"key": api_key}
            response = requests.get(url, params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching season: {e}")
            return None
    
def get_nfl_schedule(season_code):
    """
    Fetches the NFL schedule from the SportsDataIO Replay API.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}scores/json/schedulesbasic/{season_code}"
    params = {"key": api_key}  # API key as query parameter
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
    base_url, api_key = get_api_config()
    url = f"{base_url}stats/json/boxscorebyscoreidv3/{score_id}"
    params = {"key": api_key}  # API key as query parameter
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
    base_url, api_key = get_api_config()
    team_lower = team.lower()  # Ensure the team name is lowercase
    url = f"{base_url}scores/json/playersbasic/{team_lower}"
    params = {"key": api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch players for team {team}: {e}")
        return None

def get_current_season():
    """
    Fetches the current NFL season using the SportsDataIO API.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}scores/json/currentseason"
    params = {"key": api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch the current season: {e}")
        return None

def get_current_week():
    """
    Fetches the current NFL week using the SportsDataIO API.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}scores/json/currentweek"
    params = {"key": api_key}  # API key as query parameter
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch the current week: {e}")
        return None

def get_play_by_play(game_id):
    """
    Fetches all plays for a specific game from the SportsDataIO Replay API.

    Parameters:
        game_id (int): Global Game ID.

    Returns:
        dict: Play-by-play data for the game.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}pbp/json/playbyplay/{game_id}"
    params = {"key": api_key}
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

def get_current_replay_time():
    _, api_key = get_api_config()
    if st.session_state.api_mode == "Replay":
        try:
            url = f"https://replay.sportsdata.io/api/metadata?key={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            current_time = response.json().get("CurrentTime")
            
            if current_time:
                # Parse the time using dateutil and set it as Eastern Time
                eastern_tz = pytz.timezone("US/Eastern")
                replay_time = parser.isoparse(current_time).replace(tzinfo=eastern_tz)
                return replay_time
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching current replay time: {e}")
            return None
    else:
        # Get the current datetime in UTC
        utc_now = datetime.now(pytz.utc)
        # Convert UTC to Eastern Standard Time
        est_now = utc_now.astimezone(pytz.timezone('US/Eastern'))

        return est_now

def check_games_in_progress():
    """
    Checks if any NFL games are currently in progress.
    Returns True if games are in progress, otherwise False.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}scores/json/areanygamesinprogress?key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()  # True if games are in progress, False otherwise
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to check games in progress: {e}")
        return None

def get_player_box_scores(score_id, player_ids):
    """
    Fetches player box scores from the API and filters relevant players.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}stats/json/boxscorebyscoreidv3/{score_id}"
    params = {"key": api_key}

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


def get_player_season_stats(player_ids, season_code):
    """
    Fetches player season stats from the API and filters relevant players.

    Parameters:
        player_ids (list): List of player IDs to filter.
        api_key (str): API key for authentication.

    Returns:
        dict: Dictionary of player stats keyed by PlayerID.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}stats/json/playerseasonstats/{season_code}"
    params = {"key": api_key}

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

def get_latest_in_game_odds(score_id):
    """
    Fetches the most recent in-game betting odds for each sportsbook for a given ScoreId
    from the SportsDataIO Replay API.

    Parameters:
        score_id (int): The ScoreId of the game.
        api_key (str): API key for authenticating with the SportsDataIO Replay API.

    Returns:
        list: A list of dictionaries containing the latest odds for each sportsbook,
              or None if no odds are available.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}odds/json/livegameoddslinemovement/{score_id}"
    params = {"key": api_key}
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

def get_player_props(score_id, player_ids):
    """
    Fetches player props for a given score ID and filters the response based on the list of player IDs.

    Parameters:
        score_id (int): The score ID of the game.
        player_ids (list): List of player IDs to filter the response.
        api_key (str): API key for SportsData.io.

    Returns:
        list: Filtered list of player props for the specified players.
    """
    base_url, api_key = get_api_config()
    url = f"{base_url}odds/json/bettingplayerpropsbyscoreid/{score_id}"
    params = {"key": api_key}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        player_props = response.json()
        
        # Filter props based on player IDs
        filtered_props = [
            prop for prop in player_props if prop["PlayerID"] in player_ids
        ]
        return filtered_props
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch player props for ScoreID {score_id}: {e}")
        return []




