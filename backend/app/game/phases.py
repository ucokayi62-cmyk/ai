"""Game phases enumeration."""
from enum import Enum


class GamePhase(str, Enum):
    """Game phase states."""
    
    LOBBY = "LOBBY"
    PREPARING = "PREPARING"
    ROLE_PREPARE = "ROLE_PREPARE"
    NIGHT = "NIGHT"
    MORNING = "MORNING"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    EXECUTION = "EXECUTION"
    WINNER = "WINNER"
    END = "END"
