from anki_convo.card import TranslationCard


class CountingCardGenerator:
    """Card generator that returns a fixed number of cards with the same source
    and target.

    It keeps track of how often it was called in order to test that lru_cache works.
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
