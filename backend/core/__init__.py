"""
Riichi Mahjong Core Module

This module provides the core game logic for Riichi Mahjong.

Main components:
- GameEngine: Pure game logic (no I/O)
- GameState: Immutable game state snapshots
- GameController: Orchestrates games with agents

Usage:
    from backend.core import GameEngine, GameController
    from backend.ai import RandomAgent, HumanCLIAgent
    
    # Option 1: Use the controller for full games
    controller = GameController()
    controller.set_agent(0, HumanCLIAgent("You"))
    for i in range(1, 4):
        controller.set_agent(i, RandomAgent(f"Bot {i}"))
    final_state = controller.run_game()
    
    # Option 2: Use the engine directly for AI training
    engine = GameEngine()
    engine.setup()
    while not engine.is_game_over:
        state = engine.get_state()
        action = my_ai.decide(state)
        engine.apply_action(action)
"""

from .tiles import Tile, Suit, Rank, Honour, create_standard_deck
from .wall import Wall
from .player import Player
from .shanten import ShantenCalculator
from .scorer import Scorer
from .game_state import (
    GameState, GamePhase, GameEvent, GameEventType,
    Action, ActionType, AvailableActions,
    PlayerState, TileState, MeldState, ChiOption
)
from .game_engine import GameEngine

# Lazy imports for controller to avoid circular imports with ai module
def __getattr__(name):
    if name == "GameController":
        from .game_controller import GameController
        return GameController
    elif name == "CLIGameController":
        from .game_controller import CLIGameController
        return CLIGameController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Tiles
    'Tile', 'Suit', 'Rank', 'Honour', 'create_standard_deck',
    # Game components
    'Wall', 'Player', 'ShantenCalculator', 'Scorer',
    # State and actions
    'GameState', 'GamePhase', 'GameEvent', 'GameEventType',
    'Action', 'ActionType', 'AvailableActions',
    'PlayerState', 'TileState', 'MeldState', 'ChiOption',
    # Engine and controller
    'GameEngine', 'GameController', 'CLIGameController',
]
