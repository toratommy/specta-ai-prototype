# Helper functions for prompt-based customization

def prepare_user_preferences(players, tone):
    return {
        "players": players,
        "tone": tone,
    }

def prepare_game_info(game_key, game_data):
    return {
        "GameKey": game_key,
        "game_data": game_data,
    }
