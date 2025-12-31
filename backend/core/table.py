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
    