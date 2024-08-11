import asyncio
import itertools

import pytest

from phrasify.card import TranslationCard
from phrasify.card_gen import JSONCachedCardGenerator
from phrasify.error import CardGenerationError, ChainError
from phrasify.event_loop import run_coroutine_in_thread


def test_llm_translation_card_generator(
    llm_translation_card_generator, llm_response, llm_expected_cards, mocker
):
    """Test that llm_translation_card_generator calls the chain with the correct
    inputs and returns the expected cards depending on the chain's response."""
    card = TranslationCard()
    mocker.patch.object(
        llm_translation_card_generator, "chain", return_value=llm_response
    )
    actual_cards = llm_translation_card_generator(card)

    chain_inputs = {
        "n_cards": llm_translation_card_generator.n_cards,
        "source_language": llm_translation_card_generator.source_language,
        "target_language": llm_translation_card_generator.target_language,
        "card": card,
    }
    llm_translation_card_generator.chain.assert_called_once_with(chain_inputs)

    assert actual_cards == llm_expected_cards


def test_llm_translation_card_generator_0_cards(llm_translation_card_generator):
    """Test that llm_translation_card_generator returns an empty list when
    n_cards=0."""
    card = TranslationCard()
    llm_translation_card_generator.n_cards = 0
    actual_cards = llm_translation_card_generator(card)

    assert actual_cards == []


def test_llm_translation_card_generator_chain_error(
    llm_translation_card_generator, mocker
):
    """Test that llm_translation_card_generator raises a CardGenerationError when the
    chain raises a ChainError."""
    card = TranslationCard()
    mocker.patch.object(llm_translation_card_generator, "chain", side_effect=ChainError)
    with pytest.raises(
        CardGenerationError, match="Error generating card using chain inputs"
    ):
        llm_translation_card_generator(card)


@pytest.mark.parametrize(
    "llm_response",
    [
        "This is not a valid JSON string",
        "Unmatched open bracket [",
        "Unmatched open bracket {",
        "Unmatched close bracket [}]",
        "Unmatched close bracket {]}",
        '[{"front": "friend", "back": "друг"}]',
    ],
)
def test_llm_translation_card_generator_invalid_response(
    llm_translation_card_generator, mocker, llm_response
):
    """Test that llm_translation_card_generator raises a CardGenerationError when the
    chain returns an invalid response."""
    card = TranslationCard()
    mocker.patch.object(
        llm_translation_card_generator, "chain", return_value=llm_response
    )
    with pytest.raises(CardGenerationError, match="Error parsing response from chain"):
        llm_translation_card_generator(card)


def test_json_cached_card_generator_gets_fewer_cards_first(
    json_cached_card_generator: JSONCachedCardGenerator,
):
    """
    Test that JSONCachedCardGenerator first tries to get fewer cards (faster)
    from the underlying card generator, then more cards (slower).
    """

    card = TranslationCard()
    generator = json_cached_card_generator

    # First call: get 1 card
    card_iter = generator(card)
    actual_card = next(card_iter)
    expected_card = TranslationCard(
        source=f"Source of card for {card} after 1 call(s) with 1 card(s) (card 0)",
        target=f"Target of card for {card} after 1 call(s) with 1 card(s) (card 0)",
    )
    assert actual_card == expected_card

    # Simulate other work being done. In the meantime, the cache should be filled
    # with the bigger batch of cards.
    run_coroutine_in_thread(asyncio.sleep(0.5)).result()

    # Get 5 more cards, which uses the cache with the bigger batch of cards
    actual_cards = list(itertools.islice(card_iter, 5))
    expected_cards = [
        TranslationCard(
            source=f"Source of card for {card} after 2 call(s) with 5 card(s) (card {i})",  # noqa: E501
            target=f"Target of card for {card} after 2 call(s) with 5 card(s) (card {i})",  # noqa: E501
        )
        for i in range(5)
    ]
    assert actual_cards == expected_cards
