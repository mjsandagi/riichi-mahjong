import time
from tiles import Tile, Suit, Rank
from wall import Wall
from player import Player
from shanten import ShantenCalculator
from scorer import Scorer
import ui  

class Game:
    def __init__(self):
        self.wall = Wall()
        self.players = [Player("East"), Player("South"), Player("West"), Player("North")]
        self.shanten_calc = ShantenCalculator()
        self.scorer = Scorer() 
        
        self.turn_count = 0
        self.active_player_index = 0 # 0=You (East), 1=South, etc.
        self.skip_draw = False # State flag for Pon/Chi/Kan behaviour

    def setup(self):
        ui.console.print("\n[bold green]=== MAHJONG ENGINE SETUP ===[/]")
        # 1. Deal 13 tiles to everyone
        for _ in range(13):
            for p in self.players:
                p.draw_tile(self.wall.draw())
        
        # 2. Sort hands for sanity
        for p in self.players:
            p.sort_hand()
        
        ui.console.print("Deal complete. Game Start!\n")
        time.sleep(1)

    def run_turn(self):
        """
        Executes a single turn. 
        Returns True to continue game, False if Game Over (Win).
        """
        active_player = self.players[self.active_player_index]
        self.turn_count += 1
        
        # --- VISUALS ---
        # Update the full dashboard for the human player
        ui.print_dashboard(self, self.active_player_index)
        
        # If it's a bot, pause briefly so the human can see what's happening
        if self.active_player_index != 0:
            time.sleep(0.8)
            ui.console.print(f"[dim]{active_player.name} is thinking...[/]")

        # ==========================
        # 1. DRAW PHASE
        # ==========================
        if not self.skip_draw:
            drawn_tile = self.wall.draw()
            if not drawn_tile:
                ui.console.print("[bold red]--- Wall Empty! Ryuukyoku (Draw Game) ---[/]")
                return False
            
            # Show the draw event
            if self.active_player_index == 0:
                ui.console.print(f"Draws: ", ui.get_tile_style(drawn_tile))
            else:
                ui.console.print(f"[dim]{active_player.name} draws a tile.[/]")

            active_player.draw_tile(drawn_tile)

            # --- CHECK TSUMO (Win on Draw) ---
            if self.shanten_calc.calculate_shanten(active_player.hand) == -1:
                # Check Yaku
                yaku = self.scorer.check_yaku(active_player.hand, active_player.open_melds)
                
                # Auto-win if Yaku present
                if yaku:
                    ui.console.print(f"\n[bold yellow on red] TSUMO! {active_player.name} wins! [/]")
                    ui.console.print(f"Yaku: {', '.join(yaku)}")
                    ui.console.print(ui.render_hand(active_player))
                    return False # GAME OVER
        else:
            ui.console.print("[dim](Skipping draw due to called tile)[/]")
            self.skip_draw = False # Reset flag

        # ==========================
        # 2. DISCARD PHASE (Human + Riichi Logic)
        # ==========================
        discard = None
        
        # --- HUMAN INPUT (Player 0) ---
        if self.active_player_index == 0:
            # We refresh the board because we just drew a tile
            ui.print_dashboard(self, self.active_player_index)
            
            # A. IF ALREADY IN RIICHI: AUTO-DISCARD
            if active_player.is_riichi:
                time.sleep(1.0)
                ui.console.print("[bold red]IN RIICHI: Auto-discarding drawn tile...[/]")
                # In Riichi, you discard the tile you just drew (last index)
                discard = active_player.discard_tile(len(active_player.hand) - 1)
                ui.console.print(f"Auto-discard: ", ui.get_tile_style(discard))

            # B. NORMAL TURN
            else:
                # CHECK FOR RIICHI OPPORTUNITY
                # Conditions: Closed hand, Tenpai (shanten == 0), Enough points
                can_declare_riichi = (
                    active_player.is_menzen and 
                    active_player.score >= 1000 and 
                    self.shanten_calc.calculate_shanten(active_player.hand) == 0
                )

                if can_declare_riichi:
                    ui.console.print("\n[bold yellow blink] RIICHI OPPORTUNITY! [/]")
                    riichi_choice = ui.console.input("Declare Riichi? (bets 1000 pts) [y/N] > ").lower()
                    
                    if riichi_choice == 'y':
                        active_player.is_riichi = True
                        active_player.score -= 1000
                        ui.console.print("[bold yellow] YOU DECLARE RIICHI![/]")
                        # In a real game, you would rotate the tile here.
                        # For now, we proceed to standard discard input.

                # Input Loop
                while True:
                    try:
                        user_input = ui.console.input("[bold green]Discard index > [/]")
                        idx = int(user_input)
                        discard = active_player.discard_tile(idx)
                        if discard:
                            ui.console.print(f"You discarded: ", ui.get_tile_style(discard))
                            break
                        else:
                            ui.console.print("[red]Invalid index.[/]")
                    except ValueError:
                        ui.console.print("[red]Please enter a number.[/]")

        # --- BOT INPUT (Players 1-3) ---
        else:
            # Simple Bot Riichi Logic
            # If bot is tenpai, closed hand, and not in riichi -> 50% chance to declare
            if (not active_player.is_riichi and 
                active_player.is_menzen and 
                self.shanten_calc.calculate_shanten(active_player.hand) == 0):
                
                # Simple logic: Just do it
                active_player.is_riichi = True
                active_player.score -= 1000
                ui.console.print(f"[bold yellow] {active_player.name} DECLARES RIICHI! [/]")

            # Bot Discard
            if active_player.is_riichi:
                # Must discard drawn tile
                discard = active_player.discard_tile(len(active_player.hand) - 1)
                ui.console.print(f"{active_player.name} (Riichi) discards: ", ui.get_tile_style(discard))
            else:
                discard = active_player.discard_tile(len(active_player.hand) - 1)
                ui.console.print(f"{active_player.name} discards: ", ui.get_tile_style(discard))

        # ==========================
        # 3. INTERRUPTION PHASE (Ron / Pon)
        # ==========================
        
        # A. CHECK RON
        for p in self.players:
            if p == active_player: continue
            
            test_hand = p.hand + [discard]
            if self.shanten_calc.calculate_shanten(test_hand) == -1:
                yaku = self.scorer.check_yaku(test_hand, p.open_melds)
                if yaku:
                    ui.console.print(f"\n[bold white on red] RON! {p.name} wins on {active_player.name}'s {discard}! [/]")
                    ui.console.print(f"Yaku: {', '.join(yaku)}")
                    ui.console.print(ui.render_hand(p))
                    return False 

        # B. CHECK PON / KAN
        for i, p in enumerate(self.players):
            if p == active_player: continue
            
            # 1. CHECK KAN (Daiminkan)
            if p.can_kan(discard):
                if i == 0: # Human
                    ui.console.print(f"\n[bold cyan]👀 CHECK: You can KAN[/] ", ui.get_tile_style(discard))
                    choice = ui.console.input("Call Kan? (y/n): ").lower()
                    if choice == 'y':
                        ui.console.print(f"[bold cyan]📢 YOU called KAN![/]")
                        p.execute_kan(discard)
                        
                        # --- KAN SPECIFIC MECHANICS ---
                        # 1. Draw Replacement
                        replacement = self.wall.draw_replacement()
                        ui.console.print(f"Replacement Tile: ", ui.get_tile_style(replacement))
                        p.draw_tile(replacement)
                        
                        # 2. Reveal New Dora (Standard for Daiminkan is immediate reveal)
                        self.wall.reveal_kan_dora()
                        ui.console.print(f"New Dora Indicator: ", ui.get_tile_style(self.wall.dora_indicators[-1]))
                        
                        # 3. Update State
                        self.active_player_index = i
                        self.skip_draw = True # We already drew the replacement
                        return True
                
                # (Add Bot Kan logic here if desired)

            # 2. CHECK PON (If they didn't Kan)
            # Only check Pon if they aren't in Riichi (already handled) 
            # and didn't just Kan.
            if p.can_pon(discard) and not p.is_riichi:
                if i == 0: 
                    ui.console.print(f"\n[bold cyan]👀 CHECK: You can PON[/] ", ui.get_tile_style(discard))
                    choice = ui.console.input("Call Pon? (y/n): ").lower()
                    if choice == 'y':
                        ui.console.print(f"[bold cyan]📢 YOU called PON![/]")
                        p.execute_pon(discard)
                        self.active_player_index = i
                        self.skip_draw = True
                        return True
                    
                    
        # C. CHECK CHI (Only for the NEXT player)
        # We only check this if no one declared Pon/Ron (we returned True/False earlier if they did)
        next_p_index = (self.active_player_index + 1) % 4
        next_player = self.players[next_p_index]
        
        # You cannot Chi if you are in Riichi
        if not next_player.is_riichi:
            chi_options = next_player.can_chi(discard)
            
            if chi_options:
                # -- HUMAN INTERACTION (If next player is YOU) --
                if next_p_index == 0:
                    ui.console.print(f"\n[bold green]CHECK: You can CHI[/] ", ui.get_tile_style(discard))
                    
                    # Display options nicely
                    for idx, opt in enumerate(chi_options):
                        t1 = next_player.hand[opt[0]]
                        t2 = next_player.hand[opt[1]]
                        ui.console.print(f"   {idx}: Use {ui.get_tile_style(t1)} and {ui.get_tile_style(t2)}")
                    
                    choice = ui.console.input("Call Chi? (Enter option number or 'n'): ").lower()
                    if choice.isdigit() and int(choice) < len(chi_options):
                        opt_idx = int(choice)
                        chosen_indices = chi_options[opt_idx]
                        
                        ui.console.print(f"[bold green]YOU called CHI![/]")
                        next_player.execute_chi(discard, chosen_indices)
                        
                        # Turn moves to you (which it was going to anyway, but now we skip draw)
                        self.active_player_index = next_p_index
                        self.skip_draw = True
                        return True


        # ==========================
        # 4. ROTATE TURN
        # ==========================
        self.active_player_index = (self.active_player_index + 1) % 4
        return True

    def start(self):
        self.setup()
        running = True
        while running:
            running = self.run_turn()
        ui.console.print("\n[bold]=== GAME END ===[/]")

if __name__ == "__main__":
    game = Game()
    game.start()