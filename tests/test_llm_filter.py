import pytest

from anki_convo.card_gen import CardGeneratorConfig
from anki_convo.hooks.llm_filter import (
    LanguageFieldNames,
    LLMFilter,
    LLMFilterConfig,
    parse_llm_filter_name,
)
from tests.mocks import CountingCardGenerator


def test_parse_llm_filter_name_valid():
    filter_name = (
        "llm vocab-to-sentence source_lang=English target_lang=Ukrainian "
        "source_field=Front target_field=Back"
    )
    result = parse_llm_filter_name(filter_name)
    expected = LLMFilterConfig(
        card_generator=CardGeneratorConfig(
            prompt_name="vocab-to-sentence",
            source_language="English",
            target_language="Ukrainian",
        ),
        language_field_names=LanguageFieldNames(source="Front", target="Back"),
    )

    assert result == expected


def test_parse_llm_filter_name_invalid():
    filter_name = "invalid_filter_name"
    with pytest.raises(ValueError):
        parse_llm_filter_name(filter_name)


@pytest.fixture()
def counting_card_generator(n_cards):
    card_generator = CountingCardGenerator(n_cards=n_cards)

    return card_generator


@pytest.fixture()
def llm_filt(counting_card_generator):
    language_field_names = LanguageFieldNames(source="Front", target="Back")
    filt = LLMFilter(
        card_generator=counting_card_generator,
        language_field_names=language_field_names,
    )
    return filt


# @pytest.mark.parametrize(())
# def test_llm_filter(llm_filt: LLMFilter, field_text, field_name, expected):
#     if llm_filt.card_generator.n_cards == 0:
#         return field_text

#     result = llm_filt(field_text=field_text, field_name="Front")

#     if counting_card_generator.n_cards == 0:
#         pass

#     # Create an LLMFilter instance
#     filter = LLMFilter(mock_card_generator, CardSide.FRONT)

#     # Set up the mock to return a TextCard with the expected front and back
#     mock_card = MagicMock()
#     mock_card.front = "Hello, how are you?"
#     mock_card.back = "Привіт, як справи?"
#     mock_card_generator.return_value = [mock_card]

#     # Call the filter with some field text and name
#     field_text = "Hello"
#     field_name = "Front"
#     result = filter(field_text, field_name)

#     # Check that the mock was called with the expected field text
#     mock_card_generator.assert_called_once_with(field_text=field_text)

#     # Check that the result is the expected card side
#     assert result == mock_card.front
