from .tiles import Suit, Tile, Rank, Honour
from .shanten import ShantenCalculator

def test_shanten():
    calc = ShantenCalculator()

    # 1. Create a Tenpai Hand (13 tiles, waiting for 1)
    # Hand: 123m 456m 789m 11p 55s (Waiting for 1p or 5s)
    hand = [
        Tile(Suit.MAN, Rank.ONE), Tile(Suit.MAN, Rank.TWO), Tile(Suit.MAN, Rank.THREE),
        Tile(Suit.MAN, Rank.FOUR), Tile(Suit.MAN, Rank.FIVE), Tile(Suit.MAN, Rank.SIX),
        Tile(Suit.MAN, Rank.SEVEN), Tile(Suit.MAN, Rank.EIGHT), Tile(Suit.MAN, Rank.NINE),
        Tile(Suit.PIN, Rank.ONE), Tile(Suit.PIN, Rank.ONE),
        Tile(Suit.SOU, Rank.FIVE), Tile(Suit.SOU, Rank.FIVE),
    ]

    shanten = calc.calculate_shanten(hand)
    print(f"Hand Shanten: {shanten}") 
    # Expected: 0 (Tenpai)

    # 2. Add the winning tile (1p)
    hand.append(Tile(Suit.PIN, Rank.ONE))
    shanten = calc.calculate_shanten(hand)
    print(f"Winning Hand Shanten: {shanten}")
    # Expected: -1 (Agari)

if __name__ == "__main__":
    test_shanten()