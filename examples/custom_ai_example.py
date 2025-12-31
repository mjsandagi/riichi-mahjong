"""
Example: How to Create a Custom AI Agent

This file demonstrates how to create your own Mahjong AI using the decoupled architecture.
Your AI just needs to implement the `choose_action` method.
"""

import sys
import os
# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai import Agent
from backend.core import (
    GameState, Action, ActionType, AvailableActions,
)
from backend.core.game_controller import GameController


class MySimpleAI(Agent):
    """
    Example AI that demonstrates the interface.
    
    Strategy:
    - Always take wins (Tsumo/Ron)
    - Call Pon on dragons
    - Declare Riichi when possible
    - Discard the tile that keeps shanten lowest
    """
    
    def __init__(self, name: str = "Simple AI"):
        super().__init__(name)
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """
        Main decision method.
        
        Args:
            state: Complete game state snapshot
                - state.players: All player states
                - state.dora_indicators: Dora tiles
                - state.wall_remaining: Tiles left
                - state.get_player(i): Get specific player
                
            available_actions: What actions are legal
                - available_actions.can_tsumo: Can win by self-draw
                - available_actions.can_ron: Can win on discard
                - available_actions.can_pon/chi/kan: Can call
                - available_actions.can_discard: Need to discard
                - available_actions.discard_indices: Valid discard indices
                - available_actions.get_actions(): All valid Action objects
        
        Returns:
            Action object representing the chosen move
        """
        player_idx = available_actions.player_index
        my_state = state.get_player(player_idx)
        
        # === PRIORITY 1: Always take wins ===
        if available_actions.can_tsumo:
            return Action(ActionType.TSUMO, player_idx)
        
        if available_actions.can_ron:
            return Action(ActionType.RON, player_idx)
        
        # === PRIORITY 2: Call decisions ===
        if available_actions.can_pon or available_actions.can_kan:
            # Check if the tile is a dragon (value 5,6,7 in honours)
            if state.last_discard:
                tile = state.last_discard.to_tile()
                from backend.core import Suit
                if tile.suit == Suit.HONOUR and tile.value >= 5:
                    # Call on dragons for Yakuhai
                    if available_actions.can_kan:
                        return Action(ActionType.KAN, player_idx)
                    if available_actions.can_pon:
                        return Action(ActionType.PON, player_idx)
            
            # Otherwise pass
            return Action(ActionType.PASS, player_idx)
        
        if available_actions.can_chi:
            # Generally skip chi (keeps hand closed for riichi)
            return Action(ActionType.PASS, player_idx)
        
        # === PRIORITY 3: Discard decisions ===
        if available_actions.can_discard:
            # Try to declare Riichi if possible
            if available_actions.can_riichi:
                # Take first valid riichi discard
                idx = available_actions.riichi_discard_indices[0]
                return Action(ActionType.DECLARE_RIICHI, player_idx, tile_index=idx)
            
            # Choose best discard (simple heuristic: prefer honors and terminals)
            best_idx = self._choose_best_discard(my_state, available_actions)
            return Action(ActionType.DISCARD, player_idx, tile_index=best_idx)
        
        # === Fallback: Pass ===
        if available_actions.can_pass:
            return Action(ActionType.PASS, player_idx)
        
        # Emergency fallback
        actions = available_actions.get_actions()
        return actions[0] if actions else None
    
    def _choose_best_discard(self, my_state, available_actions) -> int:
        """
        Choose which tile to discard.
        
        Simple heuristic:
        - Prefer isolated honors
        - Prefer isolated terminals
        - Prefer tiles far from sequences
        """
        hand = my_state.hand
        valid_indices = set(available_actions.discard_indices)
        
        # Score each tile (higher = more likely to discard)
        scores = []
        for i, tile_state in enumerate(hand):
            if i not in valid_indices:
                scores.append(-1000)
                continue
            
            tile = tile_state.to_tile()
            score = 0
            
            # Prefer discarding honors (can't form sequences)
            if tile.is_honour:
                # But not if we have 2+ (potential pon)
                count = sum(1 for t in hand if t.suit == tile_state.suit and t.value == tile_state.value)
                if count < 2:
                    score += 50
                else:
                    score -= 20
            
            # Prefer discarding terminals
            elif tile.is_terminal:
                score += 30
            
            # Prefer isolated tiles (no neighbors)
            else:
                has_neighbor = False
                for t in hand:
                    if t.suit == tile_state.suit:
                        if abs(t.value - tile_state.value) <= 2:
                            has_neighbor = True
                            break
                if not has_neighbor:
                    score += 40
            
            scores.append(score)
        
        # Return index of highest score
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        return best_idx


def demo_custom_ai():
    """Run a demo game with the custom AI."""
    from backend.ai import RandomAgent
    
    print("="*50)
    print("Custom AI Demo")
    print("="*50)
    
    controller = GameController(["Custom AI", "Random 1", "Random 2", "Random 3"])
    
    # Use our custom AI for player 0
    controller.set_agent(0, MySimpleAI("My Custom AI"))
    
    # Random bots for others
    for i in range(1, 4):
        controller.set_agent(i, RandomAgent(f"Random {i}"))
    
    # Log events
    def log_event(event):
        if event.player_index == 0:  # Only log custom AI's actions
            print(f"[{event.event_type.name}] {event.message}")
    
    controller.on_event(log_event)
    controller.turn_delay = 0  # Fast game
    
    # Run game
    final_state = controller.run_game()
    
    print("\n" + "="*50)
    print("Game Over!")
    if final_state.winner_index == 0:
        print("Custom AI WINS!")
    elif final_state.winner_index is not None:
        print(f"Player {final_state.winner_index} wins")
    else:
        print("Draw game")
    print("="*50)


if __name__ == "__main__":
    demo_custom_ai()
