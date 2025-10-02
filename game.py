from dataclasses import dataclass, field
from typing import Any, Dict, List

from deck import Card, Deck
from players import Action, Dealer, Player, Street
from rules import (
    HandCategory,
    compare_hands,
    evaluate_best_hand,
    hand_category_to_string,
)


@dataclass
class GameState:
    """Represents the current state of the game visible to players."""

    # Public information
    community_cards: List[Card] = field(default_factory=list)
    current_street: Street = Street.PRE_FLOP
    pot_size: int = 0
    players_info: List[Dict[str, Any]] = field(default_factory=list)
    game_phase: str = "betting"  # "betting", "showdown", "finished"

    def add_player_info(self, player: Player, show_hand: bool = False) -> None:
        """
        Add player information to the game state.

        Args:
            player: Player to add info for
            show_hand: Whether to show the player's hand (for their own view)
        """
        player_info: Dict[str, Any] = {
            "position": player.position,
            "money": player.money,
            "ante": player.ante,
            "blind": player.blind,
            "bet": player.bet,
            "total_investment": player.get_total_investment(),
            "is_active": player.is_active,
            "has_bet_this_hand": player.has_bet_this_hand,
            "bet_street": player.bet_street.value if player.bet_street else None,
            "hand": [],
        }

        if show_hand:
            player_info["hand"] = [str(card) for card in player.hand]
        else:
            player_info["hand"] = ["??", "??"]  # Hidden cards

        self.players_info.append(player_info)

    def get_player_view(self, player_position: int) -> Dict[str, Any]:
        """
        Get the game state from a specific player's perspective.

        Args:
            player_position: Position of the player requesting the view

        Returns:
            Game state with player's hand revealed
        """
        view: Dict[str, Any] = {
            "community_cards": [str(card) for card in self.community_cards],
            "current_street": self.current_street.value,
            "pot_size": self.pot_size,
            "game_phase": self.game_phase,
        }
        players_list: List[Dict[str, Any]] = []

        for player_info in self.players_info:
            if player_info["position"] == player_position:
                # Show this player's hand
                player_info_copy = player_info.copy()
                player_info_copy["hand"] = [str(card) for card in player_info["hand"]]
                players_list.append(player_info_copy)
            else:
                # Hide other players' hands
                player_info_copy = player_info.copy()
                player_info_copy["hand"] = ["??", "??"]
                players_list.append(player_info_copy)

        view["players"] = players_list

        return view


class Game:
    """Main game engine for Ultimate Texas Hold'em."""

    def __init__(self, num_players: int = 6, iterations: int = 1):
        """
        Initialize a new game.

        Args:
            num_players: Number of players (1-6)
            iterations: Number of hands to play
        """
        if not 1 <= num_players <= 6:
            raise ValueError("Number of players must be between 1 and 6")

        self.num_players = num_players
        self.iterations = iterations
        self.deck = Deck()
        self.dealer = Dealer()
        self.players: List[Player] = []
        self.current_iteration = 0
        self.game_state = GameState()

        # Initialize players
        for i in range(1, num_players + 1):
            self.players.append(Player(position=i))

    def start_game(self) -> None:
        """Start the game and play all iterations."""
        print(f"=== Starting Ultimate Texas Hold'em ===")
        print(f"Players: {self.num_players}, Iterations: {self.iterations}")

        for iteration in range(1, self.iterations + 1):
            self.current_iteration = iteration
            print(f"\n{'='*50}")
            print(f"ITERATION {iteration}/{self.iterations}")
            print(f"{'='*50}")

            self.play_hand()

            if iteration < self.iterations:
                self.reset_for_new_hand()

        self.show_final_results()

    def play_hand(self) -> None:
        """Play a single hand of Ultimate Texas Hold'em."""
        print(f"\n--- Starting New Hand ---")

        # Reset for new hand
        self.deck.reset()
        self.deck.shuffle()
        self.dealer.reset()
        self.game_state = GameState()

        # Reset all players
        for player in self.players:
            player.clear_hand()
            player.reset_bets()

        # Place ante and blind bets
        self.place_initial_bets()

        # Deal initial cards
        self.deal_initial_cards()

        # Play betting rounds
        self.play_betting_rounds()

        # Deal community cards
        self.deal_community_cards()

        # Showdown (simplified for now)
        self.showdown()

    def place_initial_bets(self) -> None:
        """Place ante and blind bets for all players."""
        print(f"\n--- Placing Initial Bets ---")

        ante_amount = 1
        blind_amount = 1

        for player in self.players:
            if player.place_ante(ante_amount):
                print(f"{player} placed ${ante_amount} ante")
            else:
                print(f"{player} cannot afford ante, folding")
                player.fold()

            if player.is_active and player.place_blind(blind_amount):
                print(f"{player} placed ${blind_amount} blind")
            elif player.is_active:
                print(f"{player} cannot afford blind, folding")
                player.fold()

        # Update pot
        self.update_pot()

    def deal_initial_cards(self) -> None:
        """Deal initial hole cards to players and dealer."""
        print(f"\n--- Dealing Initial Cards ---")

        # Deal to players
        for player in self.players:
            if player.is_active:
                card1 = self.deck.deal_card()
                card2 = self.deck.deal_card()
                if card1 and card2:
                    player.receive_card(card1)
                    player.receive_card(card2)
                    print(f"{player} received: {card1}, {card2}")

        # Deal to dealer
        dealer_card1 = self.deck.deal_card()
        dealer_card2 = self.deck.deal_card()
        if dealer_card1 and dealer_card2:
            self.dealer.receive_card(dealer_card1)
            self.dealer.receive_card(dealer_card2)
            print(f"Dealer received: {dealer_card1}, {dealer_card2}")

    def play_betting_rounds(self) -> None:
        """Play all betting rounds (pre-flop, flop, river)."""
        streets = [Street.PRE_FLOP, Street.FLOP, Street.RIVER]

        for street in streets:
            self.game_state.current_street = street
            print(f"\n--- {street.value.upper()} Betting Round ---")

            # Get decisions from all active players
            for player in self.players:
                if player.is_active:
                    self.get_player_decision(player, street)

            # Update pot
            self.update_pot()

            # Show current state
            self.show_current_state()

    def get_player_decision(self, player: Player, street: Street) -> None:
        """
        Get a decision from a player.

        Args:
            player: Player making the decision
            street: Current betting street
        """
        # Create game state for this player
        self.game_state.players_info.clear()
        for p in self.players:
            self.game_state.add_player_info(p, show_hand=(p == player))

        # Get player's view of the game state
        player_view = self.game_state.get_player_view(player.position)

        # Get decision from player
        decision = self.ask_player_decision(player, player_view, street)

        # Execute decision
        if decision == Action.BET:
            if player.can_bet():
                base_bet = 1  # Default base bet amount
                if player.place_bet(base_bet, street):
                    actual_bet = player.get_bet_amount_for_street(base_bet, street)
                    print(f"{player} BET ${actual_bet} on {street.value}")
                else:
                    print(f"{player} cannot afford to bet, checking instead")
                    player.check(street)
            else:
                print(f"{player} already bet this hand, checking")
                player.check(street)
        else:  # CHECK
            if player.check(street):
                print(f"{player} CHECKED on {street.value}")
            else:
                print(f"{player} CHECKED on {street.value} (lost blind and ante)")

    def ask_player_decision(
        self, player: Player, game_state: Dict[str, Any], street: Street
    ) -> Action:
        """
        Ask a player to make a decision. This is where AI or human input would go.

        Args:
            player: Player making the decision
            game_state: Player's view of the game state
            street: Current betting street

        Returns:
            Player's decision
        """
        # For now, implement a simple AI strategy
        return self.simple_ai_decision(player, game_state, street)

    def simple_ai_decision(
        self, player: Player, game_state: Dict[str, Any], street: Street
    ) -> Action:
        """
        Simple AI decision making.

        Args:
            player: Player making the decision
            game_state: Player's view of the game state
            street: Current betting street

        Returns:
            AI's decision
        """
        # Simple strategy: bet on pre-flop with good cards, check otherwise
        if street == Street.PRE_FLOP and player.can_bet():
            # Bet if we have a pair or high cards
            hand_value = player.get_hand_value()
            if hand_value >= 20 or (player.hand[0].rank == player.hand[1].rank):
                return Action.BET

        return Action.CHECK

    def deal_community_cards(self) -> None:
        """Deal all community cards (flop, turn, river)."""
        print(f"\n--- Dealing Community Cards ---")

        # Deal flop (3 cards)
        flop_cards = self.deck.deal_cards(3)
        for card in flop_cards:
            self.dealer.add_community_card(card)
            self.game_state.community_cards.append(card)
        print(f"Flop: {', '.join(str(card) for card in flop_cards)}")

        # Deal turn (1 card)
        turn_card = self.deck.deal_card()
        if turn_card:
            self.dealer.add_community_card(turn_card)
            self.game_state.community_cards.append(turn_card)
            print(f"Turn: {turn_card}")

        # Deal river (1 card)
        river_card = self.deck.deal_card()
        if river_card:
            self.dealer.add_community_card(river_card)
            self.game_state.community_cards.append(river_card)
            print(f"River: {river_card}")

        print(
            f"All community cards: {', '.join(str(card) for card in self.game_state.community_cards)}"
        )

    def showdown(self) -> None:
        """Handle the showdown phase."""
        print(f"\n--- Showdown ---")
        print(
            f"Dealer's hole cards: {', '.join(str(card) for card in self.dealer.hand)}"
        )
        print(
            f"Community cards: {', '.join(str(card) for card in self.game_state.community_cards)}"
        )

        # Evaluate dealer best hand
        dealer_best = evaluate_best_hand(
            self.dealer.hand + self.game_state.community_cards
        )
        print(
            f"Dealer best: {hand_category_to_string(dealer_best.category)} "
            f"(tiebreakers: {dealer_best.tiebreakers})"
        )

        # Evaluate each active player and compare vs dealer
        for player in self.players:
            if not player.is_active:
                continue

            player_best = evaluate_best_hand(
                player.hand + self.game_state.community_cards
            )
            result = compare_hands(player_best, dealer_best)
            outcome = "TIES"
            if result > 0:
                outcome = "BEATS"
            elif result < 0:
                outcome = "LOSES TO"

            print(
                f"{player} - Best: {hand_category_to_string(player_best.category)} "
                f"(tiebreakers: {player_best.tiebreakers}) {outcome} Dealer"
            )

        # Resolve payouts
        print("\n--- Payouts ---")
        dealer_qualifies = dealer_best.category >= HandCategory.PAIR
        for player in self.players:
            if not player.is_active:
                continue

            player_best = evaluate_best_hand(
                player.hand + self.game_state.community_cards
            )
            result = compare_hands(player_best, dealer_best)

            ante_stake = player.ante
            blind_stake = player.blind
            play_stake = player.bet

            ante_return = 0
            blind_return = 0
            play_return = 0

            # Play (bet) pays even money; push on tie
            if play_stake > 0:
                if result > 0:
                    play_return = play_stake * 2
                elif result == 0:
                    play_return = play_stake

            # Ante pays 1:1 only if dealer qualifies; otherwise push regardless
            if ante_stake > 0:
                if dealer_qualifies:
                    if result > 0:
                        ante_return = ante_stake * 2
                    elif result == 0:
                        ante_return = ante_stake
                else:
                    ante_return = ante_stake

            # Blind payout table; push if win with less than a Straight; push on tie; lose on dealer win
            if blind_stake > 0:
                if result > 0:
                    category = player_best.category
                    if category >= HandCategory.STRAIGHT:
                        # Determine payout and return stake + winnings
                        if category == HandCategory.STRAIGHT:
                            blind_return = blind_stake * 2  # 1:1
                        elif category == HandCategory.FLUSH:
                            # 3:2 payout → stake + 1.5x
                            blind_return = blind_stake + (blind_stake * 3) // 2
                        elif category == HandCategory.FULL_HOUSE:
                            blind_return = blind_stake * 4  # 3:1
                        elif category == HandCategory.FOUR_OF_A_KIND:
                            blind_return = blind_stake * 11  # 10:1
                        elif category == HandCategory.STRAIGHT_FLUSH:
                            # Royal Flush check (Ace-high straight flush)
                            high_card = (
                                player_best.tiebreakers[0]
                                if player_best.tiebreakers
                                else 0
                            )
                            if high_card == 14:
                                blind_return = blind_stake * 501  # 500:1
                            else:
                                blind_return = blind_stake * 51  # 50:1
                    else:
                        # Win with less than a straight → push
                        blind_return = blind_stake
                elif result == 0:
                    blind_return = blind_stake

            total_return = ante_return + blind_return + play_return
            player.money += total_return

            print(
                f"{player} returns - Ante: ${ante_return}, Blind: ${blind_return}, "
                f"Play: ${play_return} (Dealer qualifies: {dealer_qualifies})"
            )

    def update_pot(self) -> None:
        """Update the pot size based on all player bets."""
        self.game_state.pot_size = sum(
            player.get_total_investment() for player in self.players
        )

    def show_current_state(self) -> None:
        """Show the current game state."""
        print(f"\nCurrent pot: ${self.game_state.pot_size}")
        for player in self.players:
            if player.is_active:
                print(
                    f"{player} - Investment: ${player.get_total_investment()}, "
                    f"Can bet: {player.can_bet()}"
                )

    def reset_for_new_hand(self) -> None:
        """Reset everything for a new hand."""
        print(f"\n--- Resetting for New Hand ---")
        # Players and dealer are already reset in play_hand()
        pass

    def show_final_results(self) -> None:
        """Show final results after all iterations."""
        print(f"\n{'='*50}")
        print(f"FINAL RESULTS")
        print(f"{'='*50}")

        for player in self.players:
            print(f"{player} - Final money: ${player.money:,}")

        total_money = sum(player.money for player in self.players)
        print(f"Total money in game: ${total_money:,}")


# Example usage
if __name__ == "__main__":
    # Create and start a game
    game = Game(num_players=6, iterations=2)
    game.start_game()
