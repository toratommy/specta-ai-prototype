from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class PlayContext(BaseModel):
    game_info: Dict[str, Any] = Field(..., description="Information about the game")
    play_info: Dict[str, Any] = Field(..., description="Details of the current play")
    player_box_scores: Optional[Dict[str, Any]] = Field(None, description="Game stats for players involved in the play")
    player_season_stats: Optional[Dict[str, Any]] = Field(None, description="Season stats for players involved in the play")
    betting_odds: Optional[Dict[str, Any]] = Field(None, description="Live betting odds and props")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences for broadcast customization")
