"""
Example: Using GameEngine Directly for AI Training

This demonstrates how to use the GameEngine directly without the controller,
which is useful for:
- Training reinforcement learning agents
- Running simulations at maximum speed
- Fine-grained control over the game loop
- Implementing custom game variants
"""

import sys
import os
# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core import (
    GameEngine, GameState, GamePhase,
    Action, ActionType, AvailableActions
)


def run_engine_directly():
    """
    Example of controlling the game engine step by step.
    This is the lowest-level interface for maximum control.
    """
    print("="*50)
    print("Direct Engine Control Example")
    print("="*50)
    
    # Create engine
    engine = GameEngine(["Player 0", "Player 1", "Player 2", "Player 3"])
    
    # Set up event logging (optional)
    def log_event(event):
        print(f"  Event: {event.event_type.name} - {event.message}")
    
    engine.add_event_listener(log_event)
    
    # Initialize the game
    print("\n--- Setting up game ---")
    engine.setup()
    
    turn = 0
    max_turns = 20  # Limit for demo
    
    while not engine.is_game_over and turn < max_turns:
        turn += 1
        print(f"\n--- Turn {turn} ---")
        
        # Advance to decision point (handles drawing)
        if engine.phase == GamePhase.DRAW:
            engine.advance_to_next_decision()
        
        if engine.is_game_over:
            break
        
        # Get current state
        state = engine.get_state()
        available = state.available_actions
        
        if not available:
            continue
        
        print(f"Player {available.player_index}'s decision")
        print(f"Phase: {state.phase.name}")
        
        # Make a decision (simple: always pass or discard first tile)
        action = make_simple_decision(state, available)
        print(f"Action: {action}")
        
        # Apply the action
        engine.apply_action(action)
    
    # Final state
    final = engine.get_state()
    print("\n" + "="*50)
    print("Game ended!")
    print(f"Phase: {final.phase.name}")
    if final.winner_index is not None:
        print(f"Winner: Player {final.winner_index}")
        print(f"Yaku: {final.winning_yaku}")


def make_simple_decision(state: GameState, available: AvailableActions) -> Action:
    """Make a simple decision (for demo purposes)."""
    player_idx = available.player_index
    
    # Take any wins
    if available.can_tsumo:
        return Action(ActionType.TSUMO, player_idx)
    if available.can_ron:
        return Action(ActionType.RON, player_idx)
    
    # Pass on calls
    if available.can_pass and (available.can_pon or available.can_chi or available.can_kan):
        return Action(ActionType.PASS, player_idx)
    
    # Discard first available tile
    if available.can_discard:
        idx = available.discard_indices[0]
        return Action(ActionType.DISCARD, player_idx, tile_index=idx)
    
    # Fallback
    actions = available.get_actions()
    return actions[0]


def training_loop_example():
    """
    Example of a training loop for reinforcement learning.
    
    This shows the pattern you'd use for:
    - Self-play training
    - Experience collection
    - Policy evaluation
    """
    print("\n" + "="*50)
    print("RL Training Loop Example")
    print("="*50)
    
    num_episodes = 5
    
    for episode in range(num_episodes):
        print(f"\n--- Episode {episode + 1} ---")
        
        # Create fresh engine
        engine = GameEngine()
        engine.setup()
        
        # Experience buffer (state, action, reward, next_state)
        experiences = []
        
        while not engine.is_game_over:
            # Advance to decision
            if engine.phase == GamePhase.DRAW:
                engine.advance_to_next_decision()
            
            if engine.is_game_over:
                break
            
            # Get state for current player
            state = engine.get_state()
            available = state.available_actions
            
            if not available:
                continue
            
            player_idx = available.player_index
            
            # Convert state to feature vector (for neural network)
            features = state_to_features(state, player_idx)
            
            # Get action from your policy (placeholder)
            action = make_simple_decision(state, available)
            
            # Apply action
            engine.apply_action(action)
            
            # Get next state
            next_state = engine.get_state()
            
            # Calculate immediate reward (0 for most actions)
            reward = 0
            if engine.is_game_over:
                if next_state.winner_index == player_idx:
                    reward = 1.0  # Win
                elif next_state.winner_index is not None:
                    reward = -0.5  # Loss to another player
                # Draw = 0
            
            # Store experience
            experiences.append({
                'state': features,
                'action': action,
                'reward': reward,
                'player': player_idx
            })
        
        # After episode, you would:
        # 1. Calculate returns/advantages
        # 2. Update policy network
        # 3. Log statistics
        
        final = engine.get_state()
        winner = final.winner_index if final.winner_index is not None else "Draw"
        print(f"  Result: Winner = {winner}, Experiences: {len(experiences)}")


def state_to_features(state: GameState, player_idx: int) -> dict:
    """
    Convert game state to feature dictionary for ML.
    
    In a real implementation, you'd convert this to tensors.
    """
    player = state.get_player(player_idx)
    
    # Example features (expand for real use)
    return {
        'turn': state.turn_count,
        'wall_remaining': state.wall_remaining,
        'hand_size': player.hand_size,
        'shanten': player.shanten,
        'is_riichi': player.is_riichi,
        'is_furiten': player.is_furiten,
        'score': player.score,
        # Add: hand tiles as one-hot, discards, dora, etc.
    }


def clone_for_simulation():
    """
    Example of cloning the engine for lookahead/simulation.
    
    Useful for Monte Carlo Tree Search or Minimax.
    """
    print("\n" + "="*50)
    print("Engine Cloning Example (for MCTS/Minimax)")
    print("="*50)
    
    # Create and setup original engine
    engine = GameEngine()
    engine.setup()
    
    # Advance a few turns
    for _ in range(5):
        if engine.phase == GamePhase.DRAW:
            engine.advance_to_next_decision()
        if engine.is_game_over:
            break
        
        state = engine.get_state()
        available = state.available_actions
        if available:
            action = make_simple_decision(state, available)
            engine.apply_action(action)
    
    print(f"Original engine turn: {engine.turn_count}")
    print(f"Original phase: {engine.phase.name}")
    
    # Clone for simulation
    simulated = engine.clone()
    
    # Run simulation on clone (doesn't affect original)
    for _ in range(10):
        if simulated.phase == GamePhase.DRAW:
            simulated.advance_to_next_decision()
        if simulated.is_game_over:
            break
        
        state = simulated.get_state()
        available = state.available_actions
        if available:
            action = make_simple_decision(state, available)
            simulated.apply_action(action)
    
    print(f"\nSimulated engine turn: {simulated.turn_count}")
    print(f"Simulated phase: {simulated.phase.name}")
    
    # Original is unchanged
    print(f"\nOriginal engine turn (unchanged): {engine.turn_count}")
    print(f"Original phase (unchanged): {engine.phase.name}")


if __name__ == "__main__":
    run_engine_directly()
    training_loop_example()
    clone_for_simulation()
