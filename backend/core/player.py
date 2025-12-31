from tiles import Suit, Tile

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.discards = []
        self.open_melds = [] # Stores active calls
        
        # --- NEW ATTRIBUTES ---
        self.score = 25000       # Standard starting score
        self.is_riichi = False   # Is he or she in Riichi?

    def draw_tile(self, tile):
        if not tile: return
        self.hand.append(tile)

    def discard_tile(self, index):
        if 0 <= index < len(self.hand):
            tile = self.hand.pop(index)
            self.discards.append(tile)
            self.hand.sort()
            return tile
        return None

    def sort_hand(self):
        self.hand.sort()

    def __repr__(self):
        # Show hand + melds
        return f"{self.name}: {self.hand} {self.open_melds if self.open_melds else ''}"

    # --- Properties ---
    @property
    def is_menzen(self):
        """Returns True if hand is closed (no open melds). Essential for Riichi."""
        return len(self.open_melds) == 0

    # --- Call Detection ---
    def can_pon(self, tile: Tile):
        # Check if we have at least 2 of these
        return sum(1 for t in self.hand if t == tile) >= 2

    # --- Call Execution ---
    def execute_pon(self, tile: Tile):
        """
        Removes 2 matching tiles, creates a Pon meld.
        """
        removed = 0
        new_hand = []
        for t in self.hand:
            # Remove only the first 2 matches we find
            if t == tile and removed < 2:
                removed += 1
            else:
                new_hand.append(t)
        
        self.hand = new_hand
        # Store meld (For now, just a string representation)
        self.open_melds.append(f"[Pon: {tile} {tile} {tile}]")
        return True
    
    # --- Chi Detection ---
    def can_chi(self, tile: Tile):
        """
        Returns a list of tuples containing the indices of tiles that can form a Chi.
        Example result: [(0, 1), (1, 2)] meaning indices 0&1 or 1&2 can form chi with target.
        """
        if tile.is_honour: return [] # Cannot Chi Honours
        
        # We need to look for neighbors. 
        # For simplicity, let's find matching values in the same suit.
        same_suit_indices = [i for i, t in enumerate(self.hand) if t.suit == tile.suit]
        
        options = []
        val = tile.value
        
        # We need to find specific indices for (val-2, val-1), (val-1, val+1), (val+1, val+2)
        # Helper to find index of a specific value in our subset
        def find_idx(v):
            for idx in same_suit_indices:
                if self.hand[idx].value == v:
                    return idx
            return None

        # 1. Low Chi: (val-2, val-1) + val
        # e.g. Hand has 1,2. Discard is 3.
        c1, c2 = find_idx(val-2), find_idx(val-1)
        if c1 is not None and c2 is not None:
            options.append((c1, c2))

        # 2. Mid Chi: (val-1, val+1) + val
        # e.g. Hand has 2,4. Discard is 3.
        c1, c2 = find_idx(val-1), find_idx(val+1)
        if c1 is not None and c2 is not None:
            options.append((c1, c2))

        # 3. High Chi: (val+1, val+2) + val
        # e.g. Hand has 4,5. Discard is 3.
        c1, c2 = find_idx(val+1), find_idx(val+2)
        if c1 is not None and c2 is not None:
            options.append((c1, c2))
            
        return options

    def execute_chi(self, tile: Tile, indices):
        """
        Removes the two tiles at the specified indices and forms a sequence meld.
        """
        # We must sort indices descending to pop correctly without shifting
        idx_a, idx_b = sorted(indices, reverse=True)
        
        t1 = self.hand.pop(idx_a)
        t2 = self.hand.pop(idx_b)
        
        # Sort the meld components for display (e.g. 3,4,5)
        meld_tiles = sorted([t1, t2, tile])
        self.open_melds.append(f"[Chi: {meld_tiles[0]} {meld_tiles[1]} {meld_tiles[2]}]")
        return True
    
    def can_kan(self, tile: Tile):
        """Returns True if hand has 3 matches for the discard (Daiminkan)."""
        return sum(1 for t in self.hand if t == tile) == 3

    def execute_kan(self, tile: Tile):
        """
        Removes 3 tiles, creates a Kan meld.
        """
        removed = 0
        new_hand = []
        for t in self.hand:
            if t == tile and removed < 3:
                removed += 1
            else:
                new_hand.append(t)
        
        self.hand = new_hand
        self.open_melds.append(f"[Kan: {tile} {tile} {tile} {tile}]")
        return True