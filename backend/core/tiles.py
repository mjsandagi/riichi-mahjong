from enum import IntEnum, unique

class Suit(IntEnum):
    MAN = 1 # Numbers
    PIN = 2 # Circles (coins)
    SOU = 3 # Bamboo
    HONOUR = 4 # Wind and Dragon tiles

@unique
class Rank(IntEnum):
    # The numbered suits
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

@unique
class Honour(IntEnum):
    """
    Standard encoding for Honours:
    1-4: Winds (East, South, West, North)
    5-7: Dragons (White, Green, Red)
    """
    # Honour: Wind (Kazehai) (what happened to Never-Eat-Shredded-Wheat?)
    EAST = 1
    SOUTH = 2
    WEST = 3
    NORTH = 4

    # Honour: Dragon (Sangenpai)
    HAKU = 5
    HATSU = 6
    CHUN = 7
    
class Tile:
    def __init__(self, suit: Suit, value: int, is_red: bool = False):
        self.suit = suit
        self.value = value
        self.is_red = is_red # Needed for "Akadora" (Red Fives)
        self.id = f"{value}_{suit.name}{'_RED' if is_red else ''}"
    
    # Returns a short string like "1m", "5p_red", "East" for debugging.
    def __repr__(self):
        suffix = "_r" if self.is_red else ""
        
        if self.suit == Suit.HONOUR:
            # Map the integer 1-7 back to the Enum name for display
            try:
                return Honour(self.value).name.capitalize()
            except ValueError:
                return f"Unknown Honour ({self.value})"
        
        # Suited tiles
        char_map = {Suit.MAN: 'm', Suit.PIN: 'p', Suit.SOU: 's'}
        return f"{self.value}{char_map.get(self.suit, '?')}{suffix}"
    
    # --- Comparison Logic ---
    def __lt__(self, other):
        """Allows sorting: [1m, 2p, East].sort()"""
        if not isinstance(other, Tile):
            return NotImplemented
        
        # 1. Sort by Suit (Man < Pin < Sou < Honour)
        if self.suit != other.suit:
            return self.suit < other.suit
        
        # 2. Sort by Value (1..9 or 1..7)
        if self.value != other.value:
            return self.value < other.value
        
        # 3. Red dora comes after Black (arbitrary choice, but consistent)
        return self.is_red and not other.is_red

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return (self.suit == other.suit and 
                self.value == other.value and 
                self.is_red == other.is_red)
    
    def __hash__(self):
        return hash(self.id)
    
    @property
    def is_honour(self):
        return self.suit == Suit.HONOUR
    
    @property
    def is_terminal(self):
        return not self.is_honour and (self.value in (1, 9))
    
    @property
    def is_yaochuu(self):
        """
        True for Terminals AND Honours (Critical for checking Yaku)
        """
        return self.is_terminal or self.is_honour
    

def create_standard_deck(akadora=True):
    deck = []

    # 1. Suited Tiles (Man, Pin, Sou)
    for suit in [Suit.MAN, Suit.PIN, Suit.SOU]:
        for rank in Rank: # Iterate over the Enum 1-9
            val = rank.value
            count = 4
            
            # Handle Red Fives
            if akadora and val == 5:
                deck.append(Tile(suit, val, is_red=True))
                count = 3
            
            for _ in range(count):
                deck.append(Tile(suit, val))

    # 2. Honours (East..Chun)
    for honour in Honour: # Iterate over 1-7
        val = honour.value
        for _ in range(4):
            deck.append(Tile(Suit.HONOUR, val))

    return deck

# --- Verification ---
if __name__ == "__main__":
    deck = create_standard_deck()
    print(f"Deck Size: {len(deck)}") # Should be 136
    for tile in deck:
        print(tile.id)
    # Check Sorting
    hand = [
        Tile(Suit.HONOUR, Honour.CHUN), 
        Tile(Suit.MAN, Rank.ONE),
        Tile(Suit.PIN, Rank.FIVE, is_red=True)
    ]
    hand.sort()
    print(f"Sorted Hand: {hand}") 
    # Output: [1m, 5pr, Chun]

    # Check Terminal/Honour logic
    t1 = Tile(Suit.MAN, Rank.ONE)
    t2 = Tile(Suit.HONOUR, Honour.EAST)
    t3 = Tile(Suit.PIN, Rank.FIVE)
    
    print(f"1m is terminal? {t1.is_terminal}") # True
    print(f"East is terminal? {t2.is_terminal}") # False (It is Honour)
    print(f"East is yaochuu? {t2.is_yaochuu}")   # True
    print(f"5p is yaochuu? {t3.is_yaochuu}")     # False