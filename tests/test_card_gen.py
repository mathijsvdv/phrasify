from anki_convo.card import TranslationCard


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
