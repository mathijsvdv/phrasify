from functools import lru_cache
from typing import Callable, Mapping, TypeVar

import requests

from phrasify.card import TranslationCard
from phrasify.card_gen import CardGeneratorConfig

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

    def __init__(self, n_cards: int = 1):
        self.n_cards = n_cards
        self.n_times_called = 0

    def __call__(self, card: TranslationCard):
        self.n_times_called += 1
        source = f"Source of card for {card} after {self.n_times_called} call(s)"
        target = f"Target of card for {card} after {self.n_times_called} call(s)"

        return [
            TranslationCard(
                source=f"{source} (card {i})", target=f"{target} (card {i})"
            )
            for i in range(self.n_cards)
        ]


class EmptyCardGenerator:
    """Card generator that returns empty cards."""

    def __init__(self, n_cards: int = 1):
        self.n_cards = n_cards

    def __call__(self, card: TranslationCard):  # noqa: ARG002
        return [TranslationCard() for _ in range(self.n_cards)]


class ErrorCardGenerator:
    """Card generator that raises an error."""

    def __init__(self, error: Exception):
        self.error = error

    def __call__(self, card: TranslationCard):  # noqa: ARG002
        raise self.error


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


def create_counting_card_generator(
    config: CardGeneratorConfig,
) -> CountingCardGenerator:
    """Create a CountingCardGenerator from a config."""
    return lru_cache(maxsize=None)(CountingCardGenerator(config.n_cards))
