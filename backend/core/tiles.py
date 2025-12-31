from enum import IntEnum

class Suit(IntEnum):
    MAN = 1 # Numbers
    PIN = 2 # Circles (coins)
    SOU = 3 # Bamboo
    HONOUR = 4 # Wind and Dragon tiles

class TileType(IntEnum):
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

    # Honour: Wind (Kazehai) (what happened to Never-Eat-Shredded-Wheat?)
    EAST = 1
    SOUTH = 2
    WEST = 3
    NORTH = 4

    # Honour: Dragon (Sangenpai)
    WHITE = 1
    GREEN = 2
    RED = 3
    
class Tile:
    def __init__(self, suit: Suit, value: TileType, is_red: bool = False):
        self.suit = suit
        self.value = value
        self.is_red = is_red # Needed for "Akadora" (Red Fives)

        self.id = f"{value.value}_{suit.name}{'_RED' if is_red else ''}"
    
    # Returns a short string like "1m", "5p_red", "East" for debugging.
    def __repr__(self):
        suffix = "_r" if self.is_red else ""
        if self.suit == Suit.MAN: 
            return f"{self.value.value}m{suffix}"
        if self.suit == Suit.PIN: 
            return f"{self.value.value}p{suffix}"
        if self.suit == Suit.SOU: 
            return f"{self.value.value}s{suffix}"

        # Honours
        if self.suit == Suit.HONOUR:
            names = {1: "East", 2: "South", 3: "West", 4: "North", 
                     5: "Haku", # White Dragon 
                     6: "Hatsu", # Green Dragon
                     7: "Chun"} # Red Dragon
            return names.get(self.value.value, "?")
        
        return "?"
    
    # Comparison logic
    def __lt__(self, other):
        """
        Allows sorting: [1m, 2p, 1s].sort() works automatically.
        """
        if self.suit != other.suit:
            return self.suit < other.suit
        if self.value != other.value:
            return self.value < other.value
        
        # If the suits and values are equal, red comes after black 
        return self.is_red and not other.is_red

    def __eq__(self, other):
        """
        Strict equality: Red 5p != White 5p
        """
        if not isinstance(other, Tile):
            return False    
        return self.suit == other.suit and self.value == other.value and self.is_red == other.is_red
    
    @property
    def is_honour(self):
        return self.suit == Suit.HONOUR
    
    @property
    def is_terminal(self):
        return self.suit != Suit.HONOUR and (self.value in (1, 9))
    
    @property
    def is_yaochuu(self):
        """
        True for Terminals AND Honours (Critical for checking Yaku)
        """
        return self.is_terminal or self.is_honour
    

def create_standard_deck(akadora=True):
    """
    Generates the standard 136-tile set
    """
    deck = []

    # 1. Man, Pin, and Sou
    for suit in [Suit.MAN, Suit.PIN, Suit.SOU]:
        for val in range(1, 10):
            count = 4
            if akadora and val == 5:
                # If akadora is on, we add 1 red five and and 3 black fives
                deck.append(Tile(suit, TileType(val), is_red=True))
                count = 3
            for _ in range(count):
                deck.append(Tile(suit, TileType(val)))

    # 2. Honours
    for val in range(1, 8):
        for _ in range(4):
            deck.append(Tile(Suit.HONOUR, TileType(val)))

    return deck