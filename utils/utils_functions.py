import streamlit as st
from utils.auth import authenticate
from sports_data import (
    get_players_by_team
)
from llm_interface import generate_broadcast


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

# Player selection fragment
@st.fragment 
def player_selections(home_team, away_team, replay_api_key):
    """
    Allows users to select players of interest from both teams.

    Parameters:
        home_team (str): Home team name.
        away_team (str): Away team name.
        replay_api_key (str): API key for the SportsDataIO Replay API.

    Returns:
        dict: Dictionary of selected players with names as keys and IDs as values.
    """
    # Fetch players from both teams
    home_players = get_players_by_team(home_team, replay_api_key)
    away_players = get_players_by_team(away_team, replay_api_key)

    # Combine and format players for selection
    all_players = {
        f"{p['Name']} ({p['Position']}, {p['Team']})": p['PlayerID']
        for p in home_players + away_players
    }

    # Allow users to select players
    selected_player_keys = st.multiselect(
        "Select Players of Interest", list(all_players.keys())
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

# Format Broadcast Updates
def format_broadcast_update(game_data, play, preferences, selected_players):
    """
    Format broadcast updates with a star icon for priority players.
    Highlights player names by removing team and position details.
    """
    # Generate broadcast content from the LLM
    broadcast_content = generate_broadcast(
        game_info=game_data,
        play_info=play,
        preferences=preferences,
    )

    # Extract player names without team/position details
    for player in selected_players:
        player_name = player.split(" (")[0]
        if player_name in broadcast_content:
            broadcast_content = broadcast_content.replace(
                player_name,
                f"**<span style='color:gold'>⭐ {player_name}</span>**"
            )

    formatted_update = f"**Live Broadcast Update:**\n{broadcast_content}"
    return formatted_update
