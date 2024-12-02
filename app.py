import streamlit as st
from utils.auth import authenticate
from sports_data import get_nfl_schedule, get_game_details
from llm_interface import generate_game_summary, generate_broadcast
from utils.prompt_helpers import prepare_user_preferences, prepare_game_info

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Function to handle sign-out
def sign_out():
    st.session_state.logged_in = False
    st.session_state.username = ""

# Main App
st.title("Specta AI")
st.header("Customized, AI-Generated Sports Broadcast")
st.divider()  # Divider after the title and subtitle

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
    st.sidebar.write("Choose a game to customize your broadcast:")
    nfl_schedule = get_nfl_schedule()

    if nfl_schedule:
        # Create a dictionary of score IDs and their descriptions with game date
        game_keys = {
            game["ScoreID"]: f"{game['AwayTeam']} vs {game['HomeTeam']} ({game['Date'][:10]})"
            for game in nfl_schedule
        }
        options = ["Select a Game"] + list(game_keys.keys())
        selected_score_id = st.sidebar.selectbox(
            "Select Game",
            options=options,
            format_func=lambda x: game_keys.get(x, x),  # Display the game name with date or placeholder
        )

        # Ensure a valid game is selected before proceeding
        if selected_score_id != "Select a Game":
            # Fetch game details
            game_data = get_game_details(selected_score_id)

            if game_data:
                # User input for temperature
                temperature = st.sidebar.slider("Set the creativity level (temperature):", 0.0, 1.0, 0.7, 0.1)

                # Generate and display game summary
                basic_details, game_summary = generate_game_summary(game_data, temperature)
                st.write("### Game Summary")
                st.markdown(basic_details)
                st.write(game_summary)
                st.divider()

                # Broadcast Customization Section
                st.write("### Customize Your Broadcast")
                
                # Player selection
                players = st.multiselect(
                    "Select Players of Interest",
                    [player["Name"] for player in game_data.get("HomeTeamPlayers", []) + game_data.get("AwayTeamPlayers", [])],
                )

                # Tone/Storyline input
                user_prompt = st.text_area(
                    "Enter 1-2 sentences about how you'd like the broadcast tailored (e.g., tone, storyline)."
                )

                if st.button("Generate Broadcast"):
                    # Prepare input for LLM
                    game_info = prepare_game_info(game_keys[selected_score_id], game_data)
                    preferences = prepare_user_preferences(game_keys[selected_score_id], players, user_prompt)

                    # Generate Broadcast
                    broadcast = generate_broadcast(game_info, preferences)

                    # Display Broadcast
                    st.write("### Customized Broadcast")
                    st.write(broadcast)
            else:
                st.error("Failed to fetch game details.")
        else:
            st.warning("Please select a game to proceed.")
    else:
        st.error("Failed to fetch NFL schedule.")
else:
    st.info("Please log in to access the app.")
