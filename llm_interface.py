import os
import io
import base64
from openai import OpenAI
import streamlit as st
import json
from langchain.llms import OpenAI as LangChainOpenAI
from PIL import Image
from utils.play_context import PlayContext

# Helper function to load prompt templates
def load_prompt_template(template_name):
    with open(f"prompts/{template_name}", "r") as file:
        return file.read()

def filter_relevant_game_data(game_data):
    """
    Filters the relevant fields from the game data JSON for games in progress or over.

    Parameters:
        game_data (dict): Full game data JSON.

    Returns:
        dict: Filtered game data.
    """
    return {
        "Score": {
            "AwayTeam": game_data["Score"]["AwayTeam"],
            "HomeTeam": game_data["Score"]["HomeTeam"],
            "AwayScore": game_data["Score"]["AwayScore"],
            "HomeScore": game_data["Score"]["HomeScore"],
            "Quarter": game_data["Score"]["Quarter"],
            "TimeRemaining": game_data["Score"]["TimeRemaining"],
            "Possession": game_data["Score"]["Possession"],
            "LastPlay": game_data["Score"].get("LastPlay", ""),
        },
        "StadiumDetails": {
            "Name": game_data["Score"]["StadiumDetails"]["Name"],
            "City": game_data["Score"]["StadiumDetails"]["City"],
            "State": game_data["Score"]["StadiumDetails"]["State"],
        },
    }

def summarize_game_data(filtered_game_data):
    """
    Creates a summarized string from the filtered game data for the LLM prompt.

    Parameters:
        filtered_game_data (dict): Filtered game data.

    Returns:
        str: Summary of the game data in bullet-point format.
    """
    return f"""
    - **Teams**: {filtered_game_data['Score']['AwayTeam']} vs {filtered_game_data['Score']['HomeTeam']}
    - **Score**: {filtered_game_data['Score']['AwayScore']} - {filtered_game_data['Score']['HomeScore']}
    - **Quarter**: {filtered_game_data['Score']['Quarter']}
    - **Time Remaining**: {filtered_game_data['Score']['TimeRemaining']}
    - **Current Possession**: {filtered_game_data['Score']['Possession']}
    - **Last Play**: {filtered_game_data['Score']['LastPlay']}
    - **Stadium**: {filtered_game_data['StadiumDetails']['Name']}, {filtered_game_data['StadiumDetails']['City']}, {filtered_game_data['StadiumDetails']['State']}
    """

def generate_game_summary(game_data, temperature=0.7):
    """
    Generates a game summary using OpenAI's API based on the provided game data.

    Parameters:
        game_data (dict): Detailed box score data for the game.
        temperature (float): Temperature setting for the LLM.

    Returns:
        tuple: Basic game details (str) and LLM-generated game summary (str).
    """
    client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

    # Determine the game status
    game_status = (
        "not started" if not game_data["Score"]["HasStarted"]
        else "in progress" if game_data["Score"]["IsInProgress"]
        else "over"
    )

    # Handle summarization based on game status
    if game_status == "not started":
        box_score_json = json.dumps(game_data, indent=2)
        dynamic_instructions = (
            "Summarize the matchup, including the teams, date, location, broadcast details, "
            "weather, and key statistics such as point spread and over/under. Highlight pregame insights."
        )
    else:
        filtered_game_data = filter_relevant_game_data(game_data)
        summarized_data = summarize_game_data(filtered_game_data)
        box_score_json = summarized_data
        if game_status == "in progress":
            dynamic_instructions = (
                "Summarize the current state of the game, including the score, quarter, time remaining, "
                "and notable plays. Highlight trends or momentum shifts."
            )
        else:  # Game Over
            dynamic_instructions = (
                "Summarize the final outcome of the game, including the final score, key moments, "
                "and standout performances. Highlight the overall impact of the game."
            )

    # Load the game summary prompt template
    prompt_template = load_prompt_template("game_summary_prompt.txt")
    prompt = prompt_template.format(box_score_json=box_score_json, dynamic_instructions=dynamic_instructions)

    # Call the OpenAI API
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": "You are a helpful assistant generating sports game summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=350,
        )
        return box_score_json, chat_completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Failed to generate game summary: {e}")
        return box_score_json, "Error generating game summary."

def generate_broadcast(play_context: PlayContext, temperature: float = 0.7) -> str:
    """
    Generates a customized play-by-play broadcast using OpenAI's API.

    Parameters:
        play_context (PlayContext): Encapsulated context for the play.
        temperature (float): Creativity level for the LLM.

    Returns:
        str: Generated broadcast content.
    """
    instructions_prompt = st.session_state.broadcast_instructions_prompt
    data_prompt_template = st.session_state.broadcast_data_prompt
    data_prompt = data_prompt_template.format(
        game_info=play_context.game_info,
        play_info=play_context.play_info,
        preferences=play_context.preferences,
        player_box_scores=play_context.player_box_scores,
        player_season_stats=play_context.player_season_stats,
        betting_odds=play_context.betting_odds,
    )

    try:
        client = OpenAI(api_key=st.secrets["api_keys"]["openai"])
        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": f"You are a helpful assistant generating sports play-by-play broadcast updates. For each update, please adhere to the instructions below. {instructions_prompt}"},
                {"role": "user", "content": data_prompt}
            ],
            temperature=temperature,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Failed to generate broadcast: {e}")
        return "Error generating broadcast."
    
def encode_image(uploaded_image):
    """
    Encodes an uploaded image file to a base64 string for LLM processing.

    Parameters:
        uploaded_image: Uploaded file object.

    Returns:
        str: Base64-encoded string of the image.
    """
    image_bytes = uploaded_image.read()  # Read the content of the uploaded file
    return base64.b64encode(image_bytes).decode("utf-8")


def infer_image_contents(uploaded_image, players):
    """
    Infers player names and image type (bet slip, fantasy roster, or other) from the uploaded image.

    Parameters:
        uploaded_image: Uploaded file object from Streamlit.
        players (dict): Dictionary of all players with names as keys and IDs as values.

    Returns:
        dict: Dictionary with inferred player names and image type.
    """
    with st.spinner('Analyzing your image...'):
        if not uploaded_image:
            return {"players": {}, "image_type": "No image uploaded.", "description": "N/A", "image_name":""}

        # Encode the image
        base64_image = encode_image(uploaded_image)

        # Prepare LLM input
        players_text = ", ".join(players.keys())

        llm_prompt = f"""
        You are an AI assistant helping with sports image analysis.
        Given the following image, determine:
        1. Which player names from this list are present: {players_text}.
        2. Classify the image as one of the following types: 'bet slip', 'fantasy roster', or 'other'.
        3. Generate a brief description of the image. E.g., if it's a bet slip, describe the bets placed. 

        Use OCR to extract text from the image and infer the information.
        Respond in valid JSON format like this:
        {{
            "players": ["Player1", "Player2"],
            "image_type": "bet slip"
            "description": "Player1 50+ yards (+250 odds, $10 wager to win $25); Player2 to score 2+ tochdowns (+150 odds, $20 wager to win $30)"
        }}
        """

        client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": llm_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                ],
            }
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            analysis_result = response.choices[0].message.content.strip()
            # Remove any extra backticks if present and parse as JSON
            cleaned_response = analysis_result.strip("```json ").strip("```")
            cleaned_response = json.loads(cleaned_response)

            detected_players = {
                player: players[player]
                for player in cleaned_response["players"]
                if player in players
            }

            st.success(
                f"""
                Image analysis complete!
                - `Image type detected: {cleaned_response['image_type']}`
                - `Players detected: {list(detected_players.keys())}`
                - `Description: {cleaned_response['description']}`
                """
            )
            return {"players": detected_players, "image_type": cleaned_response['image_type'], "description": cleaned_response['description'], "image_name":uploaded_image.name}
        except Exception as e:
            st.error(f"Failed to analyze image contents: {e}")
            return {"players": {}, "image_type": "Error processing image", "description": "N/A", "image_name":uploaded_image.name}
