# Helper functions for prompt-based customization

def prepare_user_preferences(priority_players, box_scores, tone):
    return {
        "priority_players": priority_players,
        "box_scores": box_scores,
        "tone": tone,
    }

def prepare_game_info(game_key, game_data):
    return {
        "GameKey": game_key,
        "game_data": game_data,
    }
