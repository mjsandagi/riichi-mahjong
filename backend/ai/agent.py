"""
Agent Module - Abstract base class for Mahjong AI agents.

This module defines the interface that all agents (human or AI) must implement.
An agent receives game state and returns an action.

Usage:
    class MyAI(Agent):
        def choose_action(self, state, available_actions):
            # Analyse state, return best action
            return Action(ActionType.DISCARD, player_index, tile_index=5)
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..core.game_state import GameState, Action, AvailableActions


class Agent(ABC):
    """
    Abstract base class for all Mahjong agents.
    
    An agent is any entity that can make decisions in the game:
    - Human players (via CLI, GUI, or network)
    - AI bots (random, minimax, MCTS, neural network, etc.)
    - Remote players (via WebSocket)
    
    The agent interface is intentionally simple:
    - Receive game state
    - Return an action
    
    This allows for easy testing, simulation, and swapping of agents.
    """
    
    def __init__(self, name: str = "Agent"):
        """
        Initialise the agent.
        
        Args:
            name: Display name for the agent.
        """
        self.name = name
        self.player_index: Optional[int] = None  # Set when assigned to a seat
    
    @abstractmethod
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """
        Choose an action given the current game state.
        
        This is the main decision-making method that all agents must implement.
        
        Args:
            state: The current game state (immutable snapshot).
                   Contains all visible information about the game.
            available_actions: The actions available to this agent.
                              Contains flags for what's possible and valid indices.
        
        Returns:
            An Action object representing the chosen action.
        
        Notes:
            - The agent should ONLY choose from available_actions.get_actions()
            - For AI agents, this should be deterministic given the same state
              (for reproducibility in testing)
            - For human agents, this may block waiting for input
        """
        pass
    
    def on_game_start(self, state: GameState):
        """
        Called when a new game starts.
        
        Override this to initialise any game-specific state.
        
        Args:
            state: The initial game state after dealing.
        """
        pass
    
    def on_game_event(self, event):
        """
        Called when a game event occurs.
        
        Override this to react to events (useful for learning agents).
        
        Args:
            event: A GameEvent object describing what happened.
        """
        pass
    
    def on_game_end(self, state: GameState):
        """
        Called when the game ends.
        
        Override this for post-game analysis or learning.
        
        Args:
            state: The final game state.
        """
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, seat={self.player_index})"


class PassiveAgent(Agent):
    """
    An agent that always passes when possible.
    Useful as a base for simple bots or testing.
    """
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """Always pass if possible, otherwise take first available action."""
        from ..core.game_state import ActionType
        
        actions = available_actions.get_actions()
        
        # Try to pass first
        for action in actions:
            if action.action_type == ActionType.PASS:
                return action
        
        # Otherwise take first action
        if actions:
            return actions[0]
        
        raise ValueError("No actions available!")
