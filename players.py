from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from deck import Card


class Action(Enum):
    """Enumeration of player actions in Ultimate Texas Hold'em."""

    CHECK = "check"
    BET = "bet"


class Street(Enum):
    """Enumeration of betting streets in Ultimate Texas Hold'em."""

    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    RIVER = "river"


@dataclass
class Player:
    """Represents a player in Ultimate Texas Hold'em."""

    position: int
    money: int = 1_000_000
    hand: List[Card] = field(default_factory=list)
    ante: int = 0
    blind: int = 0
    bet: int = 0
    total_bet: int = 0
    is_active: bool = True
    has_folded: bool = False
    has_bet_this_hand: bool = False
    bet_street: Optional[Street] = None

    def __post_init__(self):
        """Validate player position."""
        if not 1 <= self.position <= 6:
            raise ValueError("Player position must be between 1 and 6")

    def place_ante(self, amount: int) -> bool:
        """
        Place an ante bet.

        Args:
            amount: Amount to bet as ante

        Returns:
            True if successful, False if insufficient funds
        """
        if amount > self.money:
            return False

        self.money -= amount
        self.ante = amount
        self.total_bet += amount
        return True

    def place_blind(self, amount: int) -> bool:
        """
        Place a blind bet.

        Args:
            amount: Amount to bet as blind

        Returns:
            True if successful, False if insufficient funds
        """
        if amount > self.money:
            return False

        self.money -= amount
        self.blind = amount
        self.total_bet += amount
        return True

    def place_bet(self, amount: int, street: Street) -> bool:
        """
        Place a bet based on the current street.

        Args:
            amount: Base amount to bet (will be multiplied by street multiplier)
            street: Current betting street

        Returns:
            True if successful, False if insufficient funds or already bet
        """
        if self.has_bet_this_hand:
            return False  # Can only bet once per hand

        # Get street multiplier
        multiplier = self._get_street_multiplier(street)
        bet_amount = amount * multiplier

        if bet_amount > self.money:
            return False

        self.money -= bet_amount
        self.bet = bet_amount
        self.total_bet += bet_amount
        self.has_bet_this_hand = True
        self.bet_street = street
        return True

    def _get_street_multiplier(self, street: Street) -> int:
        """
        Get the betting multiplier for a given street.

        Args:
            street: The betting street

        Returns:
            Multiplier for the street (4x pre-flop, 2x flop, 1x river)
        """
        if street == Street.PRE_FLOP:
            return 4
        elif street == Street.FLOP:
            return 2
        else:  # RIVER
            return 1

    def check(self, street: Street) -> bool:
        """
        Check (no additional bet).

        Args:
            street: Current betting street

        Returns:
            True if successful, False if checking on river (loses blind and ante)
        """
        if street == Street.RIVER and not self.has_bet_this_hand:
            # Lose blind and ante if checking on river without betting
            self.money -= self.blind + self.ante
            return False
        return True

    def fold(self) -> None:
        """Fold the hand."""
        self.has_folded = True
        self.is_active = False

    def receive_card(self, card: Card) -> None:
        """
        Receive a card in the hand.

        Args:
            card: Card to add to hand
        """
        self.hand.append(card)

    def clear_hand(self) -> None:
        """Clear the player's hand."""
        self.hand.clear()

    def reset_bets(self) -> None:
        """Reset all bets for a new hand."""
        self.ante = 1
        self.blind = 1
        self.bet = 1
        self.total_bet = 0
        self.is_active = True
        self.has_folded = False
        self.has_bet_this_hand = False
        self.bet_street = None

    def get_hand_value(self) -> int:
        """
        Get the total value of cards in hand.
        This is a simple sum for now - poker hand evaluation will be added later.

        Returns:
            Sum of card values in hand
        """
        return sum(card.value for card in self.hand)

    def can_afford(self, amount: int) -> bool:
        """
        Check if player can afford a bet.

        Args:
            amount: Amount to check

        Returns:
            True if player has enough money
        """
        return self.money >= amount

    def get_total_investment(self) -> int:
        """
        Get total amount invested in current hand.

        Returns:
            Total of ante, blind, and bet
        """
        return self.ante + self.blind + self.bet

    def can_bet(self) -> bool:
        """
        Check if player can still bet this hand.

        Returns:
            True if player hasn't bet yet this hand
        """
        return not self.has_bet_this_hand

    def get_bet_amount_for_street(self, base_amount: int, street: Street) -> int:
        """
        Calculate the actual bet amount for a given street.

        Args:
            base_amount: Base bet amount
            street: Current street

        Returns:
            Actual bet amount (base * street multiplier)
        """
        return base_amount * self._get_street_multiplier(street)

    def __str__(self) -> str:
        """String representation of the player."""
        return f"Player {self.position} (${self.money:,})"

    def __repr__(self) -> str:
        """Detailed string representation of the player."""
        return (
            f"Player(position={self.position}, money={self.money}, "
            f"hand={self.hand}, ante={self.ante}, blind={self.blind}, "
            f"bet={self.bet}, is_active={self.is_active})"
        )


@dataclass
class Dealer:
    """Represents the dealer in Ultimate Texas Hold'em."""

    hand: List[Card] = field(default_factory=list)
    community_cards: List[Card] = field(default_factory=list)

    def receive_card(self, card: Card) -> None:
        """
        Receive a card in the dealer's hand.

        Args:
            card: Card to add to dealer's hand
        """
        self.hand.append(card)

    def add_community_card(self, card: Card) -> None:
        """
        Add a community card.

        Args:
            card: Community card to add
        """
        self.community_cards.append(card)

    def clear_hand(self) -> None:
        """Clear the dealer's hand."""
        self.hand.clear()

    def clear_community_cards(self) -> None:
        """Clear all community cards."""
        self.community_cards.clear()

    def reset(self) -> None:
        """Reset dealer for a new hand."""
        self.clear_hand()
        self.clear_community_cards()

    def get_hand_value(self) -> int:
        """
        Get the total value of cards in dealer's hand.
        This is a simple sum for now - poker hand evaluation will be added later.

        Returns:
            Sum of card values in dealer's hand
        """
        return sum(card.value for card in self.hand)

    def get_all_cards(self) -> List[Card]:
        """
        Get all cards available to the dealer (hand + community cards).

        Returns:
            Combined list of hand and community cards
        """
        return self.hand + self.community_cards

    def __str__(self) -> str:
        """String representation of the dealer."""
        return f"Dealer (hand: {len(self.hand)} cards, community: {len(self.community_cards)} cards)"

    def __repr__(self) -> str:
        """Detailed string representation of the dealer."""
        return f"Dealer(hand={self.hand}, community_cards={self.community_cards})"


# Example usage and testing
if __name__ == "__main__":
    from deck import Deck

    # Create a deck and dealer
    deck = Deck()
    deck.shuffle()
    dealer = Dealer()

    # Create some players
    players: List[Player] = []
    for i in range(1, 4):  # Create 3 players
        players.append(Player(position=i))

    print("=== Ultimate Texas Hold'em Player Test ===")
    print(f"Dealer: {dealer}")

    # Show initial player states
    for player in players:
        print(f"{player}")

    # Deal initial cards
    print("\n=== Dealing Cards ===")
    for player in players:
        card1 = deck.deal_card()
        card2 = deck.deal_card()
        if card1 and card2:
            player.receive_card(card1)
            player.receive_card(card2)
            print(f"{player} received: {card1}, {card2}")

    # Deal dealer cards
    dealer_card1 = deck.deal_card()
    dealer_card2 = deck.deal_card()
    if dealer_card1 and dealer_card2:
        dealer.receive_card(dealer_card1)
        dealer.receive_card(dealer_card2)
        print(f"Dealer received: {dealer_card1}, {dealer_card2}")

    # Deal flop (3 cards)
    print("\n=== Dealing Flop ===")
    flop_cards = deck.deal_cards(3)
    for card in flop_cards:
        dealer.add_community_card(card)
    print(f"Flop: {', '.join(str(card) for card in flop_cards)}")

    # Deal turn (1 card)
    print("\n=== Dealing Turn ===")
    turn_card = deck.deal_card()
    if turn_card:
        dealer.add_community_card(turn_card)
        print(f"Turn: {turn_card}")

    # Deal river (1 card)
    print("\n=== Dealing River ===")
    river_card = deck.deal_card()
    if river_card:
        dealer.add_community_card(river_card)
        print(f"River: {river_card}")

    print(
        f"\nAll community cards: {', '.join(str(card) for card in dealer.community_cards)}"
    )

    # Place initial bets
    print("\n=== Placing Bets ===")
    ante_amount = 1
    blind_amount = 1

    for player in players:
        if player.place_ante(ante_amount):
            print(f"{player} placed ${ante_amount} ante")
        else:
            print(f"{player} cannot afford ${ante_amount} ante")

        if player.place_blind(blind_amount):
            print(f"{player} placed ${blind_amount} blind")
        else:
            print(f"{player} cannot afford ${blind_amount} blind")

    # Show updated player states
    print("\n=== Updated Player States ===")
    for player in players:
        print(f"{player} - Total bet: ${player.get_total_investment()}")

    # Test Ultimate Texas Hold'em betting logic
    print("\n=== Ultimate Texas Hold'em Betting Logic ===")

    # Simulate different streets
    streets = [Street.PRE_FLOP, Street.FLOP, Street.RIVER]
    base_bet = 1

    for street in streets:
        print(f"\n--- {street.value.upper()} ---")
        multiplier = (
            players[0].get_bet_amount_for_street(1, street) // 1
        )  # Get multiplier by dividing by 1
        actual_bet = base_bet * multiplier
        print(
            f"Base bet: ${base_bet}, Multiplier: {multiplier}x, Actual bet: ${actual_bet}"
        )

        for i, player in enumerate(players):
            if player.is_active and player.can_bet():
                # Simulate betting decision
                if player.place_bet(base_bet, street):
                    print(f"{player} BET ${actual_bet} on {street.value}")
                else:
                    print(f"{player} cannot afford ${actual_bet} on {street.value}")
            elif player.is_active:
                # Player already bet, can only check
                if player.check(street):
                    print(f"{player} CHECKED on {street.value}")
                else:
                    print(f"{player} CHECKED on {street.value} (lost blind and ante)")

    # Test river check penalty
    print("\n--- RIVER CHECK PENALTY TEST ---")
    test_player = Player(position=6, money=1000)
    test_player.place_ante(50)
    test_player.place_blind(25)
    print(
        f"Before river check: {test_player} (ante: ${test_player.ante}, blind: ${test_player.blind})"
    )

    if not test_player.check(Street.RIVER):
        print(f"After river check: {test_player} (lost blind and ante)")
    else:
        print(f"After river check: {test_player} (no penalty)")

    # Show final states
    print("\n=== Final States ===")
    print(f"Dealer: {dealer}")
    print(f"Dealer's hole cards: {', '.join(str(card) for card in dealer.hand)}")
    print(f"Community cards: {', '.join(str(card) for card in dealer.community_cards)}")
    for player in players:
        print(
            f"{player} - Hand: {', '.join(str(card) for card in player.hand)} "
            f"(value: {player.get_hand_value()}), "
            f"Total investment: ${player.get_total_investment()}"
        )

    # Reset for new hand
    print("\n=== Resetting for New Hand ===")
    dealer.reset()
    for player in players:
        player.clear_hand()
        player.reset_bets()

    print(f"Dealer after reset: {dealer}")
    for player in players:
        print(
            f"{player} after reset - Hand: {len(player.hand)} cards, "
            f"Total bet: ${player.get_total_investment()}"
        )
