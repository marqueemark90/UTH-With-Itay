import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class Suit(Enum):
    """Enumeration of card suits."""

    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Card:
    """Represents a playing card with rank and suit."""

    def __init__(self, rank: int, suit: Suit):
        """
        Initialize a card.

        Args:
            rank: Card rank (1=Ace, 2-10, 11=Jack, 12=Queen, 13=King)
            suit: Card suit
        """
        if not 1 <= rank <= 13:
            raise ValueError("Rank must be between 1 and 13")
        self.rank = rank
        self.suit = suit

    @property
    def value(self) -> int:
        """Get the numeric value of the card for comparison."""
        return self.rank

    @property
    def display_rank(self) -> str:
        """Get the display string for the card rank."""
        if self.rank == 1:
            return "A"
        elif self.rank == 11:
            return "J"
        elif self.rank == 12:
            return "Q"
        elif self.rank == 13:
            return "K"
        else:
            return str(self.rank)

    def __str__(self) -> str:
        """String representation of the card."""
        return f"{self.display_rank}{self.suit.value}"

    def __repr__(self) -> str:
        """Detailed string representation of the card."""
        return f"Card(rank={self.rank}, suit={self.suit})"

    def __eq__(self, other: Any) -> bool:
        """Check if two cards are equal."""
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        """Hash function for the card."""
        return hash((self.rank, self.suit))


@dataclass
class Deck:
    """A deck of 52 playing cards for Ultimate Texas Hold'em."""

    cards: List[Card] = field(default_factory=list)

    def __post_init__(self):
        """Initialize the deck with 52 cards if not provided."""
        if not self.cards:
            self.reset()

    def reset(self) -> None:
        """Reset the deck to contain all 52 standard playing cards."""
        self.cards = []
        for suit in Suit:
            for rank in range(1, 14):  # 1 (Ace) through 13 (King)
                self.cards.append(Card(rank, suit))

    def shuffle(self) -> None:
        """Shuffle the deck using Fisher-Yates algorithm."""
        random.shuffle(self.cards)

    def deal_card(self) -> Optional[Card]:
        """
        Deal one card from the top of the deck.

        Returns:
            The top card, or None if deck is empty
        """
        if not self.cards:
            return None
        return self.cards.pop()

    def deal_cards(self, count: int) -> List[Card]:
        """
        Deal multiple cards from the deck.

        Args:
            count: Number of cards to deal

        Returns:
            List of cards dealt

        Raises:
            ValueError: If trying to deal more cards than available
        """
        if count > len(self.cards):
            raise ValueError(
                f"Cannot deal {count} cards, only {len(self.cards)} available"
            )

        dealt_cards: List[Card] = []
        for _ in range(count):
            card = self.deal_card()
            if card is not None:
                dealt_cards.append(card)

        return dealt_cards

    def cards_remaining(self) -> int:
        """Get the number of cards remaining in the deck."""
        return len(self.cards)

    def is_empty(self) -> bool:
        """Check if the deck is empty."""
        return len(self.cards) == 0

    def peek_top(self) -> Optional[Card]:
        """
        Look at the top card without removing it.

        Returns:
            The top card, or None if deck is empty
        """
        if not self.cards:
            return None
        return self.cards[-1]

    def __str__(self) -> str:
        """String representation of the deck."""
        return f"Deck({self.cards_remaining()} cards remaining)"

    def __repr__(self) -> str:
        """Detailed string representation of the deck."""
        return f"Deck(cards={self.cards})"


# Example usage and testing
if __name__ == "__main__":
    # Create a new deck
    deck = Deck()
    print(f"New deck: {deck}")
    print(f"Cards remaining: {deck.cards_remaining()}")

    # Shuffle the deck
    deck.shuffle()
    print(f"After shuffle: {deck}")

    # Deal some cards
    print("\nDealing 5 cards:")
    dealt = deck.deal_cards(5)
    for i, card in enumerate(dealt, 1):
        print(f"Card {i}: {card}")

    print(f"\nAfter dealing: {deck}")
    print(f"Cards remaining: {deck.cards_remaining()}")

    # Peek at the top card
    top_card = deck.peek_top()
    print(f"Top card (without dealing): {top_card}")

    # Reset the deck
    deck.reset()
    print(f"\nAfter reset: {deck}")
    print(f"Cards remaining: {deck.cards_remaining()}")
