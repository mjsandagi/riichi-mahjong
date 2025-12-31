"""
Game State Module - Immutable snapshots and action definitions for Riichi Mahjong.

This module provides serializable representations of game state that can be:
- Passed to AI agents for decision making
- Sent to frontend clients via WebSocket
- Used for game replay and analysis
- Cloned for simulation without affecting real game state
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import copy

from .tiles import Tile, Suit


# =============================================================================
# ENUMS - Game Phases and Action Types
# =============================================================================

class GamePhase(Enum):
    """
    Represents the current phase of the game turn.
    Used to determine what actions are valid.
    """
    SETUP = auto()              # Game not yet started
    DRAW = auto()               # Active player needs to draw (or skip if called)
    DISCARD = auto()            # Active player needs to discard a tile
    CALL_FOR_WIN = auto()       # Check if anyone can Ron on the discard
    CALL_FOR_MELD = auto()      # Check if anyone can Pon/Kan/Chi on the discard
    GAME_OVER_WIN = auto()      # Game ended with a winner
    GAME_OVER_DRAW = auto()     # Game ended in exhaustive draw (Ryuukyoku)


class ActionType(Enum):
    """All possible actions a player can take."""
    # Discard Phase Actions
    DISCARD = auto()            # Discard a tile from hand
    DECLARE_RIICHI = auto()     # Declare Riichi (must discard after)
    TSUMO = auto()              # Win by self-draw
    
    # Call Phase Actions (responding to a discard)
    RON = auto()                # Win on opponent's discard
    PON = auto()                # Call Pon (triplet)
    KAN = auto()                # Call Kan (quad) - Daiminkan
    CHI = auto()                # Call Chi (sequence) - only from left player
    PASS = auto()               # Decline to call


class GameEventType(Enum):
    """Types of events that occur during the game (for UI/logging)."""
    GAME_STARTED = auto()
    TILE_DRAWN = auto()
    TILE_DISCARDED = auto()
    RIICHI_DECLARED = auto()
    PON_CALLED = auto()
    CHI_CALLED = auto()
    KAN_CALLED = auto()
    REPLACEMENT_DRAWN = auto()
    DORA_REVEALED = auto()
    TSUMO_WIN = auto()
    RON_WIN = auto()
    EXHAUSTIVE_DRAW = auto()
    TURN_CHANGED = auto()


# =============================================================================
# DATA CLASSES - Immutable State Representations
# =============================================================================

@dataclass(frozen=True)
class TileState:
    """
    Immutable representation of a tile for serialization.
    Can be converted to/from Tile objects.
    """
    suit: int       # Suit enum value
    value: int      # 1-9 for suits, 1-7 for honours
    is_red: bool    # Red dora flag
    
    @classmethod
    def from_tile(cls, tile: Tile) -> 'TileState':
        """Create TileState from a Tile object."""
        return cls(suit=int(tile.suit), value=tile.value, is_red=tile.is_red)
    
    def to_tile(self) -> Tile:
        """Convert back to a Tile object."""
        return Tile(Suit(self.suit), self.value, self.is_red)
    
    def __repr__(self):
        return repr(self.to_tile())


@dataclass(frozen=True)
class MeldState:
    """
    Represents an open meld (Pon, Chi, or Kan).
    """
    meld_type: str              # "pon", "chi", "kan"
    tiles: tuple                # Tuple of TileState
    called_from: int            # Player index the tile was called from
    
    @classmethod
    def from_string(cls, meld_str: str, called_from: int = -1) -> 'MeldState':
        """
        Parse existing string-based meld format.
        e.g. "[Pon: 5m 5m 5m]" -> MeldState
        """
        # This is a temporary parser for backwards compatibility
        if "Pon:" in meld_str:
            return cls(meld_type="pon", tiles=(), called_from=called_from)
        elif "Chi:" in meld_str:
            return cls(meld_type="chi", tiles=(), called_from=called_from)
        elif "Kan:" in meld_str:
            return cls(meld_type="kan", tiles=(), called_from=called_from)
        return cls(meld_type="unknown", tiles=(), called_from=called_from)


@dataclass(frozen=True)
class PlayerState:
    """
    Immutable snapshot of a player's state.
    Contains all information visible to that player.
    """
    index: int                              # Player seat (0=East, 1=South, etc.)
    name: str                               # Player name
    score: int                              # Current score
    is_riichi: bool                         # In Riichi state
    is_menzen: bool                         # Closed hand (no open melds)
    hand: tuple                             # Tuple of TileState (own hand only)
    hand_size: int                          # Number of tiles in hand (for other players)
    discards: tuple                         # Tuple of TileState (river/kawa)
    open_melds: tuple                       # Tuple of meld strings (temporary)
    shanten: int                            # Shanten count (-1 = complete)
    waits: tuple                            # Tuple of TileState (waiting tiles if tenpai)
    is_furiten: bool                        # Furiten status


@dataclass(frozen=True)
class ChiOption:
    """Represents a Chi option with the hand indices to use."""
    option_index: int           # Index in the chi_options list
    tile_indices: tuple         # Tuple of 2 indices from hand
    resulting_tiles: tuple      # The 3 tiles that form the sequence (TileState)


@dataclass(frozen=True)
class Action:
    """
    Represents an action a player can take.
    This is what agents return as their decision.
    """
    action_type: ActionType
    player_index: int                       # Who is taking the action
    tile_index: Optional[int] = None        # For DISCARD: which tile to discard
    chi_option: Optional[int] = None        # For CHI: which chi option to use
    
    def __repr__(self):
        parts = [f"{self.action_type.name}"]
        if self.tile_index is not None:
            parts.append(f"tile_idx={self.tile_index}")
        if self.chi_option is not None:
            parts.append(f"chi_opt={self.chi_option}")
        return f"Action({', '.join(parts)})"


@dataclass
class AvailableActions:
    """
    Container for all actions available to a player at a decision point.
    """
    player_index: int
    phase: GamePhase
    
    # Discard phase options
    can_discard: bool = False
    discard_indices: tuple = ()             # Valid indices to discard
    
    can_riichi: bool = False
    riichi_discard_indices: tuple = ()      # Tiles that keep tenpai after riichi
    
    can_tsumo: bool = False
    tsumo_yaku: tuple = ()                  # Yaku if tsumo is valid
    
    # Call phase options (responding to discard)
    can_ron: bool = False
    ron_yaku: tuple = ()                    # Yaku if ron is valid
    
    can_pon: bool = False
    can_kan: bool = False
    
    can_chi: bool = False
    chi_options: tuple = ()                 # Tuple of ChiOption
    
    can_pass: bool = False                  # Can decline to call
    
    def get_actions(self) -> list:
        """Returns a list of all valid Action objects."""
        actions = []
        
        if self.can_tsumo:
            actions.append(Action(ActionType.TSUMO, self.player_index))
        
        if self.can_ron:
            actions.append(Action(ActionType.RON, self.player_index))
        
        if self.can_riichi:
            for idx in self.riichi_discard_indices:
                actions.append(Action(ActionType.DECLARE_RIICHI, self.player_index, tile_index=idx))
        
        if self.can_discard:
            for idx in self.discard_indices:
                actions.append(Action(ActionType.DISCARD, self.player_index, tile_index=idx))
        
        if self.can_pon:
            actions.append(Action(ActionType.PON, self.player_index))
        
        if self.can_kan:
            actions.append(Action(ActionType.KAN, self.player_index))
        
        if self.can_chi:
            for opt in self.chi_options:
                actions.append(Action(ActionType.CHI, self.player_index, chi_option=opt.option_index))
        
        if self.can_pass:
            actions.append(Action(ActionType.PASS, self.player_index))
        
        return actions


@dataclass(frozen=True)
class GameState:
    """
    Complete immutable snapshot of the game state.
    This is what gets passed to agents for decision making.
    """
    # Game metadata
    turn_count: int
    phase: GamePhase
    active_player_index: int                # Whose turn it is
    
    # All player states
    players: tuple                          # Tuple of PlayerState (4 players)
    
    # Wall information
    wall_remaining: int
    dora_indicators: tuple                  # Tuple of TileState
    
    # Current turn context
    last_discard: Optional[TileState] = None        # The tile just discarded
    last_discard_player: Optional[int] = None       # Who discarded it
    drawn_tile: Optional[TileState] = None          # Tile just drawn (for active player)
    
    # Available actions for decision
    available_actions: Optional[AvailableActions] = None
    
    # Result information (if game over)
    winner_index: Optional[int] = None
    winning_yaku: tuple = ()
    
    def get_player(self, index: int) -> PlayerState:
        """Get a specific player's state."""
        return self.players[index]
    
    def get_active_player(self) -> PlayerState:
        """Get the active player's state."""
        return self.players[self.active_player_index]


@dataclass
class GameEvent:
    """
    Represents something that happened in the game.
    Used for UI updates, logging, and replay.
    """
    event_type: GameEventType
    player_index: Optional[int] = None      # Which player is involved
    tile: Optional[TileState] = None        # Relevant tile
    tiles: tuple = ()                       # Multiple tiles (for melds)
    message: str = ""                       # Human-readable description
    yaku: tuple = ()                        # Yaku list (for wins)
    data: dict = field(default_factory=dict)  # Additional data


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def tiles_to_state(tiles: list) -> tuple:
    """Convert a list of Tile objects to a tuple of TileState."""
    return tuple(TileState.from_tile(t) for t in tiles)


def state_to_tiles(states: tuple) -> list:
    """Convert a tuple of TileState to a list of Tile objects."""
    return [s.to_tile() for s in states]


def create_player_state(
    player,  # Player object
    index: int,
    shanten_calc,
    include_hand: bool = True
) -> PlayerState:
    """
    Create a PlayerState from a Player object.
    
    Args:
        player: The Player object
        index: Player seat index
        shanten_calc: ShantenCalculator instance
        include_hand: Whether to include the actual hand tiles (False for opponents)
    """
    shanten = shanten_calc.calculate_shanten(player.hand)
    waits = []
    is_furiten = False
    
    if shanten == 0:
        waits = shanten_calc.get_waits(player.hand)
        # Check furiten
        wait_ids = set((w.suit, w.value) for w in waits)
        discard_ids = set((t.suit, t.value) for t in player.discards)
        is_furiten = not wait_ids.isdisjoint(discard_ids)
    
    return PlayerState(
        index=index,
        name=player.name,
        score=player.score,
        is_riichi=player.is_riichi,
        is_menzen=player.is_menzen,
        hand=tiles_to_state(player.hand) if include_hand else (),
        hand_size=len(player.hand),
        discards=tiles_to_state(player.discards),
        open_melds=tuple(player.open_melds),
        shanten=shanten,
        waits=tiles_to_state(waits),
        is_furiten=is_furiten
    )
