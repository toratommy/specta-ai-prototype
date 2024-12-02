import os
from openai import OpenAI
import streamlit as st
import json

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
        str: Summary of the game data.
    """
    return f"""
    {filtered_game_data['Score']['AwayTeam']} vs {filtered_game_data['Score']['HomeTeam']}
    Score: {filtered_game_data['Score']['AwayScore']} - {filtered_game_data['Score']['HomeScore']}
    Quarter: {filtered_game_data['Score']['Quarter']}
    Time Remaining: {filtered_game_data['Score']['TimeRemaining']}
    Current Possession: {filtered_game_data['Score']['Possession']}
    Last Play: {filtered_game_data['Score']['LastPlay']}
    Stadium: {filtered_game_data['StadiumDetails']['Name']}, {filtered_game_data['StadiumDetails']['City']}, {filtered_game_data['StadiumDetails']['State']}
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
    # Initialize OpenAI client
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
        instructions = (
            "Summarize the matchup, including the teams, date, location, broadcast details, "
            "weather, and key statistics such as point spread and over/under. Highlight pregame insights."
        )
        # Basic game details for display
        basic_details = f"""
- **Teams**: {game_data['Score']['AwayTeam']} vs. {game_data['Score']['HomeTeam']}
- **Date & Time**: {game_data['Score']['DateTime']}
- **Location**: {game_data['Score']['StadiumDetails']['Name']}, {game_data['Score']['StadiumDetails']['City']}, {game_data['Score']['StadiumDetails']['State']}
- **Broadcast**: {game_data['Score']['Channel']}
- **Weather Forecast**: {game_data['Score']['ForecastDescription']}, {game_data['Score']['ForecastTempHigh']}°F, Wind: {game_data['Score']['ForecastWindSpeed']} mph
        """
    else:
        # Summarize and filter for in-progress or over games
        filtered_game_data = filter_relevant_game_data(game_data)
        summarized_data = summarize_game_data(filtered_game_data)
        box_score_json = summarized_data
        instructions = (
            "For games in progress, summarize the current state of the game, including the score, "
            "quarter, time remaining, and notable plays. Highlight trends or momentum shifts.\n"
            "For games that are over, summarize the final outcome, key moments, and standout performances."
        )
        # Basic game details for display
        basic_details = f"""
- **Teams**: {filtered_game_data['Score']['AwayTeam']} vs. {filtered_game_data['Score']['HomeTeam']}
- **Score**: {filtered_game_data['Score']['AwayScore']} - {filtered_game_data['Score']['HomeScore']}
- **Quarter**: {filtered_game_data['Score']['Quarter']}
- **Time Remaining**: {filtered_game_data['Score']['TimeRemaining']}
- **Possession**: {filtered_game_data['Score']['Possession']}
- **Stadium**: {filtered_game_data['StadiumDetails']['Name']}, {filtered_game_data['StadiumDetails']['City']}, {filtered_game_data['StadiumDetails']['State']}
        """

    # Construct the prompt
    prompt = f"""
    The following summarizes the current state of the game:
    {box_score_json}

    Instructions:
    {instructions}

    Generate an engaging game summary based on the information above, emphasizing relevant and interesting details.
    """

    # Call the OpenAI API
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant generating sports game summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=350,  # Limit to 350 tokens for richer summaries
        )
        return basic_details, chat_completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Failed to generate game summary: {e}")
        return basic_details, "Error generating game summary."

def generate_broadcast(game_data, user_preferences):
    """
    Generates a customized broadcast for the selected game and user preferences 
    using OpenAI's function calling feature.
    
    Parameters:
        game_data (dict): Information about the selected game.
        user_preferences (dict): User preferences, including players of interest and tone.
        
    Returns:
        str: Customized broadcast text generated by the LLM.
    """
    # Retrieve OpenAI API key from Streamlit secrets
    openai.api_key = st.secrets["api_keys"]["openai"]

    # Define the function schema for the LLM
    def create_broadcast(game_info, preferences):
        """
        Function to format the broadcast text based on game data and user preferences.
        """
        broadcast_text = f"Broadcast for {game_info['GameKey']}:\n"
        broadcast_text += f"Players of Interest: {', '.join(preferences['players'])}\n"
        broadcast_text += f"Tone: {preferences['tone']}\n"
        broadcast_text += "Game Highlights: ... (generated by LLM)"
        return broadcast_text

    function = {
        "name": "create_broadcast",
        "description": "Generates a customized broadcast for a game.",
        "parameters": {
            "type": "object",
            "properties": {
                "game_info": {
                    "type": "object",
                    "properties": {
                        "GameKey": {"type": "string"},
                        "game_data": {"type": "string"},
                    },
                    "required": ["GameKey", "game_data"],
                },
                "preferences": {
                    "type": "object",
                    "properties": {
                        "players": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "tone": {"type": "string"},
                    },
                    "required": ["players", "tone"],
                },
            },
            "required": ["game_info", "preferences"],
        },
    }

    # Prepare inputs for function calling
    llm_input = {
        "game_info": {
            "GameKey": game_data.get("GameKey", "Unknown Game"),
            "game_data": json.dumps(game_data),
        },
        "preferences": user_preferences,
    }

    # Send a function-calling request to OpenAI's API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",  # Ensure function calling is supported by the model
        messages=[
            {
                "role": "user",
                "content": "Generate a customized broadcast for the user based on the game data and preferences.",
            }
        ],
        functions=[function],
        function_call={"name": "create_broadcast"},
    )

    # Process the response
    message = response["choices"][0]["message"]

    if message.get("function_call"):
        # Extract arguments provided by the LLM for the function
        function_args = json.loads(message["function_call"]["arguments"])
        return create_broadcast(function_args["game_info"], function_args["preferences"])
    else:
        # Handle cases where the LLM doesn't call the function
        return message["content"]
