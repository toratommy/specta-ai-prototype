import streamlit as st
from utils.auth import authenticate
from sports_data import (
    get_nfl_schedule,
    get_game_details,
    get_players_by_team,
    get_play_by_play,
    get_current_replay_time,
    filter_new_plays,
)
from llm_interface import generate_game_summary, generate_broadcast
from utils.prompt_helpers import prepare_user_preferences

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
    all_players = [
        f"{player['Name']} ({player['Position']}, {player['Team']})"
        for player in get_players_by_team(home_team, replay_api_key) + get_players_by_team(away_team, replay_api_key)
    ]
    selected_players = st.multiselect("Select Players of Interest", all_players)
    return selected_players

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