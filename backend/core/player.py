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