import pytest
from core.scorer import Scorer
from core.tiles import Tile, Suit, Rank, Honour

# Helper to create tiles quickly
def t(suit, value):
    return Tile(suit, value)

class TestScoring:
    def setup_method(self):
        self.scorer = Scorer()

    def test_tanyao(self):
        """Test tanyao (all simples) - no terminals or honors"""
        # Hand: 234m 345p 567s 666m 88s
        hand = [
            t(Suit.MAN, 2), t(Suit.MAN, 3), t(Suit.MAN, 4),
            t(Suit.PIN, 3), t(Suit.PIN, 4), t(Suit.PIN, 5),
            t(Suit.SOU, 5), t(Suit.SOU, 6), t(Suit.SOU, 7),
            t(Suit.MAN, 6), t(Suit.MAN, 6), t(Suit.MAN, 6),
            t(Suit.SOU, 8), t(Suit.SOU, 8)
        ]
        
        # Scorer expects (hand, melds). Assuming closed hand (melds=[]).
        yaku_list = self.scorer.check_yaku(hand, melds=[])
        
        # Check if string matches (flexible match)
        assert any("tanyao" in y.lower() for y in yaku_list)

    def test_yakuhai_dragon(self):
        """Test dragon triplet scoring"""
        # Hand: 123m 456p 789s White-White-White 11m
        hand = [
            t(Suit.MAN, 1), t(Suit.MAN, 2), t(Suit.MAN, 3),
            t(Suit.PIN, 4), t(Suit.PIN, 5), t(Suit.PIN, 6),
            t(Suit.SOU, 7), t(Suit.SOU, 8), t(Suit.SOU, 9),
            t(Suit.HONOUR, 5), t(Suit.HONOUR, 5), t(Suit.HONOUR, 5), # White Dragon
            t(Suit.MAN, 1), t(Suit.MAN, 1) # Pair
        ]
        
        yaku_list = self.scorer.check_yaku(hand, melds=[])
        assert any("yakuhai" in y.lower() for y in yaku_list)

    @pytest.mark.skip(reason="Logic not yet implemented in scorer.py")
    def test_pinfu(self):
        """Test pinfu (all sequences, no fu)"""
        # FIX: The original test had 5 sets. Pinfu needs 4 sequences + 1 pair.
        hand = [
            # Seq 1
            t(Suit.MAN, 2), t(Suit.MAN, 3), t(Suit.MAN, 4),
            # Seq 2
            t(Suit.PIN, 3), t(Suit.PIN, 4), t(Suit.PIN, 5),
            # Seq 3
            t(Suit.SOU, 5), t(Suit.SOU, 6), t(Suit.SOU, 7),
            # Seq 4 (The Wait: 2-3s waiting for 4s, completed here)
            t(Suit.SOU, 2), t(Suit.SOU, 3), t(Suit.SOU, 4),
            # Pair (Head) - Must NOT be Yakuhai (Dragons/Winds)
            t(Suit.MAN, 8), t(Suit.MAN, 8) 
        ]
        
        yaku_list = self.scorer.check_yaku(hand, melds=[])
        assert any("pinfu" in y.lower() for y in yaku_list)

    @pytest.mark.skip(reason="Logic not yet implemented in scorer.py")
    def test_toitoi(self):
        """Test toitoi (all triplets)"""
        hand = [
            t(Suit.MAN, 2), t(Suit.MAN, 2), t(Suit.MAN, 2),
            t(Suit.PIN, 5), t(Suit.PIN, 5), t(Suit.PIN, 5),
            t(Suit.SOU, 8), t(Suit.SOU, 8), t(Suit.SOU, 8),
            t(Suit.HONOUR, 1), t(Suit.HONOUR, 1), t(Suit.HONOUR, 1),
            t(Suit.MAN, 7), t(Suit.MAN, 7)
        ]
        yaku_list = self.scorer.check_yaku(hand, melds=[])
        assert any("toitoi" in y.lower() for y in yaku_list)

    @pytest.mark.skip(reason="Logic not yet implemented in scorer.py")
    def test_honitsu(self):
        """Test honitsu (half flush - one suit plus honors)"""
        hand = [
            t(Suit.MAN, 2), t(Suit.MAN, 3), t(Suit.MAN, 4),
            t(Suit.MAN, 5), t(Suit.MAN, 6), t(Suit.MAN, 7),
            t(Suit.MAN, 8), t(Suit.MAN, 8), t(Suit.MAN, 8),
            t(Suit.HONOUR, 1), t(Suit.HONOUR, 1), t(Suit.HONOUR, 1),
            t(Suit.MAN, 1), t(Suit.MAN, 1)
        ]
        yaku_list = self.scorer.check_yaku(hand, melds=[])
        assert any("honitsu" in y.lower() for y in yaku_list)

    @pytest.mark.skip(reason="Logic not yet implemented in scorer.py")
    def test_chinitsu(self):
        """Test chinitsu (full flush - one suit only)"""
        hand = [
            t(Suit.MAN, 1), t(Suit.MAN, 1), t(Suit.MAN, 1),
            t(Suit.MAN, 2), t(Suit.MAN, 3), t(Suit.MAN, 4),
            t(Suit.MAN, 5), t(Suit.MAN, 6), t(Suit.MAN, 7),
            t(Suit.MAN, 8), t(Suit.MAN, 8), t(Suit.MAN, 8),
            t(Suit.MAN, 9), t(Suit.MAN, 9)
        ]
        yaku_list = self.scorer.check_yaku(hand, melds=[])
        assert any("chinitsu" in y.lower() for y in yaku_list)