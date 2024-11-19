# Main Streamlit app

import streamlit as st
from utils.auth import authenticate
from sports_data import get_nfl_schedule, get_game_details
from llm_interface import generate_broadcast
from utils.prompt_helpers import prepare_user_preferences, prepare_game_info


# Streamlit App Title
st.title("Specta AI - Custom Sports Broadcast")

# Login Section
st.sidebar.header("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    if authenticate(username, password):
        st.sidebar.success("Login successful!")
        st.session_state.logged_in = True
    else:
        st.sidebar.error("Invalid credentials.")

if st.session_state.get("logged_in", False):
    # Fetch NFL Schedule
    st.sidebar.header("Game Selection")
    st.sidebar.write("Choose a game to customize your broadcast:")
    nfl_schedule = get_nfl_schedule()
    
    if nfl_schedule:
        game_keys = {game["GameKey"]: f"{game['HomeTeam']} vs {game['AwayTeam']}" for game in nfl_schedule}
        selected_game_key = st.sidebar.selectbox("Select Game", options=list(game_keys.keys()), format_func=lambda x: game_keys[x])

        # Fetch game details
        game_data = get_game_details(selected_game_key)
        
        if game_data:
            st.write(f"### Game: {game_keys[selected_game_key]}")
            st.write(f"Date: {game_data.get('Day')}, Stadium: {game_data.get('Stadium', {}).get('Name', 'Unknown')}")

            # Player selection
            players = st.sidebar.multiselect("Select Players of Interest", [player["Name"] for player in game_data.get("HomeTeamPlayers", []) + game_data.get("AwayTeamPlayers", [])])

            # Tone/Storyline input
            user_prompt = st.sidebar.text_area("Enter 1-2 sentences about how you'd like the broadcast tailored (e.g., tone, storyline).")

            if st.sidebar.button("Generate Broadcast"):
                # Prepare input for LLM
                game_info = prepare_game_info(game_keys[selected_game_key], game_data)
                preferences = prepare_user_preferences(game_keys[selected_game_key], players, user_prompt)

                # Generate Broadcast
                broadcast = generate_broadcast(game_info, preferences)

                # Display Broadcast
                st.write("### Customized Broadcast")
                st.write(broadcast)
        else:
            st.error("Failed to fetch game details.")
    else:
        st.error("Failed to fetch NFL schedule.")
else:
    st.info("Please log in to access the app.")
