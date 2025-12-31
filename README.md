# Riichi Mahjong

An implementation of Riichi Mahjong with AI opponents and a web-based interface. Caveat: it is currently a work-in-progress, with the features mentioned below still in development.

## Project Structure

```
riichi-mahjong/
├── backend/          # Backend server and game logic
│   ├── ai/           # AI agent implementations
│   ├── core/         # Game logic and rules
│   ├── server/       # Flask/WebSocket server
│   └── tests/        # Unit tests
└── frontend/         # Web-based UI
    ├── assets/       # Game assets (tiles, etc.)
    ├── css/          # Stylesheets
    └── javascript/   # Client-side logic
```

## Features

-   Complete Riichi Mahjong ruleset (that's the goal!)
-   Multiple AI opponents (Random, Minimax, MCTS)
-   Hand evaluation and scoring system
-   Shanten calculation
-   Real-time multiplayer via WebSockets
-   Browser-based interface

## Backend Components

-   **core/**: Game engine including tile management, hand evaluation, scoring, and game table logic
-   **ai/**: Various AI agents with different strategies
-   **server/**: WebSocket server for real-time communication
-   **tests/**: Test suites for scoring and shanten calculation

## Frontend Components

-   **index.html**: Main game interface
-   **javascript/**: Game rendering and client-server communication
-   **assets/tiles/**: Tile graphics

## Getting Started

### Prerequisites

-   Python 3.11 and above
-   Modern web browser

### Installation

1. Clone the repository
2. Install Python dependencies (if any)
3. Run the backend server from `backend/server/main.py`
4. Open `frontend/index.html` in a web browser
