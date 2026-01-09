"""
Socket Manager Module - WebSocket session and connection management.

Handles the WebSocket communication layer between the web frontend
and the game engine.
"""

from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from flask_socketio import SocketIO


@dataclass
class PlayerConnection:
    """Represents a connected player."""
    sid: str                    # Socket ID
    seat: int                   # Seat index (0-3)
    name: str = "Player"
    connected: bool = True


@dataclass 
class GameRoom:
    """Represents a game room/session."""
    room_id: str
    players: Dict[int, PlayerConnection] = field(default_factory=dict)  # seat -> connection
    spectators: list = field(default_factory=list)
    game_started: bool = False
    
    def add_player(self, sid: str, name: str = "Player") -> Optional[int]:
        """Add a player to the next available seat."""
        for seat in range(4):
            if seat not in self.players:
                self.players[seat] = PlayerConnection(sid=sid, seat=seat, name=name)
                return seat
        return None
    
    def remove_player(self, sid: str) -> Optional[int]:
        """Remove a player by socket ID."""
        for seat, player in list(self.players.items()):
            if player.sid == sid:
                del self.players[seat]
                return seat
        return None
    
    def get_player_seat(self, sid: str) -> Optional[int]:
        """Get the seat for a socket ID."""
        for seat, player in self.players.items():
            if player.sid == sid:
                return seat
        return None
    
    def is_full(self) -> bool:
        """Check if all seats are taken."""
        return len(self.players) >= 4


class SocketManager:
    """
    Manages WebSocket connections and game rooms.
    
    This class provides a clean interface for:
    - Managing player connections
    - Creating and joining game rooms
    - Broadcasting messages to players
    """
    
    def __init__(self, socketio: SocketIO = None):
        self.socketio = socketio
        self.rooms: Dict[str, GameRoom] = {}
        self.sid_to_room: Dict[str, str] = {}  # socket_id -> room_id
    
    def set_socketio(self, socketio: SocketIO):
        """Set the SocketIO instance."""
        self.socketio = socketio
    
    def create_room(self, room_id: str) -> GameRoom:
        """Create a new game room."""
        if room_id not in self.rooms:
            self.rooms[room_id] = GameRoom(room_id=room_id)
        return self.rooms[room_id]
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID."""
        return self.rooms.get(room_id)
    
    def join_room(self, sid: str, room_id: str, name: str = "Player") -> Optional[int]:
        """
        Join a player to a room.
        
        Returns the assigned seat, or None if room is full.
        """
        room = self.create_room(room_id)
        
        if room.is_full():
            return None
        
        seat = room.add_player(sid, name)
        if seat is not None:
            self.sid_to_room[sid] = room_id
        
        return seat
    
    def leave_room(self, sid: str) -> Optional[tuple]:
        """
        Remove a player from their room.
        
        Returns (room_id, seat) if found, None otherwise.
        """
        if sid not in self.sid_to_room:
            return None
        
        room_id = self.sid_to_room[sid]
        room = self.rooms.get(room_id)
        
        if room:
            seat = room.remove_player(sid)
            del self.sid_to_room[sid]
            return (room_id, seat)
        
        return None
    
    def get_player_room(self, sid: str) -> Optional[str]:
        """Get the room ID for a player."""
        return self.sid_to_room.get(sid)
    
    def broadcast_to_room(self, room_id: str, event: str, data: dict):
        """Broadcast a message to all players in a room."""
        if self.socketio:
            self.socketio.emit(event, data, room=room_id)
    
    def send_to_player(self, sid: str, event: str, data: dict):
        """Send a message to a specific player."""
        if self.socketio:
            self.socketio.emit(event, data, room=sid)
    
    def cleanup_empty_rooms(self):
        """Remove rooms with no players."""
        empty_rooms = [
            room_id for room_id, room in self.rooms.items()
            if len(room.players) == 0 and not room.game_started
        ]
        for room_id in empty_rooms:
            del self.rooms[room_id]


# Global socket manager instance
socket_manager = SocketManager()
