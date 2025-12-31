import random
from tiles import create_standard_deck  # Import the function from your tile file

class Wall:
    def __init__(self):
        self.tiles = create_standard_deck()
        random.shuffle(self.tiles)
        
        # The Dead Wall (Wangpai) is the last 14 tiles.
        self.dead_wall = self.tiles[-14:] 
        self.tiles = self.tiles[:-14]
        
        # Dora Indicators: start with 1 visible
        self.dora_indicators = [self.dead_wall[5]] 
        
    def draw(self):
        if not self.tiles:
            return None 
        return self.tiles.pop()
    
    @property
    def remaining(self):
        return len(self.tiles)

    def reveal_kan_dora(self):
        current_count = len(self.dora_indicators)
        if current_count < 5:
            next_index = 5 + (current_count * 2) 
            self.dora_indicators.append(self.dead_wall[next_index])