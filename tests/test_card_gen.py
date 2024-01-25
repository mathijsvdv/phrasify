import pytest

from anki_convo.card import TranslationCard
from anki_convo.card_gen import parse_translation_card_response


@pytest.mark.parametrize(
    ("response", "expected_cards"),
    [
        ("[]", []),
        (
            '[{"source": "Hello, how are you?", "target": "Привіт, як справи?"}]',
            [
                TranslationCard(
                    source="Hello, how are you?", target="Привіт, як справи?"
                )
            ],
        ),
        (
            (
                '[{"source": "Hello, how are you?", "target": "Привіт, як справи?"}, '
                '{"source": "Good morning, have a nice day!",'
                ' "target": "Доброго ранку, маєте чудовий день!"}]'
            ),
            [
                TranslationCard(
                    source="Hello, how are you?", target="Привіт, як справи?"
                ),
                TranslationCard(
                    source="Good morning, have a nice day!",
                    target="Доброго ранку, маєте чудовий день!",
                ),
            ],
        ),
        # Weirdly formatted JSON
        ("[         ]", []),
        (
            (
                '[          {  \n"source": "Hello, how are you?"  ,'
                '\n\n"target":   "Привіт, як справи?"},   '
                '\n\n\t{"source":    "Good morning, have a nice day!",'
                '\n"target": "Доброго ранку, маєте чудовий день!"}\n\n\n]'
            ),
            [
                TranslationCard(
                    source="Hello, how are you?", target="Привіт, як справи?"
                ),
                TranslationCard(
                    source="Good morning, have a nice day!",
                    target="Доброго ранку, маєте чудовий день!",
                ),
            ],
        ),
    ],
)
def test_parse_translation_card_response_valid(response, expected_cards):
    response = {"text": response}
    actual_cards = parse_translation_card_response(response)
    assert actual_cards == expected_cards


@pytest.mark.slow
@pytest.mark.expensive
def test_llm_translation_card_generator(
    llm_translation_card_generator, translation_card
):
    actual_cards = llm_translation_card_generator(translation_card)

    # TODO The language card generator is non-deterministic, so we cannot come up with
    #   fixed unit tests for this. One possibility is to judge the quality of the output
    #   through a metric like BLEU score, or let a powerful LLM like GPT-4 rate the
    #   output based on some rules.
    #   We can also try PromptWatch.

    assert len(actual_cards) == llm_translation_card_generator.n_cards
    for card in actual_cards:
        assert isinstance(card, TranslationCard)
