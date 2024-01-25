from dataclasses import dataclass
from typing import List

import pytest

from anki_convo.card import TranslationCard
from anki_convo.card_gen import LLMTranslationCardGenerator
from tests.mocks import Always, identity


@pytest.fixture(params=[0, 1, 3, 5])
def n_cards(request):
    return request.param


@dataclass
class LLMCardGenerationExpectation:
    """Expected result of calling a card generator, given the response from the LLM."""

    response: str
    expected_cards: List[TranslationCard]


llm_card_generation_expectations_params = {
    "empty": ("[]", []),
    "one_card": (
        '[{"source": "Hello, how are you?", "target": "Привіт, як справи?"}]',
        [TranslationCard(source="Hello, how are you?", target="Привіт, як справи?")],
    ),
    "two_cards": (
        (
            '[{"source": "Hello, how are you?", "target": "Привіт, як справи?"}, '
            '{"source": "Good morning, have a nice day!",'
            ' "target": "Доброго ранку, маєте чудовий день!"}]'
        ),
        [
            TranslationCard(source="Hello, how are you?", target="Привіт, як справи?"),
            TranslationCard(
                source="Good morning, have a nice day!",
                target="Доброго ранку, маєте чудовий день!",
            ),
        ],
    ),
    "empty_weird": ("[         ]", []),
    "two_cards_weird": (
        (
            '[          {  \n"source": "Hello, how are you?"  ,'
            '\n\n"target":   "Привіт, як справи?"},   '
            '\n\n\t{"source":    "Good morning, have a nice day!",'
            '\n"target": "Доброго ранку, маєте чудовий день!"}\n\n\n]'
        ),
        [
            TranslationCard(source="Hello, how are you?", target="Привіт, як справи?"),
            TranslationCard(
                source="Good morning, have a nice day!",
                target="Доброго ранку, маєте чудовий день!",
            ),
        ],
    ),
}


def surround_with_json_block(s: str) -> str:
    return f"""
Absolutely! Here are some cards:

```json
{s}
```

This is the end of the cards.
"""


@pytest.fixture(params=[identity, surround_with_json_block])
def transform_response(request):
    return request.param


@pytest.fixture(
    params=llm_card_generation_expectations_params.values(),
    ids=llm_card_generation_expectations_params.keys(),
)
def llm_card_generation_expectation(request, transform_response):
    """Fixture containing the response from the LLM (input for
    LLMTranslationCardGenerator) and the expected cards."""
    response, expected_cards = request.param
    response = transform_response(response)
    return LLMCardGenerationExpectation(
        response=response, expected_cards=expected_cards
    )


@pytest.fixture()
def llm_response(llm_card_generation_expectation: LLMCardGenerationExpectation):
    """Fixture containing the response from the LLM (input for
    TranslationCardGenerator)."""
    return llm_card_generation_expectation.response


@pytest.fixture()
def llm_expected_cards(llm_card_generation_expectation: LLMCardGenerationExpectation):
    """Fixture containing the expected cards (output for TranslationCardGenerator)."""
    return llm_card_generation_expectation.expected_cards


# TODO: Add a test for the case where the chain raises an error
# TODO: Add a test for the case where the chain returns an invalid response
@pytest.fixture()
def llm_translation_card_generator():
    chain = Always("")  # We will mock the chain's response in the tests
    generator = LLMTranslationCardGenerator(
        chain=chain,
        # n_cards, source_language and target_language are not used in the tests:
        # ultimately the chain decides how many cards to generate,
        # and with which languages.
        # We are testing the card generator's ability to adapt to the chain's
        # response, not the chain's ability to generate cards.
        n_cards=1,
        source_language="English",
        target_language="Ukrainian",
    )
    return generator


@pytest.fixture(
    params=[("friend", "друг"), ("to give", "давати"), ("love", "любов")],
    ids=["friend", "to give", "love"],
)
def translation_card(request):
    source, target = request.param
    return TranslationCard(source=source, target=target)
