"""
Human CLI Agent - Human player input via command-line interface.

This agent prompts the human player for input via the terminal.
It displays the available options and waits for valid input.
"""

from .agent import Agent
from ..core.game_state import GameState, Action, ActionType, AvailableActions


class HumanCLIAgent(Agent):
    """
    An agent that prompts a human player for input via CLI.
    
    This agent:
    - Displays available actions clearly
    - Validates input before returning
    - Handles errors gracefully
    """
    
    def __init__(self, name: str = "Human"):
        super().__init__(name)
        self._console = None  # Lazy import to avoid dependency
    
    @property
    def console(self):
        """Lazy-load Rich console."""
        if self._console is None:
            try:
                from rich.console import Console
                self._console = Console()
            except ImportError:
                # Fallback to basic print if Rich not available
                class BasicConsole:
                    def print(self, *args, **kwargs):
                        # Strip Rich formatting
                        text = ' '.join(str(a) for a in args)
                        print(text)
                    def input(self, prompt=""):
                        return input(prompt)
                self._console = BasicConsole()
        return self._console
    
    def choose_action(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """Prompt human for action choice."""
        
        # Auto-take wins
        if available_actions.can_tsumo:
            self.console.print("[bold yellow]TSUMO! You win![/]")
            return Action(ActionType.TSUMO, available_actions.player_index)
        
        if available_actions.can_ron:
            self.console.print(f"[bold yellow]RON opportunity! Yaku: {', '.join(available_actions.ron_yaku)}[/]")
            choice = self._get_yes_no("Declare Ron?", default_yes=True)
            if choice:
                return Action(ActionType.RON, available_actions.player_index)
            else:
                return Action(ActionType.PASS, available_actions.player_index)
        
        # Handle call opportunities
        if available_actions.can_pon or available_actions.can_kan or available_actions.can_chi:
            return self._handle_call_decision(state, available_actions)
        
        # Handle discard phase
        if available_actions.can_discard:
            return self._handle_discard_decision(state, available_actions)
        
        # Pass if nothing else
        if available_actions.can_pass:
            return Action(ActionType.PASS, available_actions.player_index)
        
        raise ValueError("No actions available!")
    
    def _handle_call_decision(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """Handle Pon/Kan/Chi call decisions."""
        
        player_idx = available_actions.player_index
        
        # Show KAN option
        if available_actions.can_kan:
            self.console.print("[bold cyan]You can call KAN (enter 'k')[/]")
        
        # Show PON option
        if available_actions.can_pon:
            self.console.print("[bold cyan]You can call PON (enter 'p')[/]")
        
        # Show CHI options with numbers
        if available_actions.can_chi:
            self.console.print("[bold green]You can call CHI[/]")
            for opt in available_actions.chi_options:
                tiles_str = ', '.join(str(t) for t in opt.resulting_tiles)
                self.console.print(f"   {opt.option_index}: {tiles_str}")
        
        self.console.print("   n: Pass (don't call)")
        
        while True:
            choice = self.console.input("Call? > ").lower().strip()
            
            # Pass
            if choice == 'n' or choice == 'pass' or choice == '':
                return Action(ActionType.PASS, player_idx)
            
            # KAN
            if choice == 'k' and available_actions.can_kan:
                return Action(ActionType.KAN, player_idx)
            
            # PON
            if choice == 'p' and available_actions.can_pon:
                return Action(ActionType.PON, player_idx)
            
            # CHI - check if user entered a number directly
            if available_actions.can_chi:
                try:
                    opt_idx = int(choice)
                    if 0 <= opt_idx < len(available_actions.chi_options):
                        return Action(ActionType.CHI, player_idx, chi_option=opt_idx)
                    else:
                        self.console.print(f"[red]Chi option must be 0-{len(available_actions.chi_options)-1}[/]")
                        continue
                except ValueError:
                    pass  # Not a number, check other options
            
            # Show help for invalid input
            valid_choices = []
            if available_actions.can_kan:
                valid_choices.append("'k' for KAN")
            if available_actions.can_pon:
                valid_choices.append("'p' for PON")
            if available_actions.can_chi:
                valid_choices.append(f"0-{len(available_actions.chi_options)-1} for CHI")
            valid_choices.append("'n' to pass")
            
            self.console.print(f"[red]Invalid. Enter: {', '.join(valid_choices)}[/]")
    
    def _handle_discard_decision(
        self, 
        state: GameState, 
        available_actions: AvailableActions
    ) -> Action:
        """Handle discard decisions (including Riichi)."""
        
        player_state = state.get_player(available_actions.player_index)
        
        # Check for Riichi opportunity
        if available_actions.can_riichi:
            self.console.print("\n[bold yellow blink]RIICHI OPPORTUNITY![/]")
            self.console.print(f"[dim]Valid discards for Riichi: {available_actions.riichi_discard_indices}[/]")
            
            if self._get_yes_no("Declare Riichi? (bets 1000 pts)"):
                # Must choose a valid riichi discard
                while True:
                    try:
                        idx_str = self.console.input("[bold yellow]Riichi discard index > [/]")
                        idx = int(idx_str)
                        if idx in available_actions.riichi_discard_indices:
                            return Action(ActionType.DECLARE_RIICHI, available_actions.player_index, tile_index=idx)
                        else:
                            self.console.print(f"[red]Must discard one of: {available_actions.riichi_discard_indices}[/]")
                    except ValueError:
                        self.console.print("[red]Please enter a number.[/]")
        
        # Normal discard
        while True:
            try:
                idx_str = self.console.input("[bold green]Discard index > [/]")
                idx = int(idx_str)
                if idx in available_actions.discard_indices:
                    return Action(ActionType.DISCARD, available_actions.player_index, tile_index=idx)
                else:
                    self.console.print(f"[red]Invalid index. Valid: 0-{len(player_state.hand)-1}[/]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/]")
    
    def _get_yes_no(self, prompt: str, default_yes: bool = False) -> bool:
        """Get a yes/no answer from the user."""
        default_hint = "[Y/n]" if default_yes else "[y/N]"
        while True:
            choice = self.console.input(f"{prompt} {default_hint} > ").lower().strip()
            if choice == '':
                return default_yes
            if choice in ('y', 'yes'):
                return True
            if choice in ('n', 'no'):
                return False
            self.console.print("[red]Please enter y or n.[/]")
