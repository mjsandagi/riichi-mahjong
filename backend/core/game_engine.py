"""
Game Engine Module - Pure game logic for Riichi Mahjong.

This module contains the core game engine with NO I/O operations.
All decisions come from external agents via the Action interface.
All outputs go through GameEvent emissions.

Key design principles:
- Pure functions where possible
- No print statements or console I/O
- No time.sleep or delays
- State changes only through apply_action()
- Fully deterministic given the same Wall seed
"""

import copy
from typing import Callable, Optional

from .tiles import Tile, Suit
from .wall import Wall
from .player import Player
from .shanten import ShantenCalculator
from .scorer import Scorer
from .game_state import (
    GameState, GamePhase, GameEvent, GameEventType,
    Action, ActionType, AvailableActions,
    PlayerState, TileState, ChiOption,
    tiles_to_state, create_player_state
)


class GameEngine:
    """
    Pure game engine for Riichi Mahjong.
    
    This engine:
    - Manages all game state
    - Validates and applies actions
    - Emits events for UI/logging
    - Can be cloned for AI simulation
    
    Usage:
        engine = GameEngine()
        engine.setup()
        
        while not engine.is_game_over:
            state = engine.get_state()
            # Get action from agent
            action = agent.choose_action(state)
            events = engine.apply_action(action)
            # Handle events (UI updates, etc.)
    """
    
    def __init__(self, player_names: list = None):
        """
        Initialise the game engine.
        
        Args:
            player_names: List of 4 player names. Defaults to wind names.
        """
        if player_names is None:
            player_names = ["East", "South", "West", "North"]
        
        assert len(player_names) == 4, "Must have exactly 4 players"
        
        self.wall = Wall()
        self.players = [Player(name) for name in player_names]
        self.shanten_calc = ShantenCalculator()
        self.scorer = Scorer()
        
        # Game state
        self.turn_count = 0
        self.active_player_index = 0
        self.phase = GamePhase.SETUP
        
        # Turn state
        self._skip_draw = False         # Skip draw after calling Pon/Chi/Kan
        self._last_discard = None       # The tile that was just discarded
        self._last_discard_player = None  # Who discarded it
        self._drawn_tile = None         # The tile just drawn
        
        # Call checking state
        self._pending_calls = {}        # player_index -> AvailableActions for call checking
        self._call_responses = {}       # player_index -> Action (PASS or call)
        
        # Win state
        self._winner_index = None
        self._winning_yaku = []
        
        # Event listeners
        self._event_listeners: list[Callable[[GameEvent], None]] = []
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def add_event_listener(self, listener: Callable[[GameEvent], None]):
        """Register a callback to receive game events."""
        self._event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable[[GameEvent], None]):
        """Unregister an event listener."""
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)
    
    def _emit_event(self, event: GameEvent):
        """Emit an event to all listeners."""
        for listener in self._event_listeners:
            listener(event)
    
    @property
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.phase in (GamePhase.GAME_OVER_WIN, GamePhase.GAME_OVER_DRAW)
    
    def setup(self) -> list[GameEvent]:
        """
        Initialise the game: shuffle wall, deal tiles, set up dora.
        
        Returns:
            List of GameEvents that occurred during setup.
        """
        events = []
        
        # Deal 13 tiles to each player
        for _ in range(13):
            for p in self.players:
                tile = self.wall.draw()
                p.draw_tile(tile)
        
        # Sort all hands
        for p in self.players:
            p.sort_hand()
        
        self.turn_count = 0
        self.active_player_index = 0
        self.phase = GamePhase.DRAW
        
        events.append(GameEvent(
            event_type=GameEventType.GAME_STARTED,
            message="Game started. Deal complete.",
            data={
                "dora_indicators": tiles_to_state(self.wall.dora_indicators),
                "wall_remaining": self.wall.remaining
            }
        ))
        
        for event in events:
            self._emit_event(event)
        
        return events
    
    def get_state(self, for_player: int = None) -> GameState:
        """
        Get the current game state.
        
        Args:
            for_player: If specified, hide other players' hands (for fair AI).
                       If None, include all information (for simulation/debug).
        
        Returns:
            Immutable GameState snapshot.
        """
        # Build player states
        player_states = []
        for i, p in enumerate(self.players):
            # Include hand only for the requesting player or if for_player is None
            include_hand = (for_player is None) or (i == for_player)
            player_states.append(create_player_state(
                p, i, self.shanten_calc, include_hand=include_hand
            ))
        
        # Build available actions for current decision point
        available_actions = self._get_available_actions()
        
        return GameState(
            turn_count=self.turn_count,
            phase=self.phase,
            active_player_index=self.active_player_index,
            players=tuple(player_states),
            wall_remaining=self.wall.remaining,
            dora_indicators=tiles_to_state(self.wall.dora_indicators),
            last_discard=TileState.from_tile(self._last_discard) if self._last_discard else None,
            last_discard_player=self._last_discard_player,
            drawn_tile=TileState.from_tile(self._drawn_tile) if self._drawn_tile else None,
            available_actions=available_actions,
            winner_index=self._winner_index,
            winning_yaku=tuple(self._winning_yaku)
        )
    
    def apply_action(self, action: Action) -> list[GameEvent]:
        """
        Apply an action to the game state.
        
        Args:
            action: The action to apply.
        
        Returns:
            List of GameEvents that occurred.
        
        Raises:
            ValueError: If the action is invalid for the current state.
        """
        events = []
        
        # Validate action
        available = self._get_available_actions()
        valid_actions = available.get_actions() if available else []
        
        # Check if action is in valid actions (simplified check)
        if not self._is_action_valid(action, valid_actions):
            raise ValueError(f"Invalid action {action} for current state. "
                           f"Valid actions: {valid_actions}")
        
        # Apply based on action type
        if action.action_type == ActionType.DISCARD:
            events.extend(self._apply_discard(action))
        
        elif action.action_type == ActionType.DECLARE_RIICHI:
            events.extend(self._apply_riichi(action))
        
        elif action.action_type == ActionType.TSUMO:
            events.extend(self._apply_tsumo(action))
        
        elif action.action_type == ActionType.RON:
            events.extend(self._apply_ron(action))
        
        elif action.action_type == ActionType.PON:
            events.extend(self._apply_pon(action))
        
        elif action.action_type == ActionType.KAN:
            events.extend(self._apply_kan(action))
        
        elif action.action_type == ActionType.CHI:
            events.extend(self._apply_chi(action))
        
        elif action.action_type == ActionType.PASS:
            events.extend(self._apply_pass(action))
        
        # Emit events
        for event in events:
            self._emit_event(event)
        
        return events
    
    def clone(self) -> 'GameEngine':
        """
        Create a deep copy of the engine for simulation.
        Useful for AI lookahead without affecting real game state.
        
        Returns:
            A new GameEngine with identical state.
        """
        return copy.deepcopy(self)
    
    def advance_to_next_decision(self) -> list[GameEvent]:
        """
        Advance the game state to the next decision point.
        Handles automatic phases like drawing tiles.
        
        Returns:
            List of GameEvents that occurred.
        """
        events = []
        
        if self.phase == GamePhase.DRAW:
            events.extend(self._do_draw_phase())
        
        return events
    
    # =========================================================================
    # INTERNAL: State Queries
    # =========================================================================
    
    def _get_available_actions(self) -> Optional[AvailableActions]:
        """Determine what actions are available in the current phase."""
        
        if self.phase == GamePhase.DISCARD:
            return self._get_discard_actions()
        
        elif self.phase == GamePhase.CALL_FOR_WIN:
            return self._get_call_for_win_actions()
        
        elif self.phase == GamePhase.CALL_FOR_MELD:
            return self._get_call_for_meld_actions()
        
        return None
    
    def _get_discard_actions(self) -> AvailableActions:
        """Get available actions during discard phase."""
        player = self.players[self.active_player_index]
        
        actions = AvailableActions(
            player_index=self.active_player_index,
            phase=GamePhase.DISCARD,
            can_discard=True,
            discard_indices=tuple(range(len(player.hand)))
        )
        
        # Check for Tsumo (win on self-draw)
        if self.shanten_calc.calculate_shanten(player.hand) == -1:
            yaku = self.scorer.check_yaku(player.hand, player.open_melds, is_riichi=player.is_riichi)
            if yaku:
                actions.can_tsumo = True
                actions.tsumo_yaku = tuple(yaku)
        
        # Check for Riichi opportunity
        if not player.is_riichi and player.is_menzen and player.score >= 1000:
            if self.shanten_calc.calculate_shanten(player.hand) == 0:
                # Find which discards keep tenpai
                riichi_discards = []
                for i in range(len(player.hand)):
                    # Simulate discard
                    test_hand = player.hand[:i] + player.hand[i+1:]
                    if self.shanten_calc.calculate_shanten(test_hand) == 0:
                        riichi_discards.append(i)
                
                if riichi_discards:
                    actions.can_riichi = True
                    actions.riichi_discard_indices = tuple(riichi_discards)
        
        # If in Riichi, can only discard drawn tile
        if player.is_riichi:
            actions.discard_indices = (len(player.hand) - 1,)
            actions.can_riichi = False
        
        return actions
    
    def _get_call_for_win_actions(self) -> Optional[AvailableActions]:
        """Get Ron actions for players who can win on the discard."""
        if not self._last_discard:
            return None
        
        # Check each player (except discarder) for Ron
        for i, p in enumerate(self.players):
            if i == self._last_discard_player:
                continue
            
            # Check if this player can Ron
            test_hand = p.hand + [self._last_discard]
            if self.shanten_calc.calculate_shanten(test_hand) == -1:
                # Check Furiten
                waits = self.shanten_calc.get_waits(p.hand)
                wait_ids = set((w.suit, w.value) for w in waits)
                discard_ids = set((t.suit, t.value) for t in p.discards)
                
                if wait_ids.isdisjoint(discard_ids):  # Not furiten
                    yaku = self.scorer.check_yaku(test_hand, p.open_melds, is_riichi=p.is_riichi)
                    if yaku:
                        return AvailableActions(
                            player_index=i,
                            phase=GamePhase.CALL_FOR_WIN,
                            can_ron=True,
                            ron_yaku=tuple(yaku),
                            can_pass=True
                        )
        
        return None
    
    def _get_call_for_meld_actions(self) -> Optional[AvailableActions]:
        """Get Pon/Kan/Chi actions for players."""
        if not self._last_discard:
            return None
        
        # Priority: Pon/Kan > Chi (Pon/Kan can be called by anyone, Chi only by next player)
        
        # Check Pon/Kan for all players except discarder
        for i, p in enumerate(self.players):
            if i == self._last_discard_player:
                continue
            if p.is_riichi:  # Can't call when in Riichi
                continue
            
            can_kan = p.can_kan(self._last_discard)
            can_pon = p.can_pon(self._last_discard)
            
            if can_kan or can_pon:
                return AvailableActions(
                    player_index=i,
                    phase=GamePhase.CALL_FOR_MELD,
                    can_pon=can_pon,
                    can_kan=can_kan,
                    can_pass=True
                )
        
        # Check Chi for next player only
        next_player_idx = (self._last_discard_player + 1) % 4
        next_player = self.players[next_player_idx]
        
        if not next_player.is_riichi:
            chi_options = next_player.can_chi(self._last_discard)
            if chi_options:
                chi_option_states = []
                for opt_idx, (idx1, idx2) in enumerate(chi_options):
                    t1 = next_player.hand[idx1]
                    t2 = next_player.hand[idx2]
                    resulting = sorted([t1, t2, self._last_discard])
                    chi_option_states.append(ChiOption(
                        option_index=opt_idx,
                        tile_indices=(idx1, idx2),
                        resulting_tiles=tiles_to_state(resulting)
                    ))
                
                return AvailableActions(
                    player_index=next_player_idx,
                    phase=GamePhase.CALL_FOR_MELD,
                    can_chi=True,
                    chi_options=tuple(chi_option_states),
                    can_pass=True
                )
        
        return None
    
    def _is_action_valid(self, action: Action, valid_actions: list[Action]) -> bool:
        """Check if an action matches one of the valid actions."""
        for valid in valid_actions:
            if (action.action_type == valid.action_type and 
                action.player_index == valid.player_index):
                # For actions with indices, check those too
                if action.action_type == ActionType.DISCARD:
                    if action.tile_index == valid.tile_index:
                        return True
                elif action.action_type == ActionType.DECLARE_RIICHI:
                    if action.tile_index == valid.tile_index:
                        return True
                elif action.action_type == ActionType.CHI:
                    if action.chi_option == valid.chi_option:
                        return True
                else:
                    return True
        return False
    
    # =========================================================================
    # INTERNAL: Action Implementations
    # =========================================================================
    
    def _do_draw_phase(self) -> list[GameEvent]:
        """Execute the draw phase."""
        events = []
        player = self.players[self.active_player_index]
        
        self.turn_count += 1
        
        if self._skip_draw:
            self._skip_draw = False
            self.phase = GamePhase.DISCARD
            return events
        
        # Draw a tile
        drawn_tile = self.wall.draw()
        
        if not drawn_tile:
            # Wall empty - exhaustive draw
            self.phase = GamePhase.GAME_OVER_DRAW
            events.append(GameEvent(
                event_type=GameEventType.EXHAUSTIVE_DRAW,
                message="Wall empty! Ryuukyoku (Exhaustive Draw)"
            ))
            return events
        
        self._drawn_tile = drawn_tile
        player.draw_tile(drawn_tile)
        
        events.append(GameEvent(
            event_type=GameEventType.TILE_DRAWN,
            player_index=self.active_player_index,
            tile=TileState.from_tile(drawn_tile),
            message=f"{player.name} draws a tile"
        ))
        
        # Check for automatic Tsumo (complete hand with yaku)
        self.phase = GamePhase.DISCARD
        
        return events
    
    def _apply_discard(self, action: Action) -> list[GameEvent]:
        """Apply a discard action."""
        events = []
        player = self.players[action.player_index]
        
        discarded = player.discard_tile(action.tile_index)
        self._last_discard = discarded
        self._last_discard_player = action.player_index
        self._drawn_tile = None
        
        events.append(GameEvent(
            event_type=GameEventType.TILE_DISCARDED,
            player_index=action.player_index,
            tile=TileState.from_tile(discarded),
            message=f"{player.name} discards {discarded}"
        ))
        
        # Move to call checking phase
        self.phase = GamePhase.CALL_FOR_WIN
        
        # If no one can win, check for meld calls
        if not self._get_call_for_win_actions():
            self.phase = GamePhase.CALL_FOR_MELD
            
            # If no one can call, advance turn
            if not self._get_call_for_meld_actions():
                self._advance_turn()
                events.append(GameEvent(
                    event_type=GameEventType.TURN_CHANGED,
                    player_index=self.active_player_index,
                    message=f"Turn passes to {self.players[self.active_player_index].name}"
                ))
        
        return events
    
    def _apply_riichi(self, action: Action) -> list[GameEvent]:
        """Apply a Riichi declaration."""
        events = []
        player = self.players[action.player_index]
        
        # Declare Riichi
        player.is_riichi = True
        player.score -= 1000
        
        events.append(GameEvent(
            event_type=GameEventType.RIICHI_DECLARED,
            player_index=action.player_index,
            message=f"{player.name} declares RIICHI!"
        ))
        
        # Then discard
        discarded = player.discard_tile(action.tile_index)
        self._last_discard = discarded
        self._last_discard_player = action.player_index
        self._drawn_tile = None
        
        events.append(GameEvent(
            event_type=GameEventType.TILE_DISCARDED,
            player_index=action.player_index,
            tile=TileState.from_tile(discarded),
            message=f"{player.name} discards {discarded}"
        ))
        
        # Move to call checking
        self.phase = GamePhase.CALL_FOR_WIN
        if not self._get_call_for_win_actions():
            self.phase = GamePhase.CALL_FOR_MELD
            if not self._get_call_for_meld_actions():
                self._advance_turn()
        
        return events
    
    def _apply_tsumo(self, action: Action) -> list[GameEvent]:
        """Apply a Tsumo (self-draw win)."""
        events = []
        player = self.players[action.player_index]
        
        yaku = self.scorer.check_yaku(player.hand, player.open_melds, is_riichi=player.is_riichi)
        
        self._winner_index = action.player_index
        self._winning_yaku = yaku
        self.phase = GamePhase.GAME_OVER_WIN
        
        events.append(GameEvent(
            event_type=GameEventType.TSUMO_WIN,
            player_index=action.player_index,
            yaku=tuple(yaku),
            message=f"TSUMO! {player.name} wins!"
        ))
        
        return events
    
    def _apply_ron(self, action: Action) -> list[GameEvent]:
        """Apply a Ron (win on discard)."""
        events = []
        player = self.players[action.player_index]
        
        # Add the discarded tile to complete the hand
        winning_hand = player.hand + [self._last_discard]
        yaku = self.scorer.check_yaku(winning_hand, player.open_melds, is_riichi=player.is_riichi)
        
        self._winner_index = action.player_index
        self._winning_yaku = yaku
        self.phase = GamePhase.GAME_OVER_WIN
        
        loser = self.players[self._last_discard_player]
        
        events.append(GameEvent(
            event_type=GameEventType.RON_WIN,
            player_index=action.player_index,
            tile=TileState.from_tile(self._last_discard),
            yaku=tuple(yaku),
            message=f"RON! {player.name} wins on {loser.name}'s {self._last_discard}!",
            data={"deal_in_player": self._last_discard_player}
        ))
        
        return events
    
    def _apply_pon(self, action: Action) -> list[GameEvent]:
        """Apply a Pon call."""
        events = []
        player = self.players[action.player_index]
        
        player.execute_pon(self._last_discard)
        
        events.append(GameEvent(
            event_type=GameEventType.PON_CALLED,
            player_index=action.player_index,
            tile=TileState.from_tile(self._last_discard),
            message=f"{player.name} calls PON!"
        ))
        
        # Turn moves to caller, skip draw
        self.active_player_index = action.player_index
        self._skip_draw = True
        self._last_discard = None
        self._last_discard_player = None
        self.phase = GamePhase.DISCARD
        
        return events
    
    def _apply_kan(self, action: Action) -> list[GameEvent]:
        """Apply a Kan call (Daiminkan)."""
        events = []
        player = self.players[action.player_index]
        
        player.execute_kan(self._last_discard)
        
        events.append(GameEvent(
            event_type=GameEventType.KAN_CALLED,
            player_index=action.player_index,
            tile=TileState.from_tile(self._last_discard),
            message=f"{player.name} calls KAN!"
        ))
        
        # Draw replacement tile
        replacement = self.wall.draw_replacement()
        if replacement:
            player.draw_tile(replacement)
            self._drawn_tile = replacement
            
            events.append(GameEvent(
                event_type=GameEventType.REPLACEMENT_DRAWN,
                player_index=action.player_index,
                tile=TileState.from_tile(replacement),
                message=f"{player.name} draws replacement tile"
            ))
        
        # Reveal new dora
        self.wall.reveal_kan_dora()
        new_dora = self.wall.dora_indicators[-1]
        
        events.append(GameEvent(
            event_type=GameEventType.DORA_REVEALED,
            tile=TileState.from_tile(new_dora),
            message=f"New Dora Indicator: {new_dora}"
        ))
        
        # Turn moves to caller, skip draw (already drew replacement)
        self.active_player_index = action.player_index
        self._skip_draw = True
        self._last_discard = None
        self._last_discard_player = None
        self.phase = GamePhase.DISCARD
        
        return events
    
    def _apply_chi(self, action: Action) -> list[GameEvent]:
        """Apply a Chi call."""
        events = []
        player = self.players[action.player_index]
        
        # Get the chi option
        chi_options = player.can_chi(self._last_discard)
        chosen_indices = chi_options[action.chi_option]
        
        player.execute_chi(self._last_discard, chosen_indices)
        
        events.append(GameEvent(
            event_type=GameEventType.CHI_CALLED,
            player_index=action.player_index,
            tile=TileState.from_tile(self._last_discard),
            message=f"{player.name} calls CHI!"
        ))
        
        # Turn moves to caller, skip draw
        self.active_player_index = action.player_index
        self._skip_draw = True
        self._last_discard = None
        self._last_discard_player = None
        self.phase = GamePhase.DISCARD
        
        return events
    
    def _apply_pass(self, action: Action) -> list[GameEvent]:
        """Apply a pass (decline to call)."""
        events = []
        
        # Check if we were in win phase or meld phase
        if self.phase == GamePhase.CALL_FOR_WIN:
            # Move to meld checking
            self.phase = GamePhase.CALL_FOR_MELD
            
            if not self._get_call_for_meld_actions():
                self._advance_turn()
                events.append(GameEvent(
                    event_type=GameEventType.TURN_CHANGED,
                    player_index=self.active_player_index
                ))
        
        elif self.phase == GamePhase.CALL_FOR_MELD:
            # Advance turn
            self._advance_turn()
            events.append(GameEvent(
                event_type=GameEventType.TURN_CHANGED,
                player_index=self.active_player_index
            ))
        
        return events
    
    def _advance_turn(self):
        """Move to the next player's turn."""
        self.active_player_index = (self.active_player_index + 1) % 4
        self._last_discard = None
        self._last_discard_player = None
        self.phase = GamePhase.DRAW
