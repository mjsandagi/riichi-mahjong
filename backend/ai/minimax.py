"""
Minimax Agent for Riichi Mahjong

This module provides a template for implementing Minimax-based AI.
Note: Pure Minimax is challenging for Mahjong due to:
- Hidden information (opponent hands unknown)
- Chance nodes (tile draws are random)
- Large branching factor

Consider using:
- Expectiminimax (handles chance nodes)
- Alpha-beta pruning (efficiency)
- Determinization (handle hidden info)
- Limited depth with evaluation function

TODO: Implement the following:
1. Game tree search with depth limit
2. Alpha-beta pruning
3. Evaluation function for non-terminal states
4. Chance node handling for draws
"""

import random
from typing import Optional, List, Tuple

from .agent import Agent
from ..core.game_state import GameState, Action, ActionType, AvailableActions
from ..core.game_engine import GameEngine
from ..core.game_state import GamePhase


class MinimaxAgent(Agent):
    """
    Minimax-based agent for Riichi Mahjong.
    
    This is a TEMPLATE implementation using simplified minimax.
    In practice, you'll want to use:
    - Expectiminimax for chance nodes (drawing tiles)
    - Alpha-beta pruning for efficiency
    - Iterative deepening for time management
    
    Usage:
        agent = MinimaxAgent("Minimax Bot", max_depth=3)
        controller.set_agent(0, agent)
    """
    
    def __init__(
        self, 
        name: str = "Minimax Bot",
        max_depth: int = 2
    ):
        """
        Initialize Minimax agent.
        
        Args:
            name: Display name
            max_depth: Maximum search depth (keep low due to branching)
        """
        super().__init__(name)
        self.max_depth = max_depth
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """
        Choose action using minimax search.
        
        For now, uses simple heuristics.
        TODO: Implement full minimax search.
        """
        player_idx = available_actions.player_index
        
        # Always take wins
        if available_actions.can_tsumo:
            return Action(ActionType.TSUMO, player_idx)
        if available_actions.can_ron:
            return Action(ActionType.RON, player_idx)
        
        actions = available_actions.get_actions()
        
        if not actions:
            raise ValueError("No actions available!")
        
        # Use simple evaluation for now
        # TODO: Replace with actual minimax search
        
        if available_actions.can_discard:
            return self._choose_best_discard(state, available_actions)
        
        # Pass on calls by default (keeps hand closed)
        if available_actions.can_pass:
            return Action(ActionType.PASS, player_idx)
        
        return random.choice(actions)
    
    def _choose_best_discard(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """
        Choose the best discard using evaluation.
        
        For each possible discard:
        1. Simulate the discard
        2. Evaluate resulting hand
        3. Choose discard with best evaluation
        """
        player_idx = available_actions.player_index
        player_state = state.get_player(player_idx)
        
        best_action = None
        best_score = float('-inf')
        
        # Try Riichi first if available
        if available_actions.can_riichi:
            # Riichi is usually good when available
            idx = available_actions.riichi_discard_indices[0]
            return Action(ActionType.DECLARE_RIICHI, player_idx, tile_index=idx)
        
        # Evaluate each discard
        for idx in available_actions.discard_indices:
            score = self._evaluate_discard(state, player_idx, idx)
            
            if score > best_score:
                best_score = score
                best_action = Action(ActionType.DISCARD, player_idx, tile_index=idx)
        
        return best_action or Action(ActionType.DISCARD, player_idx, 
                                    tile_index=available_actions.discard_indices[0])
    
    def _evaluate_discard(
        self, 
        state: GameState, 
        player_idx: int, 
        discard_idx: int
    ) -> float:
        """
        Evaluate the result of discarding a specific tile.
        
        Factors to consider:
        - Shanten after discard (lower = better)
        - Safety of discard (likelihood of dealing in)
        - Tile efficiency (ukeire - number of useful draws)
        - Hand value potential
        """
        player_state = state.get_player(player_idx)
        hand = list(player_state.hand)
        
        if discard_idx >= len(hand):
            return float('-inf')
        
        tile_state = hand[discard_idx]
        tile = tile_state.to_tile()
        
        score = 0.0
        
        # Prefer discarding isolated tiles
        # Count neighbors in hand
        neighbor_count = 0
        for i, ts in enumerate(hand):
            if i == discard_idx:
                continue
            t = ts.to_tile()
            if t.suit == tile.suit:
                if not tile.is_honour:
                    if abs(t.value - tile.value) <= 2:
                        neighbor_count += 1
                else:
                    if t.value == tile.value:
                        neighbor_count += 1
        
        # Fewer neighbors = better to discard
        score -= neighbor_count * 10
        
        # Prefer discarding honors (unless we have 2+)
        if tile.is_honour:
            honor_count = sum(1 for ts in hand if ts.suit == tile_state.suit 
                            and ts.value == tile_state.value)
            if honor_count <= 1:
                score += 20  # Good to discard isolated honor
            else:
                score -= 30  # Keep for potential pon
        
        # Prefer discarding terminals
        elif tile.is_terminal:
            score += 10
        
        # Safety consideration (very simplified)
        # In real implementation, check opponents' discards for genbutsu
        # and calculate danger based on riichi declarations
        for i, p in enumerate(state.players):
            if i != player_idx and p.is_riichi:
                # Riichi declared - be more careful
                if tile.is_honour or tile.is_terminal:
                    score += 5  # Safer
                else:
                    score -= 5  # Riskier
        
        return score
    
    def _minimax(
        self, 
        engine: GameEngine, 
        depth: int, 
        player_idx: int,
        alpha: float = float('-inf'),
        beta: float = float('inf'),
        is_maximizing: bool = True
    ) -> Tuple[float, Optional[Action]]:
        """
        Minimax search with alpha-beta pruning.
        
        TODO: Implement full minimax:
        1. Check terminal conditions
        2. If depth 0, return evaluation
        3. Generate all possible actions
        4. Recursively evaluate each action
        5. Return best score and action
        
        Note: Need to handle chance nodes for tile draws.
        """
        # Terminal check
        if engine.is_game_over:
            final_state = engine.get_state()
            return self._evaluate_terminal(final_state, player_idx), None
        
        # Depth limit
        if depth == 0:
            state = engine.get_state()
            return self._evaluate_state(state, player_idx), None
        
        # Get available actions
        state = engine.get_state()
        available = state.available_actions
        
        if not available:
            return 0.0, None
        
        actions = available.get_actions()
        
        if is_maximizing:
            best_score = float('-inf')
            best_action = None
            
            for action in actions:
                # Clone engine and apply action
                child_engine = engine.clone()
                child_engine.apply_action(action)
                
                score, _ = self._minimax(
                    child_engine, depth - 1, player_idx,
                    alpha, beta, False
                )
                
                if score > best_score:
                    best_score = score
                    best_action = action
                
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Pruning
            
            return best_score, best_action
        else:
            best_score = float('inf')
            best_action = None
            
            for action in actions:
                child_engine = engine.clone()
                child_engine.apply_action(action)
                
                score, _ = self._minimax(
                    child_engine, depth - 1, player_idx,
                    alpha, beta, True
                )
                
                if score < best_score:
                    best_score = score
                    best_action = action
                
                beta = min(beta, score)
                if beta <= alpha:
                    break
            
            return best_score, best_action
    
    def _evaluate_terminal(self, state: GameState, player_idx: int) -> float:
        """Evaluate a terminal game state."""
        if state.winner_index == player_idx:
            return 1000.0  # Win
        elif state.winner_index is not None:
            return -1000.0  # Loss
        return 0.0  # Draw
    
    def _evaluate_state(self, state: GameState, player_idx: int) -> float:
        """
        Evaluate a non-terminal game state.
        
        This is a CRITICAL function for minimax performance.
        Consider:
        - Shanten (distance to tenpai)
        - Tile efficiency (ukeire)
        - Hand value potential
        - Safety (likelihood of dealing in)
        - Relative scores
        """
        player = state.get_player(player_idx)
        
        score = 0.0
        
        # Shanten is very important
        score -= player.shanten * 100
        
        # Tenpai bonus
        if player.shanten == 0:
            score += 200
            
            # Riichi bonus
            if player.is_riichi:
                score += 100
            
            # Furiten penalty
            if player.is_furiten:
                score -= 50
        
        # Score advantage
        avg_score = sum(p.score for p in state.players) / 4
        score += (player.score - avg_score) / 100
        
        # Menzen (closed hand) bonus - more yaku potential
        if player.is_menzen:
            score += 30
        
        return score


# Alias
Minimax = MinimaxAgent
