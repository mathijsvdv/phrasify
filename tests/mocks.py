from typing import Callable, Mapping, TypeVar

from anki_convo.card import TranslationCard

T_co = TypeVar("T_co", covariant=True)


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
