from functools import lru_cache

import pytest

from anki_convo.card import TranslationCard
from anki_convo.card_gen import CardGeneratorConfig
from anki_convo.hooks.llm_filter import (
    HasNote,
    LanguageFieldNames,
    LLMFilter,
    LLMFilterConfig,
    parse_llm_filter_name,
)
from tests.mocks import CountingCardGenerator, MockTemplateRenderContext


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


@pytest.fixture(
    params=[("Front", "Back"), ("Back", "Front"), ("Source", "Target")],
    ids=["Front-Back", "Back-Front", "Source-Target"],
)
def language_field_names(request):
    source, target = request.param
    return LanguageFieldNames(source=source, target=target)


@pytest.fixture()
def llm_filt(counting_card_generator, language_field_names) -> LLMFilter:
    filt = LLMFilter(
        card_generator=lru_cache(maxsize=None)(counting_card_generator),
        language_field_names=language_field_names,
    )
    return filt


@pytest.fixture()
def context(language_field_names) -> MockTemplateRenderContext:
    """Context containing information about the note that is being rendered."""
    note = {
        language_field_names.source: "decision",
        language_field_names.target: "рішення",
    }
    return MockTemplateRenderContext(note=note)


@pytest.fixture()
def example_context() -> MockTemplateRenderContext:
    """Context where the fields Front and Back just contain the field names
    in parentheses.

    This occurs when a Card Type is being previewed
    in Tools -> Manage Note Types -> Cards.
    """
    return MockTemplateRenderContext(note={"Front": "(Front)", "Back": "(Back)"})


# TODO Test that the original field text is returned if:
#      - the `card_generator` raises an CardGenerationError
#      - no cards are generated
#      - the new field text is empty (and the original field text is not)
# TODO Test that a recommendation to fill both the source and target fields is returned
#      if both original and new field texts are empty

# TODO The LLMFilter should produce the same card, given:
#      - the same card generator and the same card
#      - the same context
#      This means:
#      - The card generator should be the same instance within the same context
#      - If the card generator is the same instance, the card generator should return
#        the same cards given the same input card


def test_llm_filter(llm_filt: LLMFilter, context: HasNote):
    """Test that the LLMFilter returns the expected card.

    We call the llm_filter multiple times (for both the 'Front' and 'Back' field)
    to test that the LRU cache works and the card generator is only called once.
    """
    note = context.note()
    source_field_name = llm_filt.language_field_names.source
    target_field_name = llm_filt.language_field_names.target

    field_name = llm_filt.language_field_names.source
    field_text = note[field_name]
    source = llm_filt(field_text=field_text, field_name=field_name, context=context)

    field_name = llm_filt.language_field_names.target
    field_text = note[field_name]
    target = llm_filt(field_text=field_text, field_name=field_name, context=context)

    actual_card = TranslationCard(source=source, target=target)

    input_card = TranslationCard(
        source=note[source_field_name], target=note[target_field_name]
    )
    expected_card = TranslationCard(
        source=f"Source of card for {input_card} after 1 call(s) (card 0)",
        target=f"Target of card for {input_card} after 1 call(s) (card 0)",
    )

    assert actual_card == expected_card


@pytest.mark.parametrize("source_target", ["source", "target"])
def test_llm_filter_example_text(
    llm_filt: LLMFilter, source_target: str, example_context: HasNote
):
    """Test that the LLMFilter returns the expected example text when the field text
    is just the field name in parentheses.

    This occurs when a Card Type is being previewed
    in Tools -> Manage Note Types -> Cards.
    """
    field_name = getattr(llm_filt.language_field_names, source_target)
    field_text = f"({field_name})"
    expected = f"(llm filter applied to '{field_name}' field)"

    result = llm_filt(
        field_text=field_text, field_name=field_name, context=example_context
    )

    assert result == expected


# @pytest.mark.parametrize()
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
