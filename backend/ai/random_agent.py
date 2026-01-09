"""
Random Agent - A simple AI that makes random valid decisions.

This agent is useful for:
- Testing the game engine
- Baseline comparison for smarter AIs
- Filling empty seats quickly
"""

import random
from typing import List

from .agent import Agent
from ..core.game_state import GameState, Action, ActionType, AvailableActions


class RandomAgent(Agent):
    """
    An agent that chooses randomly from available actions.
    
    Behavior:
    - Always takes win if available (Tsumo/Ron)
    - Randomly decides whether to call Pon/Chi/Kan
    - Randomly decides whether to declare Riichi
    - Randomly chooses which tile to discard
    """
    
    def __init__(self, name: str = "Random Bot", call_rate: float = 0.3, riichi_rate: float = 0.8):
        """
        Initialise the random agent.
        
        Args:
            name: Display name.
            call_rate: Probability of calling Pon/Chi/Kan when available (0-1).
            riichi_rate: Probability of declaring Riichi when available (0-1).
        """
        super().__init__(name)
        self.call_rate = call_rate
        self.riichi_rate = riichi_rate
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """Choose a random action from available options."""
        
        # Always take Tsumo if available
        if available_actions.can_tsumo:
            return Action(ActionType.TSUMO, available_actions.player_index)
        
        # Always take Ron if available
        if available_actions.can_ron:
            return Action(ActionType.RON, available_actions.player_index)
        
        # Handle call decisions (Pon/Kan/Chi)
        if available_actions.can_pon or available_actions.can_kan or available_actions.can_chi:
            if random.random() < self.call_rate:
                # Decide what to call (priority: Kan > Pon > Chi)
                if available_actions.can_kan:
                    return Action(ActionType.KAN, available_actions.player_index)
                elif available_actions.can_pon:
                    return Action(ActionType.PON, available_actions.player_index)
                elif available_actions.can_chi:
                    # Random chi option
                    opt = random.choice(available_actions.chi_options)
                    return Action(ActionType.CHI, available_actions.player_index, chi_option=opt.option_index)
            else:
                return Action(ActionType.PASS, available_actions.player_index)
        
        # Handle discard decisions
        if available_actions.can_discard:
            # Consider Riichi
            if available_actions.can_riichi and random.random() < self.riichi_rate:
                # Declare Riichi and discard a valid tile
                idx = random.choice(available_actions.riichi_discard_indices)
                return Action(ActionType.DECLARE_RIICHI, available_actions.player_index, tile_index=idx)
            
            # Random discard
            idx = random.choice(available_actions.discard_indices)
            return Action(ActionType.DISCARD, available_actions.player_index, tile_index=idx)
        
        # Pass if nothing else
        if available_actions.can_pass:
            return Action(ActionType.PASS, available_actions.player_index)
        
        # Fallback - should never reach here
        actions = available_actions.get_actions()
        if actions:
            return random.choice(actions)
        
        raise ValueError("No actions available for RandomAgent!")


class DefensiveRandomAgent(RandomAgent):
    """
    A variant of RandomAgent that plays more defensively.
    
    - Never calls (keeps hand closed)
    - Always declares Riichi when possible
    - Prefers discarding "safe" tiles (honors, terminals)
    """
    
    def __init__(self, name: str = "Defensive Bot"):
        super().__init__(name, call_rate=0.0, riichi_rate=1.0)
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """Choose defensively."""
        
        # Always Tsumo/Ron
        if available_actions.can_tsumo:
            return Action(ActionType.TSUMO, available_actions.player_index)
        if available_actions.can_ron:
            return Action(ActionType.RON, available_actions.player_index)
        
        # Never call
        if available_actions.can_pon or available_actions.can_kan or available_actions.can_chi:
            return Action(ActionType.PASS, available_actions.player_index)
        
        # Discard phase
        if available_actions.can_discard:
            # Always Riichi if possible
            if available_actions.can_riichi:
                idx = random.choice(available_actions.riichi_discard_indices)
                return Action(ActionType.DECLARE_RIICHI, available_actions.player_index, tile_index=idx)
            
            # Prefer discarding safe tiles (honors, terminals)
            player_state = state.get_player(available_actions.player_index)
            hand = player_state.hand
            
            # Find safe tile indices (honors and terminals)
            safe_indices = []
            for i, tile_state in enumerate(hand):
                tile = tile_state.to_tile()
                if tile.is_yaochuu:  # Honor or terminal
                    safe_indices.append(i)
            
            if safe_indices and safe_indices[0] in available_actions.discard_indices:
                idx = random.choice([i for i in safe_indices if i in available_actions.discard_indices])
                return Action(ActionType.DISCARD, available_actions.player_index, tile_index=idx)
            
            # Fallback to random
            idx = random.choice(available_actions.discard_indices)
            return Action(ActionType.DISCARD, available_actions.player_index, tile_index=idx)
        
        # Fallback
        if available_actions.can_pass:
            return Action(ActionType.PASS, available_actions.player_index)
        
        return super().choose_action(state, available_actions)
