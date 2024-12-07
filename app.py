import streamlit as st
import time
from datetime import datetime
from utils.auth import authenticate
from sports_data import (
    get_nfl_schedule,
    get_game_details,
    get_players_by_team,
    get_play_by_play,
    filter_new_plays,
)
from llm_interface import generate_game_summary, generate_broadcast
from utils.prompt_helpers import prepare_user_preferences

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
if "broadcasting" not in st.session_state:
    st.session_state.broadcasting = False
if "last_sequence" not in st.session_state:
    st.session_state.last_sequence = None

# Function to handle sign-out
def sign_out():
    st.session_state.logged_in = False
    st.session_state.username = ""

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
                game_data = get_game_details(selected_score_id)

                if game_data:
                    home_team = game_data["Score"]["HomeTeam"]
                    away_team = game_data["Score"]["AwayTeam"]

                    # Generate and display game summary
                    with st.spinner("Fetching game details and generating summary..."):
                        basic_details, game_summary = generate_game_summary(game_data, temperature)
                    st.write("### Game Summary")
                    st.markdown(basic_details, unsafe_allow_html=True)
                    st.write(game_summary)
                    st.divider()

                    # Broadcast Customization Section
                    st.write("### Customized Play-by-Play Broadcast")

                    # Player selection
                    all_players = [
                        f"{player['Name']} ({player['Position']}, {player['Team']})"
                        for player in get_players_by_team(home_team) + get_players_by_team(away_team)
                    ]
                    selected_players = st.multiselect("Select Players of Interest", all_players)

                    # Tone/Storyline input
                    user_prompt = st.text_area(
                        "Enter 1-2 sentences about how you'd like the play-by-play broadcast tailored (e.g., tone, storyline)."
                    )

                    if game_data["Score"]["IsInProgress"]:
                        if st.button("Start Play-by-Play Broadcast"):
                            st.session_state.broadcasting = True

                            # Fetch initial play-by-play data
                            play_data = get_play_by_play(game_data["Score"]["ScoreID"])
                            if play_data and play_data["Plays"]:
                                # Set the last sequence to the most recent play
                                st.session_state.last_sequence = max(
                                    play["Sequence"] for play in play_data["Plays"]
                                )

                                # Generate insight for the most recent play only
                                latest_play = max(play_data["Plays"], key=lambda x: x["Sequence"])
                                preferences = prepare_user_preferences(
                                    selected_players,
                                    user_prompt,
                                )
                                broadcast_content = generate_broadcast(
                                    game_info=latest_play,
                                    preferences=preferences,
                                    temperature=temperature,
                                )
                                st.write("### Live Broadcast Update")
                                st.write(broadcast_content)

                        if st.session_state.get("broadcasting", False):
                            st.info("Broadcast is running... Click 'Stop Broadcast' to end.")

                            stop_broadcast = st.button("Stop Broadcast")
                            while st.session_state.broadcasting and not stop_broadcast:
                                # Fetch updated play-by-play data
                                play_data = get_play_by_play(game_data["Score"]["ScoreID"])
                                if not play_data:
                                    st.error("Failed to fetch play-by-play data. Ending broadcast.")
                                    break

                                # Filter new plays
                                new_plays = filter_new_plays(play_data, st.session_state.last_sequence)

                                if new_plays:
                                    # Update the last sequence number
                                    st.session_state.last_sequence = max(
                                        play["Sequence"] for play in new_plays
                                    )

                                    # Generate insights for all new plays
                                    for play in new_plays:
                                        preferences = prepare_user_preferences(
                                            selected_players,
                                            user_prompt,
                                        )
                                        broadcast_content = generate_broadcast(
                                            game_info=play,
                                            preferences=preferences,
                                            temperature=temperature,
                                        )
                                        with st.chat_message("assistant"):
                                            st.write("### Live Broadcast Update")
                                            st.write(broadcast_content)

                                # Wait for 1 minute before the next API call
                                time.sleep(60)

                            if stop_broadcast:
                                st.session_state.broadcasting = False
                                st.success("Broadcast stopped.")
                    else:
                        st.error("The game is not in progress. Play-by-play broadcast cannot be started.")
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
