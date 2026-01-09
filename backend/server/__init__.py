"""
Server Module - Flask WebSocket server for Riichi Mahjong.

Provides real-time multiplayer functionality via WebSockets.
"""

from .socket_manager import SocketManager, socket_manager
from .main import app, socketio, run_server

__all__ = [
    'SocketManager',
    'socket_manager',
    'app',
    'socketio',
    'run_server'
]
