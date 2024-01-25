import pytest

from anki_convo.card import TranslationCard
from anki_convo.error import CardGenerationError, ChainError


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
        "card_json": card.to_json(),
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
        '{"cards": [{"source": "friend", "target": "друг"}]}',
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
