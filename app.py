import streamlit as st
import time
from datetime import datetime
from utils.auth import authenticate
from sports_data import get_nfl_schedule, get_game_details, get_players_by_team, get_play_by_play_delta
from llm_interface import generate_game_summary, generate_broadcast
from utils.prompt_helpers import prepare_user_preferences, prepare_game_info

# Add the logo to the top of the sidebar
st.sidebar.image("assets/logo.png", use_container_width=True)  # Adjust the path to your logo file

# Main App
st.title("Specta AI")
st.header("Your AI Sports Viewing Companion")
st.divider()

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "broadcast_running" not in st.session_state:
    st.session_state.broadcast_running = False

# Function to handle sign-out
def sign_out():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.broadcast_running = False

# Login Section
if not st.session_state.logged_in:
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="login_username")
    password = st.sidebar.text_input("Password", type="password", key="login_password")

    if st.sidebar.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Invalid credentials.")
else:
    # Add a sign-out button when the user is logged in
    st.sidebar.header(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Sign Out"):
        sign_out()

# Main Content After Login
if st.session_state.logged_in:
    # Fetch NFL Schedule
    st.sidebar.header("Game Selection")
    st.sidebar.write("Choose a date and game to customize your broadcast:")
    nfl_schedule = get_nfl_schedule()

    if nfl_schedule:
        # Add a date selector
        default_date = datetime(2024, 1, 20)
        selected_date = st.sidebar.date_input("Select Date:", value=default_date)

        # Filter games by the selected date
        games_on_date = [
            game for game in nfl_schedule if datetime.strptime(game["Date"], "%Y-%m-%dT%H:%M:%S").date() == selected_date
        ]

        if games_on_date:
            # Create a dictionary of score IDs and their descriptions
            game_keys = {game["ScoreID"]: f"{game['AwayTeam']} vs {game['HomeTeam']}" for game in games_on_date}
            options = ["Select a Game"] + list(game_keys.keys())

            selected_score_id = st.sidebar.selectbox(
                "Select Game",
                options=options,
                format_func=lambda x: game_keys.get(x, x),  # Display the game name or placeholder
            )
            
            # User input for temperature
            temperature = st.sidebar.slider("Set the creativity level (temperature):", 0.0, 1.0, 0.7, 0.1)

            # Ensure a valid game is selected before proceeding
            if selected_score_id != "Select a Game":
                # Fetch game details
                with st.spinner("Fetching game details and generating summary..."):
                    game_data = get_game_details(selected_score_id)

                if game_data:
                    home_team = game_data["Score"]["HomeTeam"]
                    away_team = game_data["Score"]["AwayTeam"]

                    # Generate and display game summary
                    basic_details, game_summary = generate_game_summary(game_data, temperature)
                    st.write("### Game Summary")
                    st.markdown(basic_details, unsafe_allow_html=True)
                    st.write(game_summary)
                    st.divider()

                    # Broadcast Customization Section
                    st.write("### Customized Play-by-Play Broadcast")

                    # Play-by-Play Broadcast Button
                    if not st.session_state.broadcast_running:
                        if st.button("Start Play-by-Play Broadcast"):
                            if not game_data["Score"]["IsInProgress"]:
                                st.error("The game is not currently in progress. Broadcast unavailable.")
                            else:
                                st.session_state.broadcast_running = True
                    else:
                        if st.button("Stop Play-by-Play Broadcast"):
                            st.session_state.broadcast_running = False

                    # Play-by-Play Broadcast Section
                    if st.session_state.broadcast_running:
                        broadcast_placeholder = st.empty()
                        season = datetime.strptime(game_data["Date"], "%Y-%m-%dT%H:%M:%S").year
                        week = game_data["Score"]["Week"]

                        while st.session_state.broadcast_running:
                            play_by_play_data = get_play_by_play_delta(season, week, 1)  # Fetch last 1 minute data
                            if play_by_play_data:
                                broadcast = generate_broadcast(play_by_play_data, temperature)
                                broadcast_placeholder.markdown(f"### Live Broadcast Updates\n{broadcast}")
                            time.sleep(60)  # Wait 1 minute for the next update
                else:
                    st.error("Failed to fetch game details.")
            else:
                st.warning("Please select a game to proceed.")
        else:
            st.warning("No games found for the selected date.")
    else:
        st.error("Failed to fetch NFL schedule.")
else:
    st.info("Please log in to access the app.")
