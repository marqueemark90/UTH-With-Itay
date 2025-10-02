from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations
from typing import Dict, List, Optional, Tuple

from deck import Card


class HandCategory(IntEnum):
    """Poker hand strength categories in ascending order."""

    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


@dataclass(frozen=True)
class EvaluatedHand:
    """Represents an evaluated 5-card poker hand."""

    category: HandCategory
    tiebreakers: Tuple[int, ...]
    cards: Tuple[Card, ...]

    def as_tuple(self) -> Tuple[int, Tuple[int, ...]]:
        return int(self.category), self.tiebreakers


def _rank_value(rank: int) -> int:
    """Map card rank to comparable value. Ace (1) becomes 14 by default."""
    return 14 if rank == 1 else rank


def _sorted_rank_values_desc(cards: List[Card]) -> List[int]:
    return sorted([_rank_value(c.rank) for c in cards], reverse=True)


def _straight_high_card(ranks: List[int]) -> Optional[int]:
    """
    Given a list of 5 rank values (Ace mapped to 14), return the straight high card
    or None if not a straight. Handles wheel (A-2-3-4-5) returning 5.
    """
    unique = sorted(set(ranks), reverse=True)
    if len(unique) != 5:
        return None

    # Normal straight check (e.g., K-Q-J-10-9)
    if all(unique[i] - 1 == unique[i + 1] for i in range(4)):
        return unique[0]

    # Wheel: A-2-3-4-5 → treat Ace as 1 (represented as 14 here)
    if set(unique) == {14, 5, 4, 3, 2}:
        return 5

    return None


def _is_flush(cards: List[Card]) -> bool:
    return len({c.suit for c in cards}) == 1


def _rank_counts(cards: List[Card]) -> List[Tuple[int, int]]:
    """
    Return list of (rank_value, count) sorted by count desc, then rank desc.
    """
    counts: Dict[int, int] = {}
    for c in cards:
        rv = _rank_value(c.rank)
        counts[rv] = counts.get(rv, 0) + 1
    return sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)


def evaluate_five_card_hand(cards: List[Card]) -> EvaluatedHand:
    if len(cards) != 5:
        raise ValueError("evaluate_five_card_hand requires exactly 5 cards")

    ranks_desc = _sorted_rank_values_desc(cards)
    flush = _is_flush(cards)
    straight_high = _straight_high_card(ranks_desc)
    rank_count_pairs = _rank_counts(cards)  # [(rank, count), ...] sorted

    # Straight Flush
    if flush and straight_high is not None:
        return EvaluatedHand(
            HandCategory.STRAIGHT_FLUSH, (straight_high,), tuple(cards)
        )

    # Four of a Kind
    if rank_count_pairs[0][1] == 4:
        quad_rank = rank_count_pairs[0][0]
        kicker = max(r for r, _ in rank_count_pairs if r != quad_rank)
        return EvaluatedHand(
            HandCategory.FOUR_OF_A_KIND, (quad_rank, kicker), tuple(cards)
        )

    # Full House
    if rank_count_pairs[0][1] == 3 and rank_count_pairs[1][1] == 2:
        trip_rank = rank_count_pairs[0][0]
        pair_rank = rank_count_pairs[1][0]
        return EvaluatedHand(
            HandCategory.FULL_HOUSE, (trip_rank, pair_rank), tuple(cards)
        )

    # Flush
    if flush:
        return EvaluatedHand(HandCategory.FLUSH, tuple(ranks_desc), tuple(cards))

    # Straight
    if straight_high is not None:
        return EvaluatedHand(HandCategory.STRAIGHT, (straight_high,), tuple(cards))

    # Three of a Kind
    if rank_count_pairs[0][1] == 3:
        trip_rank = rank_count_pairs[0][0]
        kickers = [r for r, _ in rank_count_pairs if r != trip_rank]
        kickers_sorted = sorted(kickers, reverse=True)
        return EvaluatedHand(
            HandCategory.THREE_OF_A_KIND,
            (trip_rank, *tuple(kickers_sorted)),
            tuple(cards),
        )

    # Two Pair
    if rank_count_pairs[0][1] == 2 and rank_count_pairs[1][1] == 2:
        pair_high = max(rank_count_pairs[0][0], rank_count_pairs[1][0])
        pair_low = min(rank_count_pairs[0][0], rank_count_pairs[1][0])
        kicker = max(r for r, _ in rank_count_pairs if r not in (pair_high, pair_low))
        return EvaluatedHand(
            HandCategory.TWO_PAIR, (pair_high, pair_low, kicker), tuple(cards)
        )

    # One Pair
    if rank_count_pairs[0][1] == 2:
        pair_rank = rank_count_pairs[0][0]
        kickers = [r for r, _ in rank_count_pairs if r != pair_rank]
        kickers_sorted = sorted(kickers, reverse=True)
        return EvaluatedHand(
            HandCategory.PAIR, (pair_rank, *tuple(kickers_sorted)), tuple(cards)
        )

    # High Card
    return EvaluatedHand(HandCategory.HIGH_CARD, tuple(ranks_desc), tuple(cards))


def evaluate_best_hand(cards: List[Card]) -> EvaluatedHand:
    """Evaluate the best 5-card hand from up to 7 cards."""
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a hand")
    best: Optional[EvaluatedHand] = None
    for combo in combinations(cards, 5):
        evaluated = evaluate_five_card_hand(list(combo))
        if best is None or (evaluated.category, evaluated.tiebreakers) > (
            best.category,
            best.tiebreakers,
        ):
            best = evaluated
    assert best is not None
    return best


def compare_hands(a: EvaluatedHand, b: EvaluatedHand) -> int:
    """Compare two evaluated hands. Return 1 if a>b, -1 if a<b, 0 if equal."""
    if a.category != b.category:
        return 1 if a.category > b.category else -1
    if a.tiebreakers != b.tiebreakers:
        return 1 if a.tiebreakers > b.tiebreakers else -1
    return 0


def hand_category_to_string(category: HandCategory) -> str:
    mapping = {
        HandCategory.HIGH_CARD: "High Card",
        HandCategory.PAIR: "Pair",
        HandCategory.TWO_PAIR: "Two Pair",
        HandCategory.THREE_OF_A_KIND: "Three of a Kind",
        HandCategory.STRAIGHT: "Straight",
        HandCategory.FLUSH: "Flush",
        HandCategory.FULL_HOUSE: "Full House",
        HandCategory.FOUR_OF_A_KIND: "Four of a Kind",
        HandCategory.STRAIGHT_FLUSH: "Straight Flush",
    }
    return mapping.get(category, str(category))
