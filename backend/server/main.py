"""
WebSocket Server for Riichi Mahjong

This module provides a Flask-SocketIO server that:
- Hosts the web frontend
- Manages WebSocket connections for real-time gameplay
- Bridges web clients to the game engine

Usage:
    python -m backend.server.main

Or from project root:
    python main.py --web
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.game_engine import GameEngine
from backend.core.game_state import (
    GameState, GamePhase, GameEvent, GameEventType,
    Action, ActionType, AvailableActions, TileState
)
from backend.ai import RandomAgent


# =============================================================================
# Flask App Setup
# =============================================================================

app = Flask(__name__, static_folder='../../frontend')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# =============================================================================
# Game Session Management
# =============================================================================

class GameSession:
    """Manages a single game session with connected players."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.engine = None
        self.player_sids = {}  # seat_index -> socket_id
        self.ai_agents = {}    # seat_index -> Agent
        self.spectators = []
        self.started = False
    
    def add_player(self, sid: str, seat: int = None):
        """Add a human player to the session."""
        if seat is None:
            # Find first available seat
            for i in range(4):
                if i not in self.player_sids:
                    seat = i
                    break
        
        if seat is not None and seat not in self.player_sids:
            self.player_sids[seat] = sid
            return seat
        return None
    
    def remove_player(self, sid: str):
        """Remove a player from the session."""
        for seat, player_sid in list(self.player_sids.items()):
            if player_sid == sid:
                del self.player_sids[seat]
                return seat
        return None
    
    def fill_with_ai(self):
        """Fill empty seats with AI agents."""
        for i in range(4):
            if i not in self.player_sids and i not in self.ai_agents:
                self.ai_agents[i] = RandomAgent(f"AI {['East', 'South', 'West', 'North'][i]}")
    
    def get_player_seat(self, sid: str):
        """Get the seat index for a player's socket ID."""
        for seat, player_sid in self.player_sids.items():
            if player_sid == sid:
                return seat
        return None


# Global session storage
game_sessions = {}
sid_to_session = {}  # socket_id -> session_id


def get_or_create_session(session_id: str = 'default') -> GameSession:
    """Get or create a game session."""
    if session_id not in game_sessions:
        game_sessions[session_id] = GameSession(session_id)
    return game_sessions[session_id]


# =============================================================================
# State Serialisation
# =============================================================================

def serialise_tile(tile: TileState) -> dict:
    """Convert TileState to JSON-serialisable dict."""
    if tile is None:
        return None
    return {
        'suit': tile.suit,
        'value': tile.value,
        'is_red': tile.is_red
    }


def serialise_player(player_state, include_hand: bool = True) -> dict:
    """Convert PlayerState to JSON-serialisable dict."""
    return {
        'index': player_state.index,
        'name': player_state.name,
        'score': player_state.score,
        'is_riichi': player_state.is_riichi,
        'is_menzen': player_state.is_menzen,
        'hand': [serialise_tile(t) for t in player_state.hand] if include_hand else [],
        'hand_size': player_state.hand_size,
        'discards': [serialise_tile(t) for t in player_state.discards],
        'open_melds': list(player_state.open_melds),
        'shanten': player_state.shanten,
        'waits': [serialise_tile(t) for t in player_state.waits],
        'is_furiten': player_state.is_furiten
    }


def serialise_available_actions(actions: AvailableActions) -> dict:
    """Convert AvailableActions to JSON-serialisable dict."""
    if actions is None:
        return None
    
    chi_options = []
    for opt in actions.chi_options:
        chi_options.append({
            'option_index': opt.option_index,
            'tile_indices': list(opt.tile_indices),
            'resulting_tiles': [serialise_tile(t) for t in opt.resulting_tiles]
        })
    
    return {
        'player_index': actions.player_index,
        'phase': actions.phase.name,
        'can_discard': actions.can_discard,
        'discard_indices': list(actions.discard_indices),
        'can_riichi': actions.can_riichi,
        'riichi_discard_indices': list(actions.riichi_discard_indices),
        'can_tsumo': actions.can_tsumo,
        'tsumo_yaku': list(actions.tsumo_yaku),
        'can_ron': actions.can_ron,
        'ron_yaku': list(actions.ron_yaku),
        'can_pon': actions.can_pon,
        'can_kan': actions.can_kan,
        'can_chi': actions.can_chi,
        'chi_options': chi_options,
        'can_pass': actions.can_pass
    }


def serialise_game_state(state: GameState, for_player: int = None) -> dict:
    """Convert GameState to JSON-serialisable dict for a specific player."""
    players = []
    for i, p in enumerate(state.players):
        # Only include hand for the requesting player
        include_hand = (for_player is None) or (i == for_player)
        players.append(serialise_player(p, include_hand=include_hand))
    
    return {
        'turn_count': state.turn_count,
        'phase': state.phase.name,
        'active_player_index': state.active_player_index,
        'players': players,
        'wall_remaining': state.wall_remaining,
        'dora_indicators': [serialise_tile(t) for t in state.dora_indicators],
        'last_discard': serialise_tile(state.last_discard),
        'last_discard_player': state.last_discard_player,
        'drawn_tile': serialise_tile(state.drawn_tile) if for_player == state.active_player_index else None,
        'available_actions': serialise_available_actions(state.available_actions),
        'winner_index': state.winner_index,
        'winning_yaku': list(state.winning_yaku)
    }


def serialise_event(event: GameEvent) -> dict:
    """Convert GameEvent to JSON-serialisable dict."""
    return {
        'event_type': event.event_type.name,
        'player_index': event.player_index,
        'tile': serialise_tile(event.tile) if event.tile else None,
        'tiles': [serialise_tile(t) for t in event.tiles],
        'message': event.message,
        'yaku': list(event.yaku),
        'data': event.data
    }


# =============================================================================
# HTTP Routes
# =============================================================================

@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend directory."""
    return send_from_directory(app.static_folder, filename)


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok', 'sessions': len(game_sessions)}


# =============================================================================
# WebSocket Events
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    sid = request.sid
    print(f"Client disconnected: {sid}")
    
    # Clean up session
    if sid in sid_to_session:
        session_id = sid_to_session[sid]
        session = game_sessions.get(session_id)
        if session:
            seat = session.remove_player(sid)
            if seat is not None:
                socketio.emit('player_left', {'seat': seat}, room=session_id)
        del sid_to_session[sid]


@socketio.on('join_game')
def handle_join_game(data):
    """Handle player joining a game."""
    session_id = data.get('session_id', 'default')
    player_name = data.get('name', 'Player')
    
    session = get_or_create_session(session_id)
    seat = session.add_player(request.sid)
    
    if seat is not None:
        sid_to_session[request.sid] = session_id
        join_room(session_id)
        
        emit('joined_game', {
            'seat': seat,
            'session_id': session_id,
            'player_name': player_name
        })
        
        # Notify others
        socketio.emit('player_joined', {
            'seat': seat,
            'name': player_name
        }, room=session_id, skip_sid=request.sid)
        
        print(f"Player {player_name} joined session {session_id} at seat {seat}")
    else:
        emit('error', {'message': 'Game is full'})


@socketio.on('start_game')
def handle_start_game(data):
    """Handle game start request."""
    session_id = data.get('session_id', 'default')
    session = game_sessions.get(session_id)
    
    if not session:
        emit('error', {'message': 'Session not found'})
        return
    
    if session.started:
        emit('error', {'message': 'Game already started'})
        return
    
    # Fill empty seats with AI
    session.fill_with_ai()
    
    # Create player names
    player_names = []
    for i in range(4):
        if i in session.player_sids:
            player_names.append(f"Player {i + 1}")
        else:
            player_names.append(session.ai_agents[i].name)
    
    # Initialise engine
    session.engine = GameEngine(player_names)
    session.engine.setup()
    session.started = True
    
    # Send initial state to all players
    broadcast_state(session)
    
    # Start game loop for AI turns
    process_ai_turns(session)


def broadcast_state(session: GameSession):
    """Send game state to all connected players."""
    if not session.engine:
        return
    
    state = session.engine.get_state()
    
    # Send personalized state to each human player
    for seat, sid in session.player_sids.items():
        player_state = serialise_game_state(state, for_player=seat)
        socketio.emit('game_state', player_state, room=sid)


def broadcast_event(session: GameSession, event: GameEvent):
    """Send game event to all connected players."""
    event_data = serialise_event(event)
    socketio.emit('game_event', event_data, room=session.session_id)


def process_ai_turns(session: GameSession):
    """Process AI turns until a human player needs to act."""
    if not session.engine or session.engine.is_game_over:
        return
    
    import time
    
    while not session.engine.is_game_over:
        # Advance to next decision if needed
        if session.engine.phase == GamePhase.DRAW:
            events = session.engine.advance_to_next_decision()
            for event in events:
                broadcast_event(session, event)
            broadcast_state(session)
        
        if session.engine.is_game_over:
            break
        
        state = session.engine.get_state()
        available = state.available_actions
        
        if not available:
            break
        
        active_seat = available.player_index
        
        # Check if it's a human player's turn
        if active_seat in session.player_sids:
            # Wait for human input
            broadcast_state(session)
            return
        
        # AI turn - get action and apply
        if active_seat in session.ai_agents:
            agent = session.ai_agents[active_seat]
            action = agent.choose_action(state, available)
            
            # Small delay for visual feedback
            socketio.sleep(0.3)
            
            events = session.engine.apply_action(action)
            for event in events:
                broadcast_event(session, event)
            broadcast_state(session)
    
    # Game over
    if session.engine.is_game_over:
        state = session.engine.get_state()
        socketio.emit('game_over', serialise_game_state(state), room=session.session_id)


@socketio.on('player_action')
def handle_player_action(data):
    """Handle player action from web client."""
    session_id = data.get('session_id', 'default')
    session = game_sessions.get(session_id)
    
    if not session or not session.engine:
        emit('error', {'message': 'No active game'})
        return
    
    seat = session.get_player_seat(request.sid)
    if seat is None:
        emit('error', {'message': 'Not in game'})
        return
    
    # Validate it's this player's turn
    state = session.engine.get_state()
    available = state.available_actions
    
    if not available or available.player_index != seat:
        emit('error', {'message': 'Not your turn'})
        return
    
    # Parse action
    action_type_str = data.get('action_type')
    tile_index = data.get('tile_index')
    chi_option = data.get('chi_option')
    
    try:
        action_type = ActionType[action_type_str]
        action = Action(
            action_type=action_type,
            player_index=seat,
            tile_index=tile_index,
            chi_option=chi_option
        )
        
        # Apply action
        events = session.engine.apply_action(action)
        for event in events:
            broadcast_event(session, event)
        broadcast_state(session)
        
        # Continue with AI turns
        if not session.engine.is_game_over:
            socketio.start_background_task(process_ai_turns, session)
        else:
            state = session.engine.get_state()
            socketio.emit('game_over', serialise_game_state(state), room=session.session_id)
        
    except Exception as e:
        emit('error', {'message': f'Invalid action: {str(e)}'})


@socketio.on('restart_game')
def handle_restart_game(data):
    """Handle game restart request."""
    session_id = data.get('session_id', 'default')
    session = game_sessions.get(session_id)
    
    if session:
        session.started = False
        session.engine = None
        socketio.emit('game_reset', {}, room=session_id)


# =============================================================================
# Main Entry
# =============================================================================

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the WebSocket server."""
    print(f"\n{'='*50}")
    print("   RIICHI MAHJONG - Web Server")
    print(f"{'='*50}")
    print(f"\n🀄 Server starting at http://{host}:{port}")
    print(f"📱 Open your browser to http://localhost:{port}")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_server(debug=True)
