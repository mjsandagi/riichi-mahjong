/**
 * Riichi Mahjong - Main Application
 *
 * Handles WebSocket communication, game state management,
 * and user interactions.
 */

class MahjongGame {
    constructor() {
        // Socket connection
        this.socket = null;
        this.connected = false;
        this.sessionId = "default";
        this.playerSeat = null;
        this.playerName = "Player";

        // Game state
        this.gameState = null;
        this.selectedTileIndex = null;
        this.myTurn = false;

        // UI elements cache
        this.ui = {};

        // Wind characters
        this.windChars = ["東", "南", "西", "北"];
        this.windNames = ["East", "South", "West", "North"];

        // Initialise
        this.init();
    }

    /**
     * Initialise the application
     */
    init() {
        this.cacheUIElements();
        this.bindEvents();
        this.showScreen("menu");
    }

    /**
     * Cache frequently used UI elements
     */
    cacheUIElements() {
        this.ui = {
            // Screens
            menuScreen: document.getElementById("menu-screen"),
            rulesScreen: document.getElementById("rules-screen"),
            gameScreen: document.getElementById("game-screen"),

            // Menu
            playerNameInput: document.getElementById("player-name"),
            btnPlayAI: document.getElementById("btn-play-ai"),
            btnRules: document.getElementById("btn-rules"),
            btnBackMenu: document.getElementById("btn-back-menu"),

            // Connection
            connectionStatus: document.getElementById("connection-status"),

            // Game info
            wallRemaining: document.getElementById("wall-remaining"),
            turnCount: document.getElementById("turn-count"),
            doraTiles: document.getElementById("dora-tiles"),
            turnIndicator: document.getElementById("turn-indicator"),
            currentWind: document.getElementById("current-wind"),

            // Player areas (indexed by seat)
            playerAreas: [
                document.getElementById("player-0-area"),
                document.getElementById("player-1-area"),
                document.getElementById("player-2-area"),
                document.getElementById("player-3-area"),
            ],
            playerNames: [
                document.getElementById("player-0-name"),
                document.getElementById("player-1-name"),
                document.getElementById("player-2-name"),
                document.getElementById("player-3-name"),
            ],
            playerScores: [
                document.getElementById("player-0-score"),
                document.getElementById("player-1-score"),
                document.getElementById("player-2-score"),
                document.getElementById("player-3-score"),
            ],
            playerStatuses: [
                null, // Player 0 has different status display
                document.getElementById("player-1-status"),
                document.getElementById("player-2-status"),
                document.getElementById("player-3-status"),
            ],
            playerHands: [
                document.getElementById("player-0-hand"),
                document.getElementById("player-1-hand"),
                document.getElementById("player-2-hand"),
                document.getElementById("player-3-hand"),
            ],
            playerMelds: [
                document.getElementById("player-0-melds"),
                document.getElementById("player-1-melds"),
                document.getElementById("player-2-melds"),
                document.getElementById("player-3-melds"),
            ],
            playerRivers: [
                document.getElementById("player-0-river"),
                document.getElementById("player-1-river"),
                document.getElementById("player-2-river"),
                document.getElementById("player-3-river"),
            ],

            // Own player specific
            drawnTile: document.getElementById("drawn-tile"),
            playerStatusBadge: document.getElementById("player-status-badge"),
            shantenDisplay: document.getElementById("shanten-display"),
            waitsDisplay: document.getElementById("waits-display"),
            waitsTiles: document.getElementById("waits-tiles"),

            // Actions
            actionPanel: document.getElementById("action-panel"),
            actionButtons: document.getElementById("action-buttons"),

            // Overlays
            gameOverOverlay: document.getElementById("game-over-overlay"),
            gameOverTitle: document.getElementById("game-over-title"),
            gameOverDetails: document.getElementById("game-over-details"),
            finalScores: document.getElementById("final-scores"),
            btnPlayAgain: document.getElementById("btn-play-again"),
            btnBackToMenu: document.getElementById("btn-back-to-menu"),

            menuOverlay: document.getElementById("menu-overlay"),
            btnMenu: document.getElementById("btn-menu"),
            btnResume: document.getElementById("btn-resume"),
            btnQuitGame: document.getElementById("btn-quit-game"),

            // Toast
            toastContainer: document.getElementById("toast-container"),
        };
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Menu buttons
        this.ui.btnPlayAI.addEventListener("click", () => this.startGame());
        this.ui.btnRules.addEventListener("click", () =>
            this.showScreen("rules")
        );
        this.ui.btnBackMenu.addEventListener("click", () =>
            this.showScreen("menu")
        );

        // In-game menu
        this.ui.btnMenu.addEventListener("click", () => this.toggleMenu(true));
        this.ui.btnResume.addEventListener("click", () =>
            this.toggleMenu(false)
        );
        this.ui.btnQuitGame.addEventListener("click", () => this.quitGame());

        // Game over buttons
        this.ui.btnPlayAgain.addEventListener("click", () =>
            this.restartGame()
        );
        this.ui.btnBackToMenu.addEventListener("click", () =>
            this.returnToMenu()
        );

        // Keyboard shortcuts
        document.addEventListener("keydown", (e) => this.handleKeyPress(e));
    }

    /**
     * Show a specific screen
     */
    showScreen(screenName) {
        ["menu", "rules", "game"].forEach((name) => {
            const screen = document.getElementById(`${name}-screen`);
            if (screen) {
                screen.classList.toggle("active", name === screenName);
            }
        });
    }

    /**
     * Connect to WebSocket server
     */
    connectSocket() {
        return new Promise((resolve, reject) => {
            const serverUrl = window.location.origin;

            this.showConnectionStatus("Connecting...", "connecting");

            this.socket = io(serverUrl, {
                transports: ["websocket", "polling"],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
            });

            this.socket.on("connect", () => {
                this.connected = true;
                this.showConnectionStatus("Connected", "connected");
                console.log("Connected to server");
                resolve();
            });

            this.socket.on("disconnect", () => {
                this.connected = false;
                this.showConnectionStatus("Disconnected", "disconnected");
                console.log("Disconnected from server");
            });

            this.socket.on("connect_error", (error) => {
                console.error("Connection error:", error);
                this.showConnectionStatus("Connection failed", "disconnected");
                reject(error);
            });

            // Game events
            this.socket.on("connected", (data) => {
                console.log("Server acknowledged connection:", data);
            });

            this.socket.on("joined_game", (data) => {
                this.playerSeat = data.seat;
                console.log(`Joined game at seat ${data.seat}`);
            });

            this.socket.on("game_state", (state) => {
                this.updateGameState(state);
            });

            this.socket.on("game_event", (event) => {
                this.handleGameEvent(event);
            });

            this.socket.on("game_over", (state) => {
                this.handleGameOver(state);
            });

            this.socket.on("game_reset", () => {
                this.hideOverlay("gameOver");
            });

            this.socket.on("error", (data) => {
                this.showToast(data.message, "error");
            });

            // Timeout for connection
            setTimeout(() => {
                if (!this.connected) {
                    reject(new Error("Connection timeout"));
                }
            }, 10000);
        });
    }

    /**
     * Show connection status indicator
     */
    showConnectionStatus(text, status) {
        const statusEl = this.ui.connectionStatus;
        statusEl.querySelector(".status-text").textContent = text;
        statusEl.className = `connection-status ${status} visible`;

        // Hide after a few seconds if connected
        if (status === "connected") {
            setTimeout(() => {
                statusEl.classList.remove("visible");
            }, 2000);
        }
    }

    /**
     * Start a new game
     */
    async startGame() {
        this.playerName = this.ui.playerNameInput.value.trim() || "Player";

        try {
            // Connect if not connected
            if (!this.connected) {
                await this.connectSocket();
            }

            // Show game screen
            this.showScreen("game");

            // Join game
            this.socket.emit("join_game", {
                session_id: this.sessionId,
                name: this.playerName,
            });

            // Start game with AI
            setTimeout(() => {
                this.socket.emit("start_game", {
                    session_id: this.sessionId,
                });
            }, 500);
        } catch (error) {
            console.error("Failed to start game:", error);
            this.showToast(
                "Failed to connect to server. Please try again.",
                "error"
            );
        }
    }

    /**
     * Update game state from server
     */
    updateGameState(state) {
        this.gameState = state;

        // Clear selection when state updates
        this.selectedTileIndex = null;

        // Update UI
        this.renderGameInfo(state);
        this.renderAllPlayers(state);
        this.updateTurnIndicator(state);
        this.updateActionPanel(state);
    }

    /**
     * Render game info (wall, turn, dora)
     */
    renderGameInfo(state) {
        this.ui.wallRemaining.textContent = state.wall_remaining;
        this.ui.turnCount.textContent = state.turn_count;
        TileRenderer.renderDora(state.dora_indicators, this.ui.doraTiles);
    }

    /**
     * Render all player areas
     */
    renderAllPlayers(state) {
        state.players.forEach((player, i) => {
            this.renderPlayer(player, i, state);
        });
    }

    /**
     * Render a single player
     */
    renderPlayer(player, seatIndex, state) {
        // Map server seat to display position
        // Server sends seat 0 = our player, 1 = right, 2 = across, 3 = left
        const displayIndex = this.getDisplayIndex(seatIndex);

        // Update name and score
        const windPrefix = this.windNames[seatIndex];
        const name =
            seatIndex === this.playerSeat
                ? `${this.playerName} (${windPrefix})`
                : player.name;

        if (this.ui.playerNames[displayIndex]) {
            this.ui.playerNames[displayIndex].textContent = name;
        }
        if (this.ui.playerScores[displayIndex]) {
            this.ui.playerScores[displayIndex].textContent =
                player.score.toLocaleString();
        }

        // Update status (riichi)
        if (displayIndex !== 0 && this.ui.playerStatuses[displayIndex]) {
            const statusEl = this.ui.playerStatuses[displayIndex];
            if (player.is_riichi) {
                statusEl.textContent = "RIICHI";
                statusEl.className = "opponent-status riichi";
            } else {
                statusEl.textContent = "";
                statusEl.className = "opponent-status";
            }
        }

        // Highlight active player
        if (this.ui.playerAreas[displayIndex]) {
            this.ui.playerAreas[displayIndex].classList.toggle(
                "active",
                seatIndex === state.active_player_index
            );
        }

        // Render hand
        if (seatIndex === this.playerSeat) {
            // Our hand - show tiles
            this.renderOwnHand(player, state);
        } else {
            // Opponent - show backs
            TileRenderer.renderOpponentHand(
                player.hand_size,
                this.ui.playerHands[displayIndex],
                displayIndex === 1 || displayIndex === 3 // vertical for left/right
            );
        }

        // Render melds
        if (this.ui.playerMelds[displayIndex]) {
            TileRenderer.renderMelds(
                player.open_melds,
                this.ui.playerMelds[displayIndex]
            );
        }

        // Render river
        if (this.ui.playerRivers[displayIndex]) {
            TileRenderer.renderRiver(
                player.discards,
                this.ui.playerRivers[displayIndex]
            );
        }
    }

    /**
     * Get display index for a seat (0 = bottom, 1 = right, 2 = top, 3 = left)
     */
    getDisplayIndex(seatIndex) {
        if (this.playerSeat === null) return seatIndex;
        // Rotate based on our seat
        return (seatIndex - this.playerSeat + 4) % 4;
    }

    /**
     * Render our own hand
     */
    renderOwnHand(player, state) {
        const isOurTurn = state.active_player_index === this.playerSeat;
        const actions = state.available_actions;
        const canDiscard =
            isOurTurn && actions && (actions.can_discard || actions.can_riichi);

        // Separate drawn tile (last tile after draw)
        let handTiles = [...player.hand];
        let drawnTile = null;

        if (state.drawn_tile && isOurTurn && state.phase === "DISCARD") {
            // The drawn tile is the last one
            drawnTile = handTiles.pop();
        }

        // Render main hand
        TileRenderer.renderHand(handTiles, this.ui.playerHands[0], {
            selectable: canDiscard,
            selectedIndices:
                this.selectedTileIndex !== null
                    ? new Set([this.selectedTileIndex])
                    : new Set(),
            onTileClick: (index, tile) => this.handleTileClick(index, tile),
        });

        // Render drawn tile separately
        this.ui.drawnTile.innerHTML = "";
        if (drawnTile) {
            const tileEl = TileRenderer.createTile(drawnTile, {
                selectable: canDiscard,
                selected: this.selectedTileIndex === handTiles.length,
                index: handTiles.length,
                animated: true,
                animationType: "just-drawn",
            });

            if (canDiscard) {
                tileEl.addEventListener("click", () =>
                    this.handleTileClick(handTiles.length, drawnTile)
                );
            }

            this.ui.drawnTile.appendChild(tileEl);
        }

        // Update status badges
        this.updatePlayerStatus(player);
    }

    /**
     * Update player status display (riichi, tenpai, furiten, shanten)
     */
    updatePlayerStatus(player) {
        const badge = this.ui.playerStatusBadge;
        const shantenEl = this.ui.shantenDisplay;
        const waitsDisplay = this.ui.waitsDisplay;

        // Clear previous
        badge.className = "status-badge hidden";
        badge.textContent = "";
        shantenEl.textContent = "";
        waitsDisplay.classList.remove("visible");

        if (player.is_riichi) {
            badge.textContent = "RIICHI";
            badge.className = "status-badge riichi";
        } else if (player.is_furiten) {
            badge.textContent = "FURITEN";
            badge.className = "status-badge furiten";
        } else if (player.shanten === 0) {
            badge.textContent = "TENPAI";
            badge.className = "status-badge tenpai";
        }

        // Shanten display
        if (player.shanten > 0 && player.shanten <= 3) {
            shantenEl.textContent = `${player.shanten}-shanten`;
        }

        // Waits display
        if (player.waits && player.waits.length > 0) {
            waitsDisplay.classList.add("visible");
            TileRenderer.renderWaits(player.waits, this.ui.waitsTiles);
        }
    }

    /**
     * Update turn indicator
     */
    updateTurnIndicator(state) {
        const windChar = this.windChars[state.active_player_index];
        this.ui.currentWind.textContent = windChar;

        // Check if it's our turn
        this.myTurn = state.active_player_index === this.playerSeat;
    }

    /**
     * Update action panel based on available actions
     */
    updateActionPanel(state) {
        const actions = state.available_actions;
        const panel = this.ui.actionPanel;
        const buttons = this.ui.actionButtons;

        buttons.innerHTML = "";

        if (!actions || actions.player_index !== this.playerSeat) {
            panel.classList.remove("visible");
            return;
        }

        const actionsToShow = [];

        // Win actions (highest priority)
        if (actions.can_tsumo) {
            actionsToShow.push({
                text: "TSUMO",
                class: "win",
                action: () => this.sendAction("TSUMO"),
            });
        }

        if (actions.can_ron) {
            actionsToShow.push({
                text: "RON",
                class: "win",
                action: () => this.sendAction("RON"),
            });
        }

        // Riichi
        if (actions.can_riichi && !this.selectedTileIndex === null) {
            actionsToShow.push({
                text: "RIICHI",
                class: "primary",
                action: () => this.declareRiichi(),
            });
        }

        // Calls
        if (actions.can_kan) {
            actionsToShow.push({
                text: "KAN",
                class: "secondary",
                action: () => this.sendAction("KAN"),
            });
        }

        if (actions.can_pon) {
            actionsToShow.push({
                text: "PON",
                class: "secondary",
                action: () => this.sendAction("PON"),
            });
        }

        if (actions.can_chi && actions.chi_options.length > 0) {
            // For simplicity, just use the first chi option
            // A more complete implementation would show a selection
            actionsToShow.push({
                text: "CHI",
                class: "secondary",
                action: () => this.sendAction("CHI", null, 0),
            });
        }

        // Pass (for call phase)
        if (actions.can_pass) {
            actionsToShow.push({
                text: "PASS",
                class: "secondary",
                action: () => this.sendAction("PASS"),
            });
        }

        // Show discard button only if a tile is selected
        if (actions.can_discard && this.selectedTileIndex !== null) {
            actionsToShow.unshift({
                text: "DISCARD",
                class: "primary",
                action: () => this.discardTile(),
            });
        }

        // Create buttons
        actionsToShow.forEach(({ text, class: className, action }) => {
            const btn = document.createElement("button");
            btn.className = `action-btn ${className}`;
            btn.textContent = text;
            btn.addEventListener("click", action);
            buttons.appendChild(btn);
        });

        panel.classList.toggle("visible", actionsToShow.length > 0);
    }

    /**
     * Handle tile click
     */
    handleTileClick(index, tile) {
        if (this.selectedTileIndex === index) {
            // Double-click to discard
            this.discardTile();
        } else {
            this.selectedTileIndex = index;
            // Re-render to show selection
            if (this.gameState) {
                this.renderOwnHand(
                    this.gameState.players.find(
                        (p) => p.index === this.playerSeat
                    ),
                    this.gameState
                );
                this.updateActionPanel(this.gameState);
            }
        }
    }

    /**
     * Discard selected tile
     */
    discardTile() {
        if (this.selectedTileIndex === null) {
            this.showToast("Select a tile to discard", "warning");
            return;
        }

        this.sendAction("DISCARD", this.selectedTileIndex);
        this.selectedTileIndex = null;
    }

    /**
     * Declare Riichi
     */
    declareRiichi() {
        if (this.selectedTileIndex === null) {
            this.showToast("Select a tile to discard with Riichi", "warning");
            return;
        }

        this.sendAction("DECLARE_RIICHI", this.selectedTileIndex);
        this.selectedTileIndex = null;
    }

    /**
     * Send action to server
     */
    sendAction(actionType, tileIndex = null, chiOption = null) {
        if (!this.socket || !this.connected) {
            this.showToast("Not connected to server", "error");
            return;
        }

        const action = {
            session_id: this.sessionId,
            action_type: actionType,
            tile_index: tileIndex,
            chi_option: chiOption,
        };

        console.log("Sending action:", action);
        this.socket.emit("player_action", action);

        // Clear selection
        this.selectedTileIndex = null;
    }

    /**
     * Handle game event from server
     */
    handleGameEvent(event) {
        console.log("Game event:", event);

        // Show relevant toasts for important events
        switch (event.event_type) {
            case "RIICHI_DECLARED":
                const playerName =
                    this.gameState?.players[event.player_index]?.name ||
                    "Player";
                this.showToast(`${playerName} declares RIICHI!`, "warning");
                break;

            case "PON_CALLED":
            case "CHI_CALLED":
            case "KAN_CALLED":
                const caller =
                    this.gameState?.players[event.player_index]?.name ||
                    "Player";
                const callType = event.event_type.replace("_CALLED", "");
                this.showToast(`${caller} calls ${callType}!`, "info");
                break;

            case "TSUMO_WIN":
            case "RON_WIN":
                // Handle in game over
                break;

            case "EXHAUSTIVE_DRAW":
                this.showToast("Exhaustive Draw - No more tiles!", "warning");
                break;
        }
    }

    /**
     * Handle game over
     */
    handleGameOver(state) {
        this.gameState = state;

        const overlay = this.ui.gameOverOverlay;
        const title = this.ui.gameOverTitle;
        const details = this.ui.gameOverDetails;
        const scores = this.ui.finalScores;

        if (state.phase === "GAME_OVER_WIN" && state.winner_index !== null) {
            const winner = state.players[state.winner_index];
            const isWinner = state.winner_index === this.playerSeat;

            title.textContent = isWinner ? "🎉 You Win!" : "Game Over";

            details.innerHTML = `
                <p class="winner">${winner.name} wins!</p>
                <p class="yaku-list">Yaku: ${
                    state.winning_yaku.join(", ") || "None"
                }</p>
            `;
        } else {
            title.textContent = "Draw Game";
            details.innerHTML = "<p>Exhaustive Draw - No Winner</p>";
        }

        // Render final scores
        scores.innerHTML = "<h3>Final Scores</h3>";
        const sortedPlayers = [...state.players].sort(
            (a, b) => b.score - a.score
        );

        sortedPlayers.forEach((player) => {
            const isWinner = player.index === state.winner_index;
            const row = document.createElement("div");
            row.className = `score-row ${isWinner ? "winner" : ""}`;
            row.innerHTML = `
                <span class="name">${player.name}</span>
                <span class="score">${player.score.toLocaleString()}</span>
            `;
            scores.appendChild(row);
        });

        overlay.classList.remove("hidden");
    }

    /**
     * Toggle in-game menu
     */
    toggleMenu(show) {
        this.ui.menuOverlay.classList.toggle("hidden", !show);
    }

    /**
     * Quit current game
     */
    quitGame() {
        this.toggleMenu(false);
        this.returnToMenu();
    }

    /**
     * Restart game
     */
    restartGame() {
        this.ui.gameOverOverlay.classList.add("hidden");

        if (this.socket) {
            this.socket.emit("restart_game", {
                session_id: this.sessionId,
            });

            setTimeout(() => {
                this.socket.emit("start_game", {
                    session_id: this.sessionId,
                });
            }, 500);
        }
    }

    /**
     * Return to main menu
     */
    returnToMenu() {
        this.ui.gameOverOverlay.classList.add("hidden");
        this.showScreen("menu");

        // Disconnect socket
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }

        // Reset state
        this.gameState = null;
        this.playerSeat = null;
        this.selectedTileIndex = null;
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyPress(e) {
        // Only handle in game screen
        if (!this.ui.gameScreen.classList.contains("active")) return;

        switch (e.key) {
            case "Escape":
                if (this.ui.gameOverOverlay.classList.contains("hidden")) {
                    this.toggleMenu(
                        !this.ui.menuOverlay.classList.contains("hidden")
                    );
                }
                break;

            case "Enter":
                if (this.selectedTileIndex !== null) {
                    this.discardTile();
                }
                break;

            case "1":
            case "2":
            case "3":
            case "4":
            case "5":
            case "6":
            case "7":
            case "8":
            case "9":
            case "0":
                // Quick select tiles by number
                const idx = e.key === "0" ? 9 : parseInt(e.key) - 1;
                const player = this.gameState?.players.find(
                    (p) => p.index === this.playerSeat
                );
                if (player && idx < player.hand.length) {
                    this.handleTileClick(idx, player.hand[idx]);
                }
                break;
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;

        this.ui.toastContainer.appendChild(toast);

        // Auto remove after delay
        setTimeout(() => {
            toast.classList.add("removing");
            setTimeout(() => toast.remove(), 200);
        }, 3000);
    }

    /**
     * Hide overlay by type
     */
    hideOverlay(type) {
        if (type === "gameOver") {
            this.ui.gameOverOverlay.classList.add("hidden");
        } else if (type === "menu") {
            this.ui.menuOverlay.classList.add("hidden");
        }
    }
}

// Initialise game when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    window.game = new MahjongGame();
});
