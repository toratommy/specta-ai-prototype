import streamlit as st
import time
import pytz
import datetime
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
from utils.play_context_helpers import (
    prepare_user_preferences,
    prepare_player_season_stats,
    prepare_player_box_scores,
    prepare_betting_odds
)
from llm_interface import generate_broadcast, load_prompt_template
from utils.play_context import PlayContext

def prepare_play_context(game_data, play_data, player_box_scores, player_season_stats, betting_odds, preferences):
    """
    Prepares a PlayContext object from individual data components.

    Parameters:
        game_data (dict): Game information.
        play_data (dict): Play details.
        player_box_scores (dict): Box scores for players involved.
        player_season_stats (dict): Season stats for players involved.
        betting_odds (dict): Betting odds data.
        preferences (dict): User preferences.

    Returns:
        PlayContext: A fully populated PlayContext object.
    """
    return PlayContext(
        game_info=game_data,
        play_info=play_data,
        player_box_scores=player_box_scores,
        player_season_stats=player_season_stats,
        betting_odds=betting_odds,
        preferences=preferences,
    )

# Initialize session state variables
def initialize_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "api_mode" not in st.session_state:
        st.session_state.api_mode = "Replay"  # Default to Replay
    if "replay_api_key" not in st.session_state:
        st.session_state.replay_api_key = st.secrets["api_keys"]["sportsdataio_replay"]  # Default Replay key
    if "broadcasting" not in st.session_state:
        st.session_state.broadcasting = False
    if "last_sequence" not in st.session_state:
        st.session_state.last_sequence = None
    if "game_summary" not in st.session_state:
        st.session_state.game_summary = None
    if "selected_players" not in st.session_state:
        st.session_state.selected_players = None
    if "input_prompt" not in st.session_state:
        st.session_state.input_prompt = None
    if "image_results" not in st.session_state:
        st.session_state.image_results = {'players':{}, 'image_type':'', 'description':'', 'image_name':''}
    if "broadcast_data_prompt" not in st.session_state:
        st.session_state.broadcast_data_prompt = load_prompt_template("broadcast_data_prompt.txt")
    if "broadcast_instructions_prompt" not in st.session_state:
        st.session_state.broadcast_instructions_prompt = load_prompt_template("broadcast_instructions_prompt.txt")
    if "broadcast_temp" not in st.session_state:
        st.session_state.broadcast_temp = 0.7


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
                                        value=st.session_state.broadcast_instructions_prompt,
                                        height=300)
        if st.button("Update Prompt"):
            st.session_state.broadcast_instructions_prompt = updated_template
            st.success("Prompt saved!")
        if st.download_button(label="Download Prompt", file_name='prompt_template.txt', data=updated_template):
            st.success("Your prompt has been successfully downloaded to prompt_template.txt")


# Sandbox toggle fragment
@st.fragment
def sandbox_toggle():
    st.session_state.sandbox_toggle = False
    if st.toggle(label="Open prompt sandbox", help="Broadcast must be stopped in order to open prompt sandbox.") == True:
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
def write_broadcast_update(current_time, play_context: PlayContext, broadcast_temp: float) -> str:
    """
    Format broadcast updates with a star icon for priority players.
    Highlights player names by removing team and position details.
    """

    # Ordinal mapping for quarters and downs
    ordinals_down = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
    ordinals_quarter = {'1': "1st", '2': "2nd", '3': "3rd", '4': "4th"}

    # Extract key game details
    score = f"{play_context.game_info['AwayScore']} - {play_context.game_info['HomeScore']}"
    time_remaining = f"{ordinals_quarter.get(play_context.play_info['QuarterName'], play_context.play_info['QuarterName'])} Quarter, {play_context.play_info['TimeRemainingMinutes']}:{str(play_context.play_info['TimeRemainingSeconds']).zfill(2)} remaining"
    ball_location = f"{play_context.play_info['YardLineTerritory']} {play_context.play_info['YardLine']}-yard line"
    possession = play_context.play_info['Team']
    down = f"{ordinals_down.get(play_context.play_info['Down'])} & {play_context.play_info['Distance']}"

    # Format the key game details into bullet points
    game_details = (
        f"- **Score**: {score}\n"
        f"- **Time Remaining**: {time_remaining}\n"
        f"- **Ball Location**: {ball_location}\n"
        f"- **Possession**: {possession}\n"
        f"- **Down**: {down}"
    )

    # Generate broadcast content from the LLM
    broadcast_content = generate_broadcast(
        play_context,
        temperature=broadcast_temp
    )

    # Extract player names without team/position details
    for player in play_context.preferences['priority_players']:
        player_name = player.split(" (")[0]
        if player_name in broadcast_content:
            broadcast_content = broadcast_content.replace(
                player_name,
                f"**<span style='color:gold'>⭐ {player_name}</span>**"
            )

    formatted_update = (
        f"**Live Broadcast Update `{current_time.strftime('%Y-%m-%d %I:%M %p')}`:**\n\n"
        f"{game_details}\n\n"
        f"{broadcast_content}"
    )
    return formatted_update

def generate_involved_player_stats(score_id, play, season_code, players):
    involved_player_ids = get_involved_players(play, players)
    box_scores = {}
    season_stats = {}
    player_props = {}
    if involved_player_ids:
        box_scores = get_player_box_scores(score_id, involved_player_ids)
        season_stats = get_player_season_stats(involved_player_ids, season_code)
        player_props = get_player_props(score_id, involved_player_ids)

    return box_scores, season_stats, player_props, involved_player_ids


# Start Play-by-Play Broadcast
def handle_broadcast_start(score_id, replay_api_key, season_code, broadcast_container, players):
    """
    Starts the play-by-play broadcast by fetching initial data and generating the first update.

    Parameters:
        game_data (dict): Game data containing the score and other details.
        replay_api_key (str): API key for the SportsDataIO Replay API.
        broadcast_container (Streamlit container): UI container for displaying broadcasts.
        selected_players (dict): Dictionary of selected players with names as keys and IDs as values.
        input_prompt (str): User-defined prompt for customizing broadcast tone.

    Returns:
        None
    """
    st.session_state.broadcasting = True
    current_time = get_current_replay_time().astimezone(pytz.timezone("US/Eastern"))

    with broadcast_container:
        with st.spinner("Fetching play-by-play data..."):
            play_data = get_play_by_play(score_id)
            game_data = play_data["Score"]

        if play_data and play_data["Plays"]:
            st.session_state.last_sequence = max(play["Sequence"] for play in play_data["Plays"])
            st.success("Broadcast is running... Hit 'Stop Play-by-Play Broadcast' button to stop the broadcast and update your selections.")

            with st.spinner("Generating play-by-play broadcast..."):
                latest_play = max(play_data["Plays"], key=lambda x: x["Sequence"])

                # get player stats and betting odds
                box_scores, season_stats, player_props, involved_player_ids = generate_involved_player_stats(score_id, latest_play, season_code, players)
                latest_betting_odds = get_latest_in_game_odds(score_id)

                # only pass through uploaded image results if they are relevant to the current play
                if any(player in list(st.session_state.image_results['players'].values()) for player in involved_player_ids):
                    play_relevant_image_results = st.session_state.image_results
                else:
                    play_relevant_image_results = None

                play_context = prepare_play_context(
                    game_data=game_data,
                    play_data=latest_play,
                    player_box_scores=prepare_player_box_scores(box_scores),
                    player_season_stats=prepare_player_season_stats(season_stats),
                    betting_odds=prepare_betting_odds(latest_betting_odds, player_props),
                    preferences=prepare_user_preferences(st.session_state.selected_players, st.session_state.input_prompt, play_relevant_image_results),
                )
                formatted_update = write_broadcast_update(
                    current_time=current_time,
                    play_context=play_context,
                    broadcast_temp=st.session_state.broadcast_temp,
                )
                st.chat_message("ai").markdown(formatted_update, unsafe_allow_html=True)
        else:
            st.error("Failed to fetch initial play-by-play data. Ending broadcast.")
            st.session_state.broadcasting = False

# Process New Plays
def process_new_plays(score_id, replay_api_key, season_code, broadcast_container, players):
    """
    Fetches and processes new play data, generating updates for each new play.
    Fetches box scores for priority players involved in the play.

    Parameters:
        game_data (dict): Game data containing the score and other details.
        replay_api_key (str): API key for the SportsDataIO Replay API.
        broadcast_container (Streamlit container): UI container for displaying broadcasts.
        selected_players (dict): Dictionary of selected players with names as keys and PlayerIDs as values.
        input_prompt (str): User-defined prompt for customizing broadcast tone.

    Returns:
        None
    """
    current_time = get_current_replay_time().astimezone(pytz.timezone("US/Eastern"))

    play_data = get_play_by_play(score_id)
    game_data = play_data["Score"]

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
                    
                    # get player stats and betting odds
                    box_scores, season_stats, player_props, involved_player_ids = generate_involved_player_stats(score_id, play, season_code, players)
                    latest_betting_odds = get_latest_in_game_odds(score_id)

                    # only pass through uploaded image results if they are relevant to the current play
                    if any(player in list(st.session_state.image_results['players'].values()) for player in involved_player_ids):
                        play_relevant_image_results = st.session_state.image_results
                    else:
                        play_relevant_image_results = None

                    play_context = prepare_play_context(
                        game_data=game_data,
                        play_data=play,
                        player_box_scores=prepare_player_box_scores(box_scores),                        
                        player_season_stats=prepare_player_season_stats(season_stats),
                        betting_odds=prepare_betting_odds(latest_betting_odds, player_props),
                        preferences=prepare_user_preferences(st.session_state.selected_players, st.session_state.input_prompt, play_relevant_image_results),
                    )
                    # st.write(play_context.play_info)
                    # st.write(play_context.player_box_scores)
                    # st.write(play_context.player_season_stats)

                    formatted_update = write_broadcast_update(
                        current_time=current_time,
                        play_context=play_context,
                        broadcast_temp=st.session_state.broadcast_temp,
                    )
                    st.chat_message("ai").markdown(formatted_update, unsafe_allow_html=True)

            with st.spinner("Waiting for next play..."):
                time.sleep(3)