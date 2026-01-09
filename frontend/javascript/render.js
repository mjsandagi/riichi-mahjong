/**
 * Riichi Mahjong - Tile Renderer
 *
 * Handles rendering of mahjong tiles with a clean, minimalist design
 */

const TileRenderer = {
    // Suit constants (match backend)
    SUIT: {
        MAN: 1,
        PIN: 2,
        SOU: 3,
        HONOUR: 4,
    },

    // Honour tile mappings
    HONOUR_NAMES: {
        1: "E", // East
        2: "S", // South
        3: "W", // West
        4: "N", // North
        5: "白", // Haku (White Dragon)
        6: "發", // Hatsu (Green Dragon)
        7: "中", // Chun (Red Dragon)
    },

    HONOUR_FULL_NAMES: {
        1: "East",
        2: "South",
        3: "West",
        4: "North",
        5: "White",
        6: "Green",
        7: "Red",
    },

    SUIT_NAMES: {
        1: "Man",
        2: "Pin",
        3: "Sou",
    },

    SUIT_CLASSES: {
        1: "man",
        2: "pin",
        3: "sou",
        4: "honour",
    },

    // Chinese numerals for Man tiles
    MAN_NUMERALS: {
        1: "一",
        2: "二",
        3: "三",
        4: "四",
        5: "五",
        6: "六",
        7: "七",
        8: "八",
        9: "九",
    },

    /**
     * Create a tile element from tile data
     * @param {Object} tile - Tile data {suit, value, is_red}
     * @param {Object} options - Rendering options
     * @returns {HTMLElement}
     */
    createTile(tile, options = {}) {
        const {
            size = "normal", // 'normal', 'small', 'mini'
            selectable = false,
            selected = false,
            index = null,
            showBack = false,
            animated = false,
            animationType = null,
        } = options;

        const tileEl = document.createElement("div");
        tileEl.className = "tile";

        // Add size class
        if (size !== "normal") {
            tileEl.classList.add(size);
        }

        // Show back of tile
        if (showBack) {
            tileEl.classList.add("back");
            return tileEl;
        }

        // Add suit class
        const suitClass = this.SUIT_CLASSES[tile.suit];
        if (suitClass) {
            tileEl.classList.add(suitClass);
        }

        // Add red dora styling
        if (tile.is_red) {
            tileEl.classList.add("red");
        }

        // Selectable/selected states
        if (selectable) {
            tileEl.classList.add("selectable");
            tileEl.dataset.index = index;
        }

        if (selected) {
            tileEl.classList.add("selected");
        }

        // Animation classes
        if (animated && animationType) {
            tileEl.classList.add(animationType);
        }

        // Create tile content
        const valueEl = document.createElement("div");
        valueEl.className = "tile-value";

        const suitEl = document.createElement("div");
        suitEl.className = "tile-suit";

        // Set content based on tile type
        if (tile.suit === this.SUIT.HONOUR) {
            valueEl.textContent = this.HONOUR_NAMES[tile.value] || "?";
            suitEl.textContent = "";
        } else if (tile.suit === this.SUIT.MAN) {
            // Use Chinese numerals for Man tiles
            valueEl.textContent = this.MAN_NUMERALS[tile.value] || tile.value;
            suitEl.textContent = "萬";
        } else if (tile.suit === this.SUIT.PIN) {
            // Use circles representation
            valueEl.textContent = this.getPinDisplay(tile.value);
            suitEl.textContent = "";
        } else if (tile.suit === this.SUIT.SOU) {
            // Bamboo - use number with bamboo character
            valueEl.textContent = tile.value;
            suitEl.textContent = "Sou";
        }

        tileEl.appendChild(valueEl);
        if (suitEl.textContent) {
            tileEl.appendChild(suitEl);
        }

        // Store tile data
        tileEl.dataset.suit = tile.suit;
        tileEl.dataset.value = tile.value;
        tileEl.dataset.isRed = tile.is_red || false;

        return tileEl;
    },

    /**
     * Get Pin (circles) display - simplified circles representation
     * @param {number} value
     * @returns {string}
     */
    getPinDisplay(value) {
        // Use simple numbers with a circle indicator
        const circles = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"];
        return circles[value - 1] || value;
    },

    /**
     * Create a back-facing tile
     * @param {string} size
     * @returns {HTMLElement}
     */
    createBackTile(size = "small") {
        return this.createTile({ suit: 0, value: 0 }, { size, showBack: true });
    },

    /**
     * Render a hand of tiles
     * @param {Array} tiles - Array of tile data
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Rendering options
     */
    renderHand(tiles, container, options = {}) {
        const {
            selectable = false,
            selectedIndices = new Set(),
            size = "normal",
            showBack = false,
            onTileClick = null,
        } = options;

        container.innerHTML = "";

        if (!tiles || tiles.length === 0) {
            return;
        }

        tiles.forEach((tile, index) => {
            const tileEl = this.createTile(tile, {
                size,
                selectable,
                selected: selectedIndices.has(index),
                index,
                showBack,
            });

            if (selectable && onTileClick) {
                tileEl.addEventListener("click", () =>
                    onTileClick(index, tile)
                );
            }

            container.appendChild(tileEl);
        });
    },

    /**
     * Render opponent's hand (back of tiles)
     * @param {number} count - Number of tiles
     * @param {HTMLElement} container
     * @param {boolean} vertical
     */
    renderOpponentHand(count, container, vertical = false) {
        container.innerHTML = "";

        for (let i = 0; i < count; i++) {
            const tileEl = this.createBackTile("small");
            container.appendChild(tileEl);
        }
    },

    /**
     * Render discards (river/kawa)
     * @param {Array} tiles
     * @param {HTMLElement} container
     */
    renderRiver(tiles, container) {
        container.innerHTML = "";

        if (!tiles || tiles.length === 0) {
            return;
        }

        tiles.forEach((tile, index) => {
            const tileEl = this.createTile(tile, {
                size: "mini",
                animated: index === tiles.length - 1,
                animationType: "discarded",
            });
            container.appendChild(tileEl);
        });
    },

    /**
     * Render dora indicators
     * @param {Array} tiles
     * @param {HTMLElement} container
     */
    renderDora(tiles, container) {
        container.innerHTML = "";

        if (!tiles || tiles.length === 0) {
            return;
        }

        tiles.forEach((tile) => {
            const tileEl = this.createTile(tile, { size: "small" });
            container.appendChild(tileEl);
        });
    },

    /**
     * Render waiting tiles
     * @param {Array} tiles
     * @param {HTMLElement} container
     */
    renderWaits(tiles, container) {
        container.innerHTML = "";

        if (!tiles || tiles.length === 0) {
            return;
        }

        tiles.forEach((tile) => {
            const tileEl = this.createTile(tile, { size: "small" });
            container.appendChild(tileEl);
        });
    },

    /**
     * Parse meld string to structured data
     * Format: "[Pon: 5m 5m 5m]" or "[Chi: 3p 4p 5p]"
     * @param {string} meldStr
     * @returns {Object}
     */
    parseMeldString(meldStr) {
        // Extract meld type
        const ponMatch = meldStr.match(/\[Pon:/);
        const chiMatch = meldStr.match(/\[Chi:/);
        const kanMatch = meldStr.match(/\[Kan:/);

        const type = ponMatch
            ? "pon"
            : chiMatch
            ? "chi"
            : kanMatch
            ? "kan"
            : "unknown";

        // Extract tiles from string
        // Format: "Xm" (man), "Xp" (pin), "Xs" (sou), or honour names
        const tileRegex =
            /(\d)[mps]|East|South|West|North|White|Green|Red|Haku|Hatsu|Chun/gi;
        const matches = [...meldStr.matchAll(tileRegex)];

        const tiles = matches.map((match) => {
            const str = match[0].toLowerCase();

            // Check for honours
            const honourMap = {
                east: { suit: 4, value: 1 },
                south: { suit: 4, value: 2 },
                west: { suit: 4, value: 3 },
                north: { suit: 4, value: 4 },
                white: { suit: 4, value: 5 },
                haku: { suit: 4, value: 5 },
                green: { suit: 4, value: 6 },
                hatsu: { suit: 4, value: 6 },
                red: { suit: 4, value: 7 },
                chun: { suit: 4, value: 7 },
            };

            if (honourMap[str]) {
                return { ...honourMap[str], is_red: false };
            }

            // Parse suited tiles
            const value = parseInt(match[1]);
            const suitChar = str.slice(-1);
            const suitMap = { m: 1, p: 2, s: 3 };

            return {
                suit: suitMap[suitChar] || 1,
                value: value,
                is_red: false,
            };
        });

        return { type, tiles };
    },

    /**
     * Render a meld
     * @param {string} meldStr
     * @param {HTMLElement} container
     */
    renderMeld(meldStr, container) {
        const meldData = this.parseMeldString(meldStr);

        const meldEl = document.createElement("div");
        meldEl.className = "meld";

        meldData.tiles.forEach((tile) => {
            const tileEl = this.createTile(tile, { size: "small" });
            meldEl.appendChild(tileEl);
        });

        container.appendChild(meldEl);
    },

    /**
     * Render all melds for a player
     * @param {Array} melds - Array of meld strings
     * @param {HTMLElement} container
     */
    renderMelds(melds, container) {
        container.innerHTML = "";

        if (!melds || melds.length === 0) {
            return;
        }

        melds.forEach((meldStr) => {
            this.renderMeld(meldStr, container);
        });
    },

    /**
     * Get tile name for display
     * @param {Object} tile
     * @returns {string}
     */
    getTileName(tile) {
        if (tile.suit === this.SUIT.HONOUR) {
            return this.HONOUR_FULL_NAMES[tile.value] || "Unknown";
        }

        const suitName = this.SUIT_NAMES[tile.suit] || "?";
        const redSuffix = tile.is_red ? " (Red)" : "";
        return `${tile.value} ${suitName}${redSuffix}`;
    },
};

// Make available globally
window.TileRenderer = TileRenderer;
