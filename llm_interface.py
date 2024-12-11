import os
from openai import OpenAI
import streamlit as st
import json

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
                {"role": "system", "content": "You are a helpful assistant generating sports game summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=350,
        )
        return box_score_json, chat_completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Failed to generate game summary: {e}")
        return box_score_json, "Error generating game summary."

def generate_broadcast(game_info, preferences, temperature=0.7):
    """
    Generates a customized play-by-play broadcast using OpenAI's API.

    Parameters:
        game_info (str): Information about the selected game.
        preferences (str): User preferences for tone, storyline, and players of interest.
        temperature (float): Temperature setting for the LLM.

    Returns:
        str: LLM-generated broadcast.
    """
    client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

    # Load the broadcast prompt template
    prompt_template = load_prompt_template("broadcast_prompt.txt")
    prompt = prompt_template.format(game_info=game_info, preferences=preferences)

    # Call the OpenAI API
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant generating sports play-by-play broadcasts."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=350,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Failed to generate play-by-play broadcast: {e}")
        return "Error generating broadcast."
