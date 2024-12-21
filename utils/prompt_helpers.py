# Helper functions for prompt-based customization

def prepare_user_preferences(priority_players, tone):
    return {
        "priority_players": priority_players,
        "tone": tone,
    }

def prepare_game_info(game_key, game_data):
    return {
        "GameKey": game_key,
        "game_data": game_data,
    }

def prepare_player_stats(box_scores, season_stats):
    return {
        "box_scores": box_scores,
        "player_season_stats": season_stats,
    }

def prepare_betting_odds(in_game_betting_odds, player_props):
    return {
        "in_game_betting_odds": in_game_betting_odds,
        "player_props": player_props,
    }
