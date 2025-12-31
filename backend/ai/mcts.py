"""
Monte Carlo Tree Search (MCTS) Agent for Riichi Mahjong

This module provides a template for implementing MCTS-based AI.
MCTS is well-suited for Mahjong because:
- Large branching factor (many possible discards)
- Hidden information (can use determinization)
- Complex evaluation (hard to write heuristics)

TODO: Implement the following:
1. Node class for tree representation
2. Selection policy (UCB1)
3. Expansion logic
4. Simulation (rollout) policy
5. Backpropagation
"""

import random
import math
from typing import Optional, List, Dict
from dataclasses import dataclass, field

from .agent import Agent
from ..core.game_state import GameState, Action, ActionType, AvailableActions
from ..core.game_engine import GameEngine
from ..core.game_state import GamePhase


@dataclass
class MCTSNode:
    """
    Node in the MCTS tree.
    
    Each node represents a game state after taking an action.
    """
    action: Optional[Action] = None     # Action that led to this node
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = field(default_factory=list)
    
    visits: int = 0
    total_reward: float = 0.0
    
    # Untried actions from this state
    untried_actions: List[Action] = field(default_factory=list)
    
    @property
    def ucb1(self) -> float:
        """Calculate UCB1 value for selection."""
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.total_reward / self.visits
        exploration = math.sqrt(2 * math.log(self.parent.visits) / self.visits)
        
        return exploitation + exploration
    
    @property
    def is_fully_expanded(self) -> bool:
        """Check if all children have been tried."""
        return len(self.untried_actions) == 0
    
    def best_child(self, exploration_weight: float = 1.414) -> 'MCTSNode':
        """Select best child using UCB1."""
        return max(self.children, key=lambda c: c.ucb1)
    
    def add_child(self, action: Action) -> 'MCTSNode':
        """Add a child node for an action."""
        child = MCTSNode(action=action, parent=self)
        self.children.append(child)
        self.untried_actions.remove(action)
        return child


class MCTSAgent(Agent):
    """
    Monte Carlo Tree Search agent for Riichi Mahjong.
    
    This is a TEMPLATE implementation. Key areas to customize:
    1. Determinization strategy for hidden information
    2. Simulation policy (random vs. heuristic)
    3. Evaluation function for terminal states
    4. Time/iteration budget
    
    Usage:
        agent = MCTSAgent("MCTS Bot", iterations=1000)
        controller.set_agent(0, agent)
    """
    
    def __init__(
        self, 
        name: str = "MCTS Bot",
        iterations: int = 100,
        exploration_weight: float = 1.414,
        simulation_depth: int = 50
    ):
        """
        Initialize MCTS agent.
        
        Args:
            name: Display name
            iterations: Number of MCTS iterations per decision
            exploration_weight: UCB1 exploration constant
            simulation_depth: Max depth for simulations
        """
        super().__init__(name)
        self.iterations = iterations
        self.exploration_weight = exploration_weight
        self.simulation_depth = simulation_depth
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """
        Choose action using MCTS.
        
        For now, falls back to simple heuristics.
        TODO: Implement full MCTS search.
        """
        player_idx = available_actions.player_index
        
        # Always take wins
        if available_actions.can_tsumo:
            return Action(ActionType.TSUMO, player_idx)
        if available_actions.can_ron:
            return Action(ActionType.RON, player_idx)
        
        # Get all valid actions
        actions = available_actions.get_actions()
        
        if not actions:
            raise ValueError("No actions available!")
        
        # TODO: Run MCTS search
        # For now, use simple heuristic or random
        
        # If we can riichi, do it
        if available_actions.can_riichi:
            for action in actions:
                if action.action_type == ActionType.DECLARE_RIICHI:
                    return action
        
        # Skip calls (keep hand closed)
        if available_actions.can_pass:
            for action in actions:
                if action.action_type == ActionType.PASS:
                    return action
        
        # Random discard from valid options
        discard_actions = [a for a in actions if a.action_type == ActionType.DISCARD]
        if discard_actions:
            return random.choice(discard_actions)
        
        return random.choice(actions)
    
    def _run_mcts(
        self, 
        root_engine: GameEngine,
        player_idx: int,
        available_actions: AvailableActions
    ) -> Action:
        """
        Run MCTS search and return best action.
        
        TODO: Implement this method with:
        1. Create root node with available actions
        2. For each iteration:
           a. Selection: traverse tree using UCB1
           b. Expansion: add new child node
           c. Simulation: play random game to end
           d. Backpropagation: update node statistics
        3. Return action with highest visit count
        """
        # Placeholder
        actions = available_actions.get_actions()
        return random.choice(actions) if actions else None
    
    def _determinize(self, engine: GameEngine, player_idx: int) -> GameEngine:
        """
        Create a determinized copy of the game.
        
        Since Mahjong has hidden information (other players' hands),
        we need to sample possible configurations.
        
        TODO: Implement determinization:
        1. Clone the engine
        2. Randomly distribute unknown tiles to other players
        3. This creates a "possible world" to simulate
        """
        # For now, just clone (assumes perfect information)
        return engine.clone()
    
    def _simulate(self, engine: GameEngine, player_idx: int) -> float:
        """
        Run a simulation (rollout) from current state.
        
        TODO: Implement simulation policy:
        1. Play random/heuristic moves until game ends
        2. Return reward from player's perspective
        
        Returns:
            Reward value (e.g., 1.0 for win, 0.0 for draw, -1.0 for loss)
        """
        depth = 0
        
        while not engine.is_game_over and depth < self.simulation_depth:
            # Advance to decision
            if engine.phase == GamePhase.DRAW:
                engine.advance_to_next_decision()
            
            if engine.is_game_over:
                break
            
            # Get available actions
            state = engine.get_state()
            available = state.available_actions
            
            if not available:
                break
            
            # Random action
            actions = available.get_actions()
            if actions:
                action = random.choice(actions)
                engine.apply_action(action)
            
            depth += 1
        
        # Evaluate final state
        final_state = engine.get_state()
        return self._evaluate(final_state, player_idx)
    
    def _evaluate(self, state: GameState, player_idx: int) -> float:
        """
        Evaluate a terminal state from player's perspective.
        
        Returns:
            Reward value
        """
        if state.winner_index == player_idx:
            return 1.0  # Win
        elif state.winner_index is not None:
            return -0.5  # Someone else won
        else:
            return 0.0  # Draw


# Alias for convenience
MCTS = MCTSAgent
