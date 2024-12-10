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
st.sidebar.image("assets/logo.png", use_container_width=True)

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
if "game_summary" not in st.session_state:
    st.session_state.game_summary = None

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
    st.sidebar.header(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Sign Out"):
        sign_out()

# Main Content After Login
if st.session_state.logged_in:
    st.sidebar.header("Game Selection")
    st.sidebar.write("Choose a date and game to customize your broadcast:")
    nfl_schedule = get_nfl_schedule()

    if nfl_schedule:
        default_date = datetime(2024, 1, 20)
        selected_date = st.sidebar.date_input("Select Date:", value=default_date)

        games_on_date = [
            game for game in nfl_schedule if datetime.strptime(game["Date"], "%Y-%m-%dT%H:%M:%S").date() == selected_date
        ]

        if games_on_date:
            game_keys = {game["ScoreID"]: f"{game['AwayTeam']} vs {game['HomeTeam']}" for game in games_on_date}
            options = ["Select a Game"] + list(game_keys.keys())

            selected_score_id = st.sidebar.selectbox(
                "Select Game",
                options=options,
                format_func=lambda x: game_keys.get(x, x),
            )

            if selected_score_id != "Select a Game":
                game_data = get_game_details(selected_score_id)

                if game_data:
                    home_team = game_data["Score"]["HomeTeam"]
                    away_team = game_data["Score"]["AwayTeam"]

                    # Tabs for different features
                    tab1, tab2 = st.tabs(["Game Summary", "Play-by-Play Broadcast"])

                    # Tab 1: Game Summary
                    with tab1:
                        st.write("### Game Summary")
                        temperature_summary = st.slider(
                            "Set the creativity level (temperature):",
                            0.0, 1.0, 0.7, 0.1, key="temperature_summary"
                        )

                        if st.button("Refresh Game Summary", key="refresh_summary"):
                            with st.spinner("Generating game summary..."):
                                basic_details, game_summary = generate_game_summary(
                                    game_data, temperature_summary
                                )
                                st.session_state.game_summary = (basic_details, game_summary)

                        if st.session_state.game_summary:
                            basic_details, game_summary = st.session_state.game_summary
                            st.markdown(basic_details, unsafe_allow_html=True)
                            st.write(game_summary)
                        else:
                            st.warning("No game summary generated yet. Click 'Refresh Game Summary'.")

                    # Tab 2: Play-by-Play Broadcast
                    with tab2:
                        st.write("### Customized Play-by-Play Broadcast")

                        temperature_broadcast = st.slider(
                            "Set the creativity level (temperature):",
                            0.0, 1.0, 0.7, 0.1, key="temperature_broadcast"
                        )

                        all_players = [
                            f"{player['Name']} ({player['Position']}, {player['Team']})"
                            for player in get_players_by_team(home_team) + get_players_by_team(away_team)
                        ]
                        selected_players = st.multiselect("Select Players of Interest", all_players)

                        user_prompt = st.text_area(
                            "Enter 1-2 sentences about how you'd like the play-by-play broadcast tailored "
                            "(e.g., tone, storyline)."
                        )

                        # Scrollable container for broadcasts
                        broadcast_container = st.container(border=True, height=500)

                        if game_data["Score"]["IsInProgress"]:
                            if st.button("Start Play-by-Play Broadcast", key="start_broadcast"):
                                st.session_state.broadcasting = True
                                play_data = get_play_by_play(game_data["Score"]["ScoreID"])

                                if play_data and play_data["Plays"]:
                                    st.session_state.last_sequence = max(
                                        play["Sequence"] for play in play_data["Plays"]
                                    )
                                    st.info("Broadcast is running...")

                                    with st.spinner("Generating initial play-by-play broadcast..."):
                                        latest_play = max(play_data["Plays"], key=lambda x: x["Sequence"])
                                        preferences = prepare_user_preferences(
                                            selected_players, user_prompt
                                        )
                                        broadcast_content = generate_broadcast(
                                            game_info=latest_play,
                                            preferences=preferences,
                                            temperature=temperature_broadcast,
                                        )
                                        with broadcast_container:
                                            st.chat_message("ai").markdown(f"**Live Broadcast Update:**\n{broadcast_content}")

                            while st.session_state.broadcasting:
                                play_data = get_play_by_play(game_data["Score"]["ScoreID"])

                                if not play_data:
                                    st.error("Failed to fetch play-by-play data. Ending broadcast.")
                                    st.session_state.broadcasting = False
                                    break

                                with st.spinner("Fetching play-by-play data..."):
                                    new_plays = filter_new_plays(
                                        play_data, st.session_state.last_sequence
                                    )

                                if new_plays:
                                    st.session_state.last_sequence = max(
                                        play["Sequence"] for play in new_plays
                                    )

                                    for play in new_plays:
                                        with st.spinner("Generating broadcast update..."):
                                            preferences = prepare_user_preferences(
                                                selected_players, user_prompt
                                            )
                                            broadcast_content = generate_broadcast(
                                                game_info=play,
                                                preferences=preferences,
                                                temperature=temperature_broadcast,
                                            )
                                            with broadcast_container:
                                                st.chat_message("ai").markdown(f"**Live Broadcast Update:**\n{broadcast_content}")

                                    with st.spinner("Waiting for next play..."):
                                        time.sleep(30)
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
