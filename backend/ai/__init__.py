"""
Riichi Mahjong AI Module

This module provides AI agents for playing Riichi Mahjong.

Available agents:
- Agent: Abstract base class for all agents
- PassiveAgent: Always passes (useful for testing)
- RandomAgent: Makes random valid decisions
- DefensiveRandomAgent: Random but prefers safe discards
- HumanCLIAgent: Human player via command line
- MCTSAgent: Monte Carlo Tree Search (template)
- MinimaxAgent: Minimax search (template)

To create your own AI:
    from backend.ai import Agent
    from backend.core import GameState, Action, ActionType, AvailableActions
    
    class MyAI(Agent):
        def choose_action(self, state: GameState, available: AvailableActions) -> Action:
            # Your AI logic here
            # Analyse state.players, state.dora_indicators, etc.
            # Return an Action from available.get_actions()
            pass
"""

from .agent import Agent, PassiveAgent
from .random_agent import RandomAgent, DefensiveRandomAgent
from .human_cli_agent import HumanCLIAgent
from .mcts import MCTSAgent
from .minimax import MinimaxAgent

__all__ = [
    'Agent',
    'PassiveAgent',
    'RandomAgent',
    'DefensiveRandomAgent',
    'HumanCLIAgent',
    'MCTSAgent',
    'MinimaxAgent',
]
