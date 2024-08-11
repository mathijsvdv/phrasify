from dataclasses import dataclass
from functools import partial
from typing import List

import pytest

from phrasify.card import TranslationCard
from phrasify.card_gen import JSONCachedCardGenerator, LLMTranslationCardGenerator
from tests.mocks import Always, CountingCardGenerator, identity


@pytest.fixture(params=[1, 3, 5])
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
    "one_card_out_of_list": (
        '{"source": "Hello, how are you?", "target": "Привіт, як справи?"}',
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


def surround_with_text(s: str) -> str:
    return f"""
Absolutely! Here are some cards:

{s}

This is the end of the cards.
"""


def put_under_key(s: str, key: str = "cards") -> str:
    return f'{{"{key}": {s}}}'


@pytest.fixture(
    params=[identity, put_under_key, partial(put_under_key, key="mycards")],
    ids=["identity", "put_under_cards", "put_under_mycards"],
)
def transform_response1(request):
    return request.param


@pytest.fixture(params=[identity, surround_with_json_block, surround_with_text])
def transform_response2(request):
    return request.param


@pytest.fixture(
    params=llm_card_generation_expectations_params.values(),
    ids=llm_card_generation_expectations_params.keys(),
)
def llm_card_generation_expectation(request, transform_response1, transform_response2):
    """Fixture containing the response from the LLM (input for
    LLMTranslationCardGenerator) and the expected cards."""
    response, expected_cards = request.param
    response = transform_response1(response)
    response = transform_response2(response)
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


@pytest.fixture()
def sleeping_card_generator():
    card_generator = CountingCardGenerator(n_cards=5, sleep_interval=0.1)

    return card_generator


@pytest.fixture()
def json_cached_card_generator(sleeping_card_generator):
    try:
        card_generator = JSONCachedCardGenerator(sleeping_card_generator)
        yield card_generator
    finally:
        card_generator.clear_cache()


@pytest.fixture(
    params=[("friend", "друг"), ("to give", "давати"), ("love", "любов")],
    ids=["friend", "to give", "love"],
)
def translation_card(request):
    source, target = request.param
    return TranslationCard(source=source, target=target)
