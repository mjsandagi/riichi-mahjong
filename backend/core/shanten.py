from .tiles import Suit, Tile, Rank, Honour

class ShantenCalculator:
    def __init__(self):
        self.MAX_SHANTEN = 8

    def calculate_shanten(self, hand_tiles):
        """
        Main entry point. Returns the minimum shanten of all 3 patterns.
        """
        # 1. Convert List[Tile] -> Frequency Array (Indices 0-33)
        counts = self._to_frequency_table(hand_tiles)
        return self._calculate_from_counts(counts)

    def get_waits(self, hand_tiles):
        """
        Returns a list of Tile objects that would complete the hand.
        Only accurate if the hand is Tenpai (0-shanten).
        """
        waits = []
        counts = self._to_frequency_table(hand_tiles)
        
        # Iterate through every possible tile index (0-33)
        for i in range(34):
            # Try adding this tile to the hand (imaginary draw)
            if counts[i] < 4: # Can't have more than 4 of a kind
                counts[i] += 1
                
                # Check if this makes the hand a winner (-1 shanten)
                if self._calculate_from_counts(counts) == -1:
                    waits.append(self._index_to_tile(i))
                
                # Backtrack (remove the imaginary tile)
                counts[i] -= 1
                
        return waits

    # --- Internal Helpers ---
    
    def _calculate_from_counts(self, counts):
        """Calculates shanten from a frequency table."""
        s_standard = self._get_standard_shanten(counts)
        s_chitoi   = self._get_chitoitsu_shanten(counts)
        s_kokushi  = self._get_kokushi_shanten(counts)
        return min(s_standard, s_chitoi, s_kokushi)

    def _to_frequency_table(self, tiles):
        # Index Mapping:
        # 0-8:   Man 1-9
        # 9-17:  Pin 1-9
        # 18-26: Sou 1-9
        # 27-33: Honours (East, S, W, N, W, G, R)
        counts = [0] * 34
        for t in tiles:
            index = -1
            if t.suit == Suit.MAN: index = t.value - 1
            elif t.suit == Suit.PIN: index = 9 + (t.value - 1)
            elif t.suit == Suit.SOU: index = 18 + (t.value - 1)
            elif t.suit == Suit.HONOUR: index = 27 + (t.value - 1)
            
            if 0 <= index < 34:
                counts[index] += 1
        return counts

    def _index_to_tile(self, index):
        """Reconstructs a Tile object from a frequency index."""
        if 0 <= index < 9:
            return Tile(Suit.MAN, index + 1)
        elif 9 <= index < 18:
            return Tile(Suit.PIN, index - 9 + 1)
        elif 18 <= index < 27:
            return Tile(Suit.SOU, index - 18 + 1)
        elif 27 <= index < 34:
            return Tile(Suit.HONOUR, index - 27 + 1)
        return None

    # --- Logic 1: Seven Pairs (Chitoitsu) ---
    def _get_chitoitsu_shanten(self, counts):
        pairs = 0
        unique_tiles = 0
        for c in counts:
            if c >= 2: pairs += 1
            if c >= 1: unique_tiles += 1
        return 6 - pairs + max(0, 7 - unique_tiles)

    # --- Logic 2: Thirteen Orphans (Kokushi Musou) ---
    def _get_kokushi_shanten(self, counts):
        yaochuu_indices = [0, 8, 9, 17, 18, 26] + list(range(27, 34))
        unique_count = 0
        has_pair = False
        for idx in yaochuu_indices:
            if counts[idx] > 0:
                unique_count += 1
            if counts[idx] >= 2:
                has_pair = True
        return 13 - unique_count - (1 if has_pair else 0)

    # --- Logic 3: Standard (4 Sets + 1 Pair) ---
    def _get_standard_shanten(self, counts):
        return self._recurse_standard(counts, 0)

    def _recurse_standard(self, counts, index):
        while index < 34 and counts[index] == 0:
            index += 1
        
        if index >= 34:
            return self._calculate_final_standard_shanten(counts)

        best_score = 99
        
        # 1. Try Set (Triplet)
        if counts[index] >= 3:
            counts[index] -= 3
            best_score = min(best_score, self._recurse_standard(counts, index) - 2)
            counts[index] += 3 

        # 2. Try Run (Sequence)
        if index < 27 and index % 9 < 7:
            if counts[index] >= 1 and counts[index+1] >= 1 and counts[index+2] >= 1:
                counts[index] -= 1
                counts[index+1] -= 1
                counts[index+2] -= 1
                best_score = min(best_score, self._recurse_standard(counts, index) - 2)
                counts[index] += 1
                counts[index+1] += 1
                counts[index+2] += 1 

        # 3. Skip
        best_score = min(best_score, self._recurse_standard(counts, index + 1))
        return best_score

    def _calculate_final_standard_shanten(self, counts):
        pairs = 0
        taatsu = 0 
        
        temp_counts = list(counts) 
        
        for i in range(34):
            if temp_counts[i] >= 2:
                pairs += 1
                temp_counts[i] -= 2
        
        for i in range(27): 
            if temp_counts[i] > 0:
                # Neighbours (e.g. 2m 3m)
                if i % 9 < 8 and temp_counts[i+1] > 0:
                    taatsu += 1
                    temp_counts[i] -= 1
                    temp_counts[i+1] -= 1
                # Kanchan (e.g. 2m 4m)
                elif i % 9 < 7 and temp_counts[i+2] > 0:
                    taatsu += 1
                    temp_counts[i] -= 1
                    temp_counts[i+2] -= 1

        potential_sets = taatsu
        if pairs > 0:
            potential_sets += (pairs - 1)
            return 8 - potential_sets - 1 
        else:
             return 8 - potential_sets