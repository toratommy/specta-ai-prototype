import streamlit as st
from datetime import datetime
import pytz
from sports_data import (
    extract_season_code,
    get_nfl_schedule,
    get_game_details,
    get_current_replay_time,
    get_players_by_team,
    check_games_in_progress
)
from llm_interface import (
    generate_game_summary, 
    infer_image_contents
)
from utils.utils_functions import (
    initialize_session_state,
    login_dialog,
    sandbox_toggle,
    sign_out,
    player_selections,
    image_upload,
    user_prompt,
    temperature_broadcast,
    handle_broadcast_start,
    process_new_plays
)

# Add the logo to the top of the sidebar
st.sidebar.image("assets/logo.png", use_container_width=True)

# Main App
st.title("Specta AI")
st.header("Your AI Sports Viewing Companion")
st.divider()

initialize_session_state()

# Trigger login dialog if not logged in
if not st.session_state.logged_in:
    login_dialog()

# Sidebar Content After Login
if st.session_state.logged_in:
    with st.sidebar:
        st.header(f"Welcome, {st.session_state.username}")
        if st.button("Sign Out"):
            sign_out()
            st.rerun()
        st.divider()

        # Add API Mode Toggle
        st.sidebar.subheader("API Mode")
        st.session_state.api_mode = st.sidebar.radio(
            "Choose API Mode:",
            options=["Replay", "Live"],
            index=0,  # Default to Replay
            help="Toggle between Replay and Live modes for the SportsData API."
        )
        if st.session_state.api_mode == "Replay":
            st.session_state.replay_api_key = st.sidebar.text_input(
            "Replay API Key",
            value=st.secrets["api_keys"]["sportsdataio_replay"],
            type="password",
            help="Click the link for details on generating a new replay API key [here](https://sportsdata.io/members/replays).",
            )

# Main Content After Login
if st.session_state.logged_in:
    st.sidebar.header("Game Selection")
    st.sidebar.write("Choose a date and game to customize your broadcast:")

    season_code = extract_season_code()
    nfl_schedule = get_nfl_schedule(season_code)
    current_time_est = get_current_replay_time()
    
    if nfl_schedule:
        # Fetch current retime for default date
        default_date = current_time_est or datetime.now()
        selected_date = st.sidebar.date_input("Select Date:", value=default_date.date())

        games_on_date = [
            game for game in nfl_schedule if game["Date"] != None and datetime.strptime(game["Date"], "%Y-%m-%dT%H:%M:%S").date() == selected_date
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
                    home_players = get_players_by_team(home_team)
                    away_players = get_players_by_team(away_team)
                    players = {p['Name'] : p['PlayerID'] for p in home_players + away_players}

                    # Tabs for different features
                    tab1, tab2 = st.tabs(["Play-by-Play Broadcast", "Game Summary"])

                    # Tab 1: Play-by-Play Broadcast
                    with tab1:
                        st.write("### Customized Play-by-Play Broadcast")

                        # Check if games are in progress
                        games_in_progress = check_games_in_progress()

                        if games_in_progress:
                            # Initialize user selection variables
                            st.session_state.selected_players = player_selections(home_players, away_players)
                            uploaded_image = image_upload()
                            if uploaded_image: # Process uploaded image with LLM
                                # Prevent duplicate image processing
                                if st.session_state.image_results['image_name'] != uploaded_image.name:
                                    st.session_state.image_results = infer_image_contents(uploaded_image, players)
                                else:
                                    st.success(
                                        f"""
                                        Image analysis complete!
                                        - `Image type detected: {st.session_state.image_results['image_type']}`
                                        - `Players detected: {list(st.session_state.image_results['players'].keys())}`
                                        - `Description: {st.session_state.image_results['description']}`
                                        """
                                    )
                                st.session_state.selected_players.update(st.session_state.image_results['players']) # add players from image to user selections
                            st.session_state.input_prompt = user_prompt()
                            st.session_state.broadcast_temp = temperature_broadcast()
                            
                            # Sandbox for editing prompt templates
                            sandbox_toggle()
                            
                            # Scrollable container for broadcasts
                            st.divider()
                            broadcast_container = st.container(border=True, height=550)
                            with broadcast_container:
                                st.header("Play-by-Play Broadcast")

                            if game_data["Score"]["IsInProgress"]:
                                if st.button("Start Play-by-Play Broadcast", key="start_broadcast"):
                                    st.session_state.broadcasting = True
                                    handle_broadcast_start(
                                        selected_score_id, 
                                        st.session_state.replay_api_key, 
                                        season_code,
                                        broadcast_container, 
                                        players
                                    )
                                else:
                                    with broadcast_container:
                                        st.info("Make selections and press 'Start Play-by-Play Broadcast'.")

                                if st.session_state.broadcasting:
                                    if st.button("Stop Play-by-Play Broadcast", key="stop_broadcast"):
                                        st.session_state.broadcasting = False
                                        with broadcast_container:
                                            st.info("Broadcast has been stopped.")
                                
                                while st.session_state.broadcasting == True:
                                    process_new_plays(
                                        selected_score_id,
                                        st.session_state.replay_api_key, 
                                        season_code, 
                                        broadcast_container,
                                        players
                                    )
                            else:
                                with broadcast_container:
                                    st.error(f"Playing has not yet started. The current time is {current_time_est.strftime('%Y-%m-%d %I:%M %p')} EST. Please wait for the game action to start or select another game.")
                        else:
                            st.error(f'No games are in progress. The current time is {current_time_est.strftime('%Y-%m-%d %I:%M %p')} EST. Please wait for games to begin or try another replay API key that has games currently in progress.')
                    # Tab 2: Game Summary
                    with tab2:
                        st.write("### Game Summary")
                        temperature_summary = st.slider(
                            "Set the creativity level (temperature):",
                            0.0, 1.0, 0.7, 0.1, key="temperature_summary"
                        )

                        if game_data["Score"]["IsInProgress"] or game_data["Score"]["IsOver"]:
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
                        else:
                            st.error(f"Selected game has not yet started. The current time is {current_time_est.strftime('%Y-%m-%d %I:%M %p')} EST. Please wait for the game to start or select another game.")
                else:
                    st.error(f"Failed to fetch game details. The selected game is not yet in progress. The current time is {current_time_est.strftime('%Y-%m-%d %I:%M %p')} EST. Please wait for the game to start, enter a different replay API key, or select another game.")
            else:
                st.warning("Please select a game using the left pane to proceed.")
        else:
            st.warning("No games found for the selected date.")
    else:
        st.error("Failed to fetch NFL schedule.")
else:
    st.info("Please log in to access the app.")