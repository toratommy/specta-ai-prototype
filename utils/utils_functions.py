import streamlit as st
from utils.auth import authenticate
from sports_data import (
    get_play_by_play,
    filter_new_plays,
    get_player_box_scores,
    get_player_season_stats,
    get_latest_in_game_odds,
    get_current_replay_time,
    get_player_props
)
from utils.prompt_helpers import (
    prepare_user_preferences,
    prepare_player_stats,
    prepare_betting_odds
)
from llm_interface import generate_broadcast, load_prompt_template
import time
import pytz


# Initialize session state variables
def initialize_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "broadcasting" not in st.session_state:
        st.session_state.broadcasting = False
    if "last_sequence" not in st.session_state:
        st.session_state.last_sequence = None
    if "game_summary" not in st.session_state:
        st.session_state.game_summary = None
    if "broadcast_prompt" not in st.session_state:
        st.session_state.broadcast_prompt = load_prompt_template("broadcast_prompt.txt") 

# Function to handle sign-out
def sign_out():
    st.session_state.logged_in = False
    st.session_state.username = ""

# Login Dialog
@st.dialog("Login")
def login_dialog():
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_button"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

# Login Dialog
def prompt_container():
    prompt_container = st.container(border=True, height=550)
    with prompt_container:
        st.header("Prompt Sandbox")
        st.info("Sandbox mode activated! Edit your prompt template below.")
        updated_template = st.text_area(label="Prompt Template", 
                                        value=st.session_state.broadcast_prompt,
                                        height=300)
        if st.button("Update Prompt"):
            st.session_state.broadcast_prompt = updated_template
            st.success("Prompt saved!")
        if st.download_button(label="Download Prompt", file_name='prompt_template.txt', data=updated_template):
            st.success("Your prompt has been successfully downloaded to broadcast_prompt.txt")


# Sandbox toggle fragment
@st.fragment
def sandbox_toggle():
    st.session_state.sandbox_toggle = False
    if st.toggle("Open prompt sandbox") == True:
        st.session_state.sandbox_toggle = True

    if st.session_state.sandbox_toggle == True:
        prompt_container()

# Player selection fragment
@st.fragment 
def player_selections(home_players, away_players):
    """
    Allows users to select players of interest from both teams.

    Parameters:
        home_players (list): Home team players.
        away_players (list): Away team players.
        replay_api_key (str): API key for the SportsDataIO Replay API.

    Returns:
        dict: Dictionary of selected players with names as keys and IDs as values.
    """

    # Combine and format players for selection
    all_players = {
        f"{p['Name']} ({p['Position']}, {p['Team']})": p['PlayerID']
        for p in home_players + away_players
    }

    # Allow users to select players
    selected_player_keys = st.multiselect(
        "Select players of interest", list(all_players.keys())
    )

    # Return selected players as a dictionary
    return {key: all_players[key] for key in selected_player_keys}


# User prompt fragment
@st.fragment 
def user_prompt():
    user_prompt = st.text_area(
        "Enter 1-2 sentences about how you'd like the play-by-play broadcast tailored "
        "(e.g., tone, storyline)."
    )
    return user_prompt

# Temperature fragment
@st.fragment 
def temperature_broadcast():
    temperature_broadcast = st.slider(
        "Set the creativity level (temperature):",
        0.0, 1.0, 0.7, 0.1, key="temperature_broadcast"
    )
    return temperature_broadcast

# image upload
@st.fragment 
def image_upload():
    image_upload = st.file_uploader("Upload an image (e.g., bet slip, fantasy roster)", type=["jpg", "png"])
    return image_upload

def get_involved_players(play, players_dict):
    """
    Identifies players involved in the current play based on the play description.

    Parameters:
        play (dict): The play information from play-by-play data.
        players_dict (dict): Dictionary of players with names as keys and PlayerIDs as values.

    Returns:
        list: List of involved PlayerIDs.
    """
    description = play.get("Description", "")
    involved_player_ids = [
        player_id for player_name, player_id in players_dict.items()
        if player_name.split(" (")[0] in description
    ]
    return involved_player_ids

# Format Broadcast Updates
def write_broadcast_update(current_time, game_data, play_data, preferences, selected_players, player_stats, betting_odds, broadcast_temp):
    """
    Format broadcast updates with a star icon for priority players.
    Highlights player names by removing team and position details.
    """
    # Generate broadcast content from the LLM
    broadcast_content = generate_broadcast(
        game_info=game_data,
        play_info=play_data,
        preferences=preferences,
        player_stats=player_stats,
        betting_odds=betting_odds,
        temperature=broadcast_temp
    )

    # Extract player names without team/position details
    for player in selected_players:
        player_name = player.split(" (")[0]
        if player_name in broadcast_content:
            broadcast_content = broadcast_content.replace(
                player_name,
                f"**<span style='color:gold'>⭐ {player_name}</span>**"
            )

    formatted_update = f"**Live Broadcast Update `{current_time.strftime('%Y-%m-%d %I:%M %p %Z')}`:**\n{broadcast_content}"
    return formatted_update

# Start Play-by-Play Broadcast
def handle_broadcast_start(game_data, replay_api_key, broadcast_container, selected_players_dict, input_prompt):
    """
    Starts the play-by-play broadcast by fetching initial data and generating the first update.
    
    Parameters:
        game_data (dict): Game data containing the score and other details.
        replay_api_key (str): API key for the SportsDataIO Replay API.
        broadcast_container (Streamlit container): UI container for displaying broadcasts.
        selected_players (list): List of selected player names.
        input_prompt (str): User-defined prompt for customizing broadcast tone.

    Returns:
        None
    """
    st.session_state.broadcasting = True
    current_time = get_current_replay_time(replay_api_key).astimezone(pytz.timezone("US/Eastern")) 

    with broadcast_container:
        with st.spinner("Fetching play-by-play data..."):
            play_data = get_play_by_play(game_data["Score"]["ScoreID"], replay_api_key)

        if play_data and play_data["Plays"]:
            st.session_state.last_sequence = max(play["Sequence"] for play in play_data["Plays"])
            st.success("Broadcast is running... Hit 'Stop Play-by-Play Broadcast' button to stop the broadcast and update your selections.")

            with st.spinner("Generating play-by-play broadcast..."):
                latest_play = max(play_data["Plays"], key=lambda x: x["Sequence"])
                preferences = prepare_user_preferences(
                        priority_players=selected_players_dict, 
                        tone=input_prompt
                    )
                formatted_update = write_broadcast_update(
                    current_time=current_time,
                    game_data=play_data['Score'], 
                    play_data=latest_play, 
                    preferences=preferences, 
                    selected_players=list(selected_players_dict.keys()), 
                    player_stats=None,
                    betting_odds=None,
                    broadcast_temp=0.7,
                )
                st.chat_message("ai").markdown(formatted_update, unsafe_allow_html=True)
        else:
            st.error("Failed to fetch initial play-by-play data. Ending broadcast.")
            st.session_state.broadcasting = False

# Process New Plays
def process_new_plays(game_data, replay_api_key, season_code, broadcast_container, selected_players_dict, all_players_dict, input_prompt, broadcast_temp):
    """
    Fetches and processes new play data, generating updates for each new play.
    Fetches box scores for priority players involved in the play.
    
    Parameters:
        game_data (dict): Game data containing the score and other details.
        replay_api_key (str): API key for the SportsDataIO Replay API.
        broadcast_container (Streamlit container): UI container for displaying broadcasts.
        selected_players_dict (dict): Dictionary of selected players with names as keys and PlayerIDs as values.
        input_prompt (str): User-defined prompt for customizing broadcast tone.

    Returns:
        None
    """

    current_time = get_current_replay_time(replay_api_key).astimezone(pytz.timezone("US/Eastern")) 

    score_id = game_data["Score"]["ScoreID"]
    play_data = get_play_by_play(score_id, replay_api_key)

    with broadcast_container:
        if not play_data:
            st.error("Failed to fetch play-by-play data. Ending broadcast.")
            st.session_state.broadcasting = False
            return

        with st.spinner("Fetching play-by-play data..."):
            new_plays = filter_new_plays(play_data, st.session_state.last_sequence)

        if new_plays:
            st.session_state.last_sequence = max(play["Sequence"] for play in new_plays)

            for play in new_plays:
                with st.spinner("Generating broadcast update..."):
                    involved_player_ids = get_involved_players(play, all_players_dict)

                    # Fetch box scores, season stats, and player props for involved players
                    box_scores = {}
                    season_stats = {}
                    player_props = {}
                    if involved_player_ids:
                        box_scores = get_player_box_scores(score_id, involved_player_ids, replay_api_key)
                        season_stats = get_player_season_stats(involved_player_ids, replay_api_key, season_code)
                        player_props = get_player_props(score_id, involved_player_ids, replay_api_key)

                    # Fetch latest in-game betting odds
                    latest_betting_odds = get_latest_in_game_odds(score_id, replay_api_key)

                    # Prepare data for the broadcast LLM
                    preferences = prepare_user_preferences(
                        priority_players=selected_players_dict, 
                        tone=input_prompt
                    )

                    player_stats = prepare_player_stats(
                        box_scores=box_scores,
                        season_stats=season_stats
                    )

                    betting_odds = prepare_betting_odds(
                        in_game_betting_odds=latest_betting_odds,
                        player_props=player_props
                    )

                    formatted_update = write_broadcast_update(
                        current_time=current_time,
                        game_data=play_data['Score'], 
                        play_data=play, 
                        preferences=preferences, 
                        selected_players=list(selected_players_dict.keys()), 
                        player_stats=player_stats,
                        betting_odds=betting_odds,
                        broadcast_temp=broadcast_temp
                    )
                    st.chat_message("ai").markdown(formatted_update, unsafe_allow_html=True)

            with st.spinner("Waiting for next play..."):
                time.sleep(5)