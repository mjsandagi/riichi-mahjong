from .tiles import Suit, Tile

class Scorer:
    def __init__(self):
        pass

    def check_yaku(self, hand, melds, is_riichi=False):
        """
        Returns a list of Yaku names found in the hand.
        If list is empty, the hand is not a legal win (Kuitan/No Yaku).
        """
        yaku_list = []
        
        # Merge hand and melds for checking certain Yaku
        # Note: 'melds' in Player are strings currently. 
        # For a real scorer, we need Melds to be objects or lists of Tiles.
        # For this version, we will inspect the 'hand' (closed tiles) + simple assumption on melds.
        
        # 1. TANYAO (All Simples)
        # Condition: No Honours, No 1s, No 9s.
        if self._is_tanyao(hand, melds):
            yaku_list.append("Tanyao (All Simples)")

        # 2. YAKUHAI (Dragons)
        # Condition: Triplet of White, Green, or Red.
        if self._is_yakuhai(hand, melds):
            yaku_list.append("Yakuhai (Dragons)")
            
        return yaku_list

    def _is_tanyao(self, hand, melds):
        # Check closed tiles
        for tile in hand:
            if tile.is_yaochuu: # defined in Tile class
                return False
        
        # Check melds (String parsing hack for now, ideally fix Meld structure)
        # If string contains "1", "9", "East", "West", "Haku", etc.
        # This is fragile but works for the current text-based implementation
        for m in melds:
            if any(x in m for x in ["1", "9", "East", "South", "West", "North", "Haku", "Hatsu", "Chun"]):
                return False
                
        return True

    def _is_yakuhai(self, hand, melds):
        # We need to count triplets. 
        # Since we don't have a full "Hand Partition" algorithm (decomposing hand into sets),
        # checking Yakuhai in a closed hand is tricky without the decomposition results.
        
        # Simplified Check: Do we have 3 of a Dragon in the raw list?
        # (This is slightly inaccurate because those 3 might be part of a sequence in rare cases, 
        # but Dragons cannot form sequences, so actually, this IS safe!)
        
        dragons = ["Haku", "Hatsu", "Chun"]
        
        # Check closed hand
        counts = {}
        for tile in hand:
            if tile.suit == Suit.HONOUR and tile.value in (5,6,7):
                counts[tile.value] = counts.get(tile.value, 0) + 1
        
        for val, count in counts.items():
            if count >= 3:
                return True
                
        # Check Melds
        for m in melds:
            if any(d in m for d in dragons):
                return True
                
        return False