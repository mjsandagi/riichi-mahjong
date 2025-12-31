# Riichi Mahjong

An implementation of Riichi Mahjong with AI opponents. The game currently features a fully functional CLI interface, with a web-based interface planned for future development.

## Project Structure

```
riichi-mahjong/
├── backend/          # Backend server and game logic
│   ├── ai/           # AI agent implementations
│   ├── core/         # Game logic and rules
│   ├── server/       # Flask/WebSocket server
│   └── tests/        # Unit tests
└── frontend/         # Web-based UI (in development)
    ├── assets/       # Game assets (tiles, etc.)
    ├── css/          # Stylesheets
    └── javascript/   # Client-side logic
```

## Features

-   Complete Riichi Mahjong ruleset
-   Fully playable via command-line interface
-   Hand evaluation and scoring system
-   Shanten calculation
-   Multiple AI opponents in development (Random, Minimax, MCTS)
-   Real-time multiplayer via WebSockets (planned)
-   Browser-based interface (planned)

## Backend Components

-   **core/**: Game engine including tile management, hand evaluation, scoring, and game table logic
-   **ai/**: Various AI agents with different strategies (in development)
-   **server/**: WebSocket server for real-time communication (planned)
-   **tests/**: Test suites for scoring and shanten calculation

## Frontend Components

-   **index.html**: Main game interface (in development)
-   **javascript/**: Game rendering and client-server communication (in development)
-   **assets/tiles/**: Tile graphics (in development)

## Getting Started

### Prerequisites

-   Python 3.11 and above
-   Modern web browser (for future web interface)

### Installation

1. Clone the repository
2. Install Python dependencies (if any)
3. Run the CLI game from `backend/core/main.py`
4. Web interface coming soon after AI development is complete
