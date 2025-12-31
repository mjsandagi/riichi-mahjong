from tiles import Suit, Tile, Rank, Honour

class ShantenCalculator:
    def __init__(self):
        self.MAX_SHANTEN = 8

    def calculate_shanten(self, hand_tiles):
        """
        Main entry point. Returns the minimum shanten of all 3 patterns.
        """
        # 1. Convert List[Tile] -> Frequency Array (Indices 0-33)
        counts = self._to_frequency_table(hand_tiles)

        # 2. Check the 3 patterns
        s_standard = self._get_standard_shanten(counts)
        s_chitoi   = self._get_chitoitsu_shanten(counts)
        s_kokushi  = self._get_kokushi_shanten(counts)

        return min(s_standard, s_chitoi, s_kokushi)

    # --- Helper: Convert Tiles to Array ---
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

    # --- Logic 1: Seven Pairs (Chitoitsu) ---
    def _get_chitoitsu_shanten(self, counts):
        # Need 7 distinct pairs.
        pairs = 0
        unique_tiles = 0
        
        for c in counts:
            if c >= 2: pairs += 1
            if c >= 1: unique_tiles += 1
            
        # Shanten = 6 - pairs + (deficit if < 7 types)
        # Normally shanten = 6 - pairs.
        # But if you have 4 copies of a tile (counts=[4]), it only counts as 2 pairs 
        # normally, but Chitoi REQUIRES distinct pairs. 
        # So we use standard formula:
        return 6 - pairs + max(0, 7 - unique_tiles)

    # --- Logic 2: Thirteen Orphans (Kokushi Musou) ---
    def _get_kokushi_shanten(self, counts):
        # Indices for Terminals (1,9) and Honours
        yaochuu_indices = [0, 8, 9, 17, 18, 26] + list(range(27, 34))
        
        unique_count = 0
        has_pair = False
        
        for idx in yaochuu_indices:
            if counts[idx] > 0:
                unique_count += 1
            if counts[idx] >= 2:
                has_pair = True
        
        # Standard Kokushi shanten: 13 - unique_count - (1 if has_pair else 0)
        return 13 - unique_count - (1 if has_pair else 0)

    # --- Logic 3: Standard (4 Sets + 1 Pair) ---
    def _get_standard_shanten(self, counts):
        # This requires recursion to find the optimal combination of sets.
        # Calculation: 8 - (2 * groups) - partial_groups - pair_present
        
        # We perform a Depth First Search (DFS)
        return self._recurse_standard(counts, 0)

    def _recurse_standard(self, counts, index):
        # Optimization: Skip empty indices
        while index < 34 and counts[index] == 0:
            index += 1
        
        # Base case: checked all tiles
        if index >= 34:
            # Calculate shanten for the remaining "leftovers"
            # We have extracted sets during recursion. Now we count potential sets.
            return self._calculate_final_standard_shanten(counts)

        # Recursive Step: Try to form groups starting at 'index'
        best_score = 99
        
        # 1. Try Set (Triplet - Koutsu)
        if counts[index] >= 3:
            counts[index] -= 3
            # Valid set found, add +1 to group count in recursion (simulated by -2 to shanten)
            best_score = min(best_score, self._recurse_standard(counts, index) - 2)
            counts[index] += 3 # Backtrack

        # 2. Try Run (Sequence - Shuntsu) -- Only for Number tiles (0-26)
        # Check suit boundaries: 0-6, 9-15, 18-24 are valid starts for runs
        if index < 27 and index % 9 < 7:
            if counts[index] >= 1 and counts[index+1] >= 1 and counts[index+2] >= 1:
                counts[index] -= 1
                counts[index+1] -= 1
                counts[index+2] -= 1
                best_score = min(best_score, self._recurse_standard(counts, index) - 2)
                counts[index] += 1
                counts[index+1] += 1
                counts[index+2] += 1 # Backtrack

        # 3. Don't use this tile in a set (skip it)
        # Just move to next index. The tile remains in 'counts' and will be counted as potential pair/taatsu later.
        best_score = min(best_score, self._recurse_standard(counts, index + 1))

        return best_score

    def _calculate_final_standard_shanten(self, counts):
        # Count pairs and potential sets (taatsu) in the leftovers
        groups = 0 # Groups were already handled by the recursion score (-2 per group)
        pairs = 0
        taatsu = 0 # Two tiles waiting to become a set (e.g., 1m 2m)
        
        temp_counts = list(counts) # Copy
        
        # 1. Find Pair
        for i in range(34):
            if temp_counts[i] >= 2:
                pairs += 1
                temp_counts[i] -= 2
        
        # 2. Find Taatsu (Neighbours or skip-neighbours) in remaining tiles
        for i in range(27): # Only numbers
            if temp_counts[i] > 0:
                # Neighbors (e.g. 2m 3m)
                if i % 9 < 8 and temp_counts[i+1] > 0:
                    taatsu += 1
                    temp_counts[i] -= 1
                    temp_counts[i+1] -= 1
                # Kanchan (e.g. 2m 4m)
                elif i % 9 < 7 and temp_counts[i+2] > 0:
                    taatsu += 1
                    temp_counts[i] -= 1
                    temp_counts[i+2] -= 1

        # We need 4 groups + 1 pair.
        # Basic formula: 8 - (2 * completed_groups) - taatsu - pairs
        # But limited: (groups + taatsu) <= 4, pairs <= 1
        
        # Note: The recursion returns a score relative to 8. 
        # Since we subtracted 2 for every group found in recursion, we start at 8.
        
        current_shanten = 8 
        
        # We can form at most 4 groups-like shapes (including the ones found in recursion)
        # But here we are only counting the taatsu/pairs.
        # Actually, simpler logic for the leftovers:
        
        # We have N groups from recursion.
        # We need to subtract:
        # - 1 for every Taatsu (up to 4 - groups)
        # - 1 for the Pair (if we have one)
        
        # However, because recursion subtracts 2 directly from shanten, we just return:
        # 8 (Base) - taatsu - pair
        
        # BUT: We must cap (taatsu + pair) usage based on "Standard Form" rules.
        # Max 4 sets allowed. Max 1 pair.
        
        # This part is tricky to get perfect without complex "Mentsu" structures.
        # Simplified Approximation:
        potential_sets = taatsu
        
        # If we have many pairs, one is the Head, others are potential sets (pon-wait)
        if pairs > 0:
            potential_sets += (pairs - 1) # Extra pairs count as taatsu
            # One pair acts as the Head
            return 8 - potential_sets - 1 
        else:
             # No pair? We need to use a taatsu to make a pair eventually? No.
             # Formula is roughly: 8 - taatsu
             return 8 - potential_sets