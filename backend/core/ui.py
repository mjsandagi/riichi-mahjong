from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from .tiles import Suit

console = Console()

def get_tile_style(tile):
    """Returns a Rich Text object with full names (e.g. '5 Sou')."""
    if not tile: return Text("??", style="dim")
    
    # 1. Define Colors
    color_map = {
        Suit.MAN: "red",       # Man -> Red
        Suit.PIN: "cyan",      # Pin -> Cyan/Blue
        Suit.SOU: "green",     # Sou -> Green
        Suit.HONOUR: "magenta" # Honours -> Magenta
    }
    
    color = color_map.get(tile.suit, "white")
    style = f"bold {color}"

    # 2. Determine Text (Full Name)
    text_content = ""

    if tile.suit == Suit.HONOUR:
        # Map values 1-7 to full English names
        honour_names = {
            1: "East", 
            2: "South", 
            3: "West", 
            4: "North",
            5: "White", # Haku
            6: "Green", # Hatsu
            7: "Red"    # Chun
        }
        text_content = honour_names.get(tile.value, "Unknown")
    else:
        # Numbered Suits: "1 Man", "5 Sou", etc.
        suit_names = {
            Suit.MAN: "Man", 
            Suit.PIN: "Pin", 
            Suit.SOU: "Sou"
        }
        s_name = suit_names.get(tile.suit, "?")
        text_content = f"{tile.value} {s_name}"

    # 3. Handle 'Red 5' (Akadora)
    if tile.is_red:
        style = "bold red underline"
    
    # Return formatted text in brackets e.g. [5 Sou]
    return Text(f"[{text_content}]", style=style)

def render_hand(player, show_indices=False):
    """Renders the player's hand as a nice row."""
    table = Table.grid(padding=(0, 1))
    
    # Row 1: The Tiles
    row_tiles = []
    for t in player.hand:
        row_tiles.append(get_tile_style(t))
    table.add_row(*row_tiles)
    
    # Row 2: The Indices (for selection)
    if show_indices:
        row_indices = []
        for i in range(len(player.hand)):
            # distinct styling for indices so they don't blend in
            row_indices.append(Text(f"   {i}   ", style="dim white"))
        table.add_row(*row_indices)
        
    return table

def render_river(player):
    """Renders the discards (River/Kawa) in a 6-per-row grid."""
    grid = Table.grid(padding=(0, 1))
    
    row = []
    for i, tile in enumerate(player.discards):
        row.append(get_tile_style(tile))
        # Wrap every 6 tiles
        if (i + 1) % 6 == 0:
            grid.add_row(*row)
            row = []
    if row:
        grid.add_row(*row)
        
    return Panel(grid, title=f"{player.name}'s River", border_style="dim")

def print_dashboard(game, active_player_index):
    """
    Clears screen and prints the full board state.
    """
    console.clear()
    
    # 1. HEADER
    dora_display = Text("Dora: ", style="bold gold1")
    for d in game.wall.dora_indicators:
        dora_display.append(get_tile_style(d))
        dora_display.append("  ")
        
    header = Table.grid(expand=True)
    header.add_row(
        f"Tiles Left: {game.wall.remaining}",
        dora_display,
        f"Turn: {game.turn_count}",
        style="bold white on blue"
    )
    console.print(header)
    console.print()

    # 2. OPPONENTS
    opponents_table = Table(box=box.SIMPLE)
    opponents_table.add_column("Player", style="bold")
    opponents_table.add_column("Score")
    opponents_table.add_column("State")
    opponents_table.add_column("Last Discards")
    
    for i, p in enumerate(game.players):
        if i == 0: continue # Skip Human
        
        # Check Riichi status for visual
        status_text = "Riichi!" if p.is_riichi else ("Thinking..." if i == active_player_index else "Waiting")
        style_state = "bold red blink" if p.is_riichi else "dim"

        # Show last 4 discards
        recent_river = Text("")
        for t in p.discards[-4:]:
            recent_river.append(get_tile_style(t))
            recent_river.append(" ")
        
        opponents_table.add_row(
            p.name, 
            str(p.score), 
            Text(status_text, style=style_state), 
            recent_river
        )
    
    console.print(Panel(opponents_table, title="Opponents"))

    # 3. PLAYER VIEW
    me = game.players[0]
    
    # --- Melds ---
    if me.open_melds:
        console.print(Text(f"Melds: {me.open_melds}", style="yellow"))

    # --- Status Calculation ---
    shanten = game.shanten_calc.calculate_shanten(me.hand)
    
    status_line = Text(f"Score: {me.score}   ", style="bold white")

    # Add Riichi Badge
    if me.is_riichi:
        status_line.append("[ RIICHI ] ", style="bold white on red")
    
    # Add Tenpai/Waits Badge
    if shanten == 0:
        # Calculate Waits
        waits = game.shanten_calc.get_waits(me.hand)
        
        # --- NEW: Check Furiten for UI ---
        wait_ids = set((w.suit, w.value) for w in waits)
        discard_ids = set((t.suit, t.value) for t in me.discards)
        
        is_furiten = not wait_ids.isdisjoint(discard_ids)
        
        if is_furiten:
            status_line.append("[ FURITEN ] ", style="bold white on red")
            status_line.append(" (Win by Tsumo only) ", style="dim red")
        else:
            status_line.append("[ TENPAI ] ", style="bold black on yellow")
            status_line.append(" Waiting for: ", style="dim")
        
        # Display the waits
        for w in waits:
            status_line.append(get_tile_style(w))
            status_line.append(" ")
            
    elif shanten == 1:
        status_line.append("1-shanten", style="dim italic")
    elif shanten == 2:
        status_line.append("2-shanten", style="dim italic")

    console.print(status_line)

    # The Hand
    console.print(Panel(
        render_hand(me, show_indices=True), 
        title=f"[bold green]YOUR HAND ({me.name})[/]",
        subtitle="Type the index number below the tile to discard",
        expand=False
    ))