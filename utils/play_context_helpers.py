# Helper functions preparing play context attributes

def prepare_user_preferences(priority_players, tone, image_results):
    return {
        "priority_players": priority_players,
        "tone": tone,
        "uploaded_image":image_results,
    }

def prepare_game_info(game_key, game_data):
    return {
        "GameKey": game_key,
        "game_data": game_data,
    }

def prepare_player_season_stats(season_stats):
    return {
        "player_season_stats": season_stats,
    }

def prepare_player_box_scores(box_scores):
    return {
        "player_box_scores": box_scores,
    }

def prepare_betting_odds(in_game_betting_odds, player_props):
    return {
        "in_game_betting_odds": in_game_betting_odds,
        "player_props": player_props,
    }
