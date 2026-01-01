"""
Game Controller - Orchestrates the game engine, agents, and UI.

The controller is the main entry point for running a game. It:
- Manages the game loop
- Queries agents for decisions
- Handles event distribution to UI/listeners
- Provides hooks for different UI implementations

Usage:
    from backend.core.game_controller import GameController
    from backend.ai.random_agent import RandomAgent
    from backend.ai.human_cli_agent import HumanCLIAgent
    
    controller = GameController()
    controller.set_agent(0, HumanCLIAgent("You"))
    controller.set_agent(1, RandomAgent("Bot 1"))
    controller.set_agent(2, RandomAgent("Bot 2"))
    controller.set_agent(3, RandomAgent("Bot 3"))
    
    controller.run_game()
"""

from __future__ import annotations  # Enable forward references

import time
from typing import Callable, Optional, List, Any

from .game_engine import GameEngine
from .game_state import (
    GameState, GamePhase, GameEvent, GameEventType,
    Action, AvailableActions
)


class GameController:
    """
    Orchestrates a Mahjong game between agents.
    
    The controller handles:
    - Game loop management
    - Agent turn management
    - Event routing to UI callbacks
    - Optional delays for human-viewable games
    """
    
    def __init__(self, player_names: List[str] = None):
        """
        Initialize the controller.
        
        Args:
            player_names: Names for the 4 players. Defaults to wind names.
        """
        if player_names is None:
            player_names = ["East", "South", "West", "North"]
        
        self.engine = GameEngine(player_names)
        self.agents: List[Optional[Any]] = [None, None, None, None]  # List of Agent objects
        
        # UI callbacks
        self._on_state_change: Optional[Callable[[GameState], None]] = None
        self._on_event: Optional[Callable[[GameEvent], None]] = None
        self._on_game_over: Optional[Callable[[GameState], None]] = None
        
        # Game settings
        self.turn_delay = 0.0  # Delay between turns (for human viewing)
        self.event_delay = 0.0  # Delay after events
        
        # Register for engine events
        self.engine.add_event_listener(self._handle_engine_event)
    
    # =========================================================================
    # Agent Management
    # =========================================================================
    
    def set_agent(self, seat: int, agent: Any):
        """
        Assign an agent to a seat.
        
        Args:
            seat: Player seat (0=East, 1=South, 2=West, 3=North)
            agent: The agent to assign
        """
        assert 0 <= seat < 4, "Seat must be 0-3"
        agent.player_index = seat
        self.agents[seat] = agent
    
    def get_agent(self, seat: int) -> Optional[Any]:
        """Get the agent at a seat."""
        return self.agents[seat]
    
    def _ensure_all_agents(self):
        """Fill empty seats with passive agents."""
        # Lazy import to avoid circular dependency
        from ..ai.agent import PassiveAgent
        for i in range(4):
            if self.agents[i] is None:
                self.agents[i] = PassiveAgent(f"Bot {i}")
                self.agents[i].player_index = i
    
    # =========================================================================
    # UI Callbacks
    # =========================================================================
    
    def on_state_change(self, callback: Callable[[GameState], None]):
        """Register callback for state changes."""
        self._on_state_change = callback
    
    def on_event(self, callback: Callable[[GameEvent], None]):
        """Register callback for game events."""
        self._on_event = callback
    
    def on_game_over(self, callback: Callable[[GameState], None]):
        """Register callback for game over."""
        self._on_game_over = callback
    
    def _handle_engine_event(self, event: GameEvent):
        """Handle events from the engine."""
        if self._on_event:
            self._on_event(event)
        
        # Notify agents
        for agent in self.agents:
            if agent:
                agent.on_game_event(event)
        
        if self.event_delay > 0:
            time.sleep(self.event_delay)
    
    def _notify_state_change(self):
        """Notify UI of state change."""
        if self._on_state_change:
            state = self.engine.get_state()
            self._on_state_change(state)
    
    # =========================================================================
    # Game Loop
    # =========================================================================
    
    def run_game(self) -> GameState:
        """
        Run a complete game from start to finish.
        
        Returns:
            The final game state.
        """
        self._ensure_all_agents()
        
        # Setup
        self.engine.setup()
        
        # Notify agents of game start
        state = self.engine.get_state()
        for agent in self.agents:
            if agent:
                agent.on_game_start(state)
        
        self._notify_state_change()
        
        # Main game loop
        while not self.engine.is_game_over:
            self._run_single_step()
            
            if self.turn_delay > 0:
                time.sleep(self.turn_delay)
        
        # Game over
        final_state = self.engine.get_state()
        
        for agent in self.agents:
            if agent:
                agent.on_game_end(final_state)
        
        if self._on_game_over:
            self._on_game_over(final_state)
        
        return final_state
    
    def _run_single_step(self):
        """Execute a single game step (one decision point)."""
        
        # Advance to next decision point if needed
        if self.engine.phase == GamePhase.DRAW:
            self.engine.advance_to_next_decision()
            self._notify_state_change()
        
        if self.engine.is_game_over:
            return
        
        # Get current state and available actions
        state = self.engine.get_state()
        available = state.available_actions
        
        if not available:
            return
        
        # Get decision from appropriate agent
        agent = self.agents[available.player_index]
        
        if agent is None:
            raise ValueError(f"No agent for player {available.player_index}")
        
        # Get agent's decision
        action = agent.choose_action(state, available)
        
        # Apply the action
        self.engine.apply_action(action)
        self._notify_state_change()
    
    def step(self) -> tuple[GameState, bool]:
        """
        Execute a single step and return state.
        
        Useful for external control (e.g., web server).
        
        Returns:
            Tuple of (current_state, is_game_over)
        """
        if not self.engine.is_game_over:
            self._run_single_step()
        
        return self.engine.get_state(), self.engine.is_game_over


class CLIGameController(GameController):
    """
    A controller with CLI-specific UI handling.
    
    Displays game state using Rich console and handles
    the typical CLI game flow.
    """
    
    def __init__(self, player_names: List[str] = None):
        super().__init__(player_names)
        self._console = None
        self.turn_delay = 0.0  # Default delay for CLI viewing [TIME DELAY PER OPPONENT'S TURN]
    
    @property
    def console(self):
        """Lazy-load Rich console."""
        if self._console is None:
            from rich.console import Console
            self._console = Console()
        return self._console
    
    def run_game(self) -> GameState:
        """Run game with CLI display."""
        from . import ui  # Import CLI UI module
        
        # Set up callbacks
        self.on_state_change(lambda state: self._display_state(state))
        self.on_event(lambda event: self._display_event(event))
        self.on_game_over(lambda state: self._display_game_over(state))
        
        return super().run_game()
    
    def _display_state(self, state: GameState):
        """Display game state using CLI UI."""
        # Only display on human player's turn or when they need to see
        from . import ui
        
        # Create a minimal game-like object for the existing UI
        # This is a compatibility shim - ideally we'd update ui.py to use GameState
        class GameShim:
            def __init__(self, state, engine):
                self.wall = engine.wall
                self.players = engine.players
                self.shanten_calc = engine.shanten_calc
                self.turn_count = state.turn_count
        
        shim = GameShim(state, self.engine)
        ui.print_dashboard(shim, state.active_player_index)
    
    def _display_event(self, event: GameEvent):
        """Display a game event."""
        from . import ui
        
        # Skip some events that are shown elsewhere
        if event.event_type in (GameEventType.GAME_STARTED, GameEventType.TURN_CHANGED):
            return
        
        # Display based on event type
        if event.event_type == GameEventType.TILE_DRAWN:
            if event.player_index == 0:  # Human
                tile = event.tile.to_tile()
                self.console.print(f"You draw: ", ui.get_tile_style(tile))
            else:
                self.console.print(f"[dim]{self.engine.players[event.player_index].name} draws a tile.[/]")
        
        elif event.event_type == GameEventType.TILE_DISCARDED:
            tile = event.tile.to_tile()
            player_name = self.engine.players[event.player_index].name
            if event.player_index == 0:
                self.console.print(f"You discard: ", ui.get_tile_style(tile))
            else:
                self.console.print(f"{player_name} discards: ", ui.get_tile_style(tile))
        
        elif event.event_type == GameEventType.RIICHI_DECLARED:
            player_name = self.engine.players[event.player_index].name
            self.console.print(f"[bold yellow]{player_name} declares RIICHI![/]")
        
        elif event.event_type == GameEventType.PON_CALLED:
            player_name = self.engine.players[event.player_index].name
            self.console.print(f"[bold cyan]{player_name} calls PON![/]")
        
        elif event.event_type == GameEventType.CHI_CALLED:
            player_name = self.engine.players[event.player_index].name
            self.console.print(f"[bold green]{player_name} calls CHI![/]")
        
        elif event.event_type == GameEventType.KAN_CALLED:
            player_name = self.engine.players[event.player_index].name
            self.console.print(f"[bold cyan]{player_name} calls KAN![/]")
        
        elif event.event_type == GameEventType.EXHAUSTIVE_DRAW:
            self.console.print("[bold red]--- Wall Empty! Ryuukyoku (Draw Game) ---[/]")
    
    def _display_game_over(self, state: GameState):
        """Display game over screen."""
        from . import ui
        
        self.console.print("\n[bold]=== GAME END ===[/]")
        
        if state.phase == GamePhase.GAME_OVER_WIN:
            winner = self.engine.players[state.winner_index]
            yaku_str = ', '.join(state.winning_yaku)
            self.console.print(f"[bold yellow]Winner: {winner.name}[/]")
            self.console.print(f"Yaku: {yaku_str}")
            self.console.print(ui.render_hand(winner))
        else:
            self.console.print("[bold]Exhaustive Draw - No Winner[/]")
        
        # Final scores
        self.console.print("\n[bold]Final Scores:[/]")
        for p in self.engine.players:
            self.console.print(f"  {p.name}: {p.score}")
