import asyncio
import time
from functools import lru_cache
from typing import Callable, Mapping, Optional, TypeVar

import requests

from phrasify.card import TranslationCard
from phrasify.card_gen import CardGeneratorConfig, NextCardFactory

T_co = TypeVar("T_co", covariant=True)


class MockResponse:
    def __init__(self, json, status_code=200):
        self._json = json
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code != 200:
            message = f"Mock error: {self.status_code}"
            raise requests.HTTPError(message)


class CountingCardGenerator:
    """Card generator that returns a fixed number of cards with the same source
    and target.

    It keeps track of how often it was called in order to test that ` lru_cache` works.
    """

    def __init__(self, n_cards: int = 1, sleep_interval: float = 0.0):
        self.n_cards = n_cards
        self.sleep_interval = sleep_interval
        self.n_times_called = 0

    def _call(self, card: TranslationCard, n_cards: Optional[int] = None):
        if n_cards is None:
            n_cards = self.n_cards

        self.n_times_called += 1
        source = f"Source of card for {card} after {self.n_times_called} call(s) with {n_cards} card(s)"  # noqa: E501
        target = f"Target of card for {card} after {self.n_times_called} call(s) with {n_cards} card(s)"  # noqa: E501

        return [
            TranslationCard(
                source=f"{source} (card {i})", target=f"{target} (card {i})"
            )
            for i in range(n_cards)
        ]

    async def acall(self, card: TranslationCard, n_cards: Optional[int] = None):
        if n_cards is None:
            n_cards = self.n_cards

        if self.sleep_interval > 0.0:
            await asyncio.sleep(self.sleep_interval * n_cards)

        return self._call(card, n_cards=n_cards)

    def __call__(self, card: TranslationCard, n_cards: Optional[int] = None):
        if n_cards is None:
            n_cards = self.n_cards

        if self.sleep_interval > 0.0:
            time.sleep(self.sleep_interval * self.n_cards)

        return self._call(card, n_cards=n_cards)


class EmptyCardGenerator:
    """Card generator that returns empty cards."""

    def __init__(self, n_cards: int = 1):
        self.n_cards = n_cards

    def __call__(
        self, card: TranslationCard, n_cards: Optional[int] = None  # noqa: ARG002
    ):
        if n_cards is None:
            n_cards = self.n_cards

        return [TranslationCard() for _ in range(n_cards)]

    async def acall(self, card: TranslationCard, n_cards: Optional[int] = None):
        return self(card, n_cards=n_cards)


class ErrorCardGenerator:
    """Card generator that raises an error."""

    def __init__(self, error: Exception):
        self.error = error

    def __call__(
        self, card: TranslationCard, n_cards: Optional[int] = None  # noqa: ARG002
    ):
        raise self.error

    async def acall(self, card: TranslationCard, n_cards: Optional[int] = None):
        return self(card, n_cards=n_cards)


class Always(Callable[..., T_co]):
    """Callable that always returns the same value."""

    def __init__(self, value: T_co):
        self.value = value

    def __call__(self, *args, **kwargs) -> T_co:  # noqa: ARG002
        return self.value


def identity(x):
    """Identity function."""
    return x


class MockTemplateRenderContext:
    def __init__(self, note: Mapping[str, str]):
        self._note = note

    def note(self):
        return self._note

    def copy(self):
        return type(self)(self._note.copy())


def create_counting_card_factory(
    config: CardGeneratorConfig,
) -> Callable[[TranslationCard], TranslationCard]:
    """Create a card factory that returns a CountingCardGenerator."""
    card_factory = NextCardFactory(CountingCardGenerator(config.n_cards))
    return lru_cache(maxsize=None)(card_factory)
