import dataclasses
from functools import lru_cache
from typing import Mapping

import pytest

from anki_convo.card import TranslationCard
from anki_convo.card_gen import (
    CardGeneratorConfig,
    CardGeneratorFactory,
    cached2_card_generator_factory,
)
from anki_convo.error import CardGenerationError
from anki_convo.hooks.llm_filter import (
    HasNote,
    LanguageFieldNames,
    LLMFilter,
    LLMFilterConfig,
    invalid_name,
    llm_filter,
    parse_llm_filter_name,
)
from tests.mocks import (
    CountingCardGenerator,
    EmptyCardGenerator,
    ErrorCardGenerator,
    MockTemplateRenderContext,
    create_counting_card_generator,
)


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
def empty_card_generator(n_cards):
    card_generator = EmptyCardGenerator(n_cards=n_cards)

    return card_generator


@pytest.fixture()
def error_card_generator():
    card_generator = ErrorCardGenerator(error=CardGenerationError())

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
def llm_filt_empty_card(empty_card_generator, language_field_names) -> LLMFilter:
    filt = LLMFilter(
        card_generator=lru_cache(maxsize=None)(empty_card_generator),
        language_field_names=language_field_names,
    )
    return filt


@pytest.fixture()
def llm_filt_error(error_card_generator, language_field_names) -> LLMFilter:
    filt = LLMFilter(
        card_generator=lru_cache(maxsize=None)(error_card_generator),
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
def context_empty_card(language_field_names) -> MockTemplateRenderContext:
    """Context containing information about the note that is being rendered.

    In this case, the note contains empty fields.
    """
    note = {
        language_field_names.source: "",
        language_field_names.target: "",
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


@pytest.mark.parametrize("source_target", ["source", "target"])
def test_llm_filter_card_generation_error(
    llm_filt_error: LLMFilter, context: HasNote, source_target: str
):
    """Test that the LLMFilter returns the original field text when the card generator
    raises a CardGenerationError.
    """
    note = context.note()
    filt = llm_filt_error
    field_name = getattr(filt.language_field_names, source_target)
    field_text = note[field_name]
    expected = field_text

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


@pytest.mark.parametrize("source_target", ["source", "target"])
@pytest.mark.parametrize("n_cards", [0])
def test_llm_filter_no_cards(llm_filt: LLMFilter, context: HasNote, source_target: str):
    """Test that the LLMFilter returns the original field text when the card generator
    returns no cards.
    """
    note = context.note()
    filt = llm_filt
    field_name = getattr(filt.language_field_names, source_target)
    field_text = note[field_name]
    expected = field_text

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


@pytest.mark.parametrize("source_target", ["source", "target"])
def test_llm_filter_empty_field_text(
    llm_filt_empty_card: LLMFilter, context: HasNote, source_target: str
):
    """Test that the LLMFilter returns the original field text when the new field text
    is empty (and the original field text is not).
    """
    note = context.note()
    filt = llm_filt_empty_card
    field_name = getattr(filt.language_field_names, source_target)
    field_text = note[field_name]
    expected = field_text

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


def test_llm_filter_empty_field_text_both(
    llm_filt_empty_card: LLMFilter, context_empty_card: HasNote
):
    """Test that the LLMFilter returns a recommendation to fill both the source and
    target fields when the new field text is empty and the original field text is also
    empty.
    """
    filt = llm_filt_empty_card
    context = context_empty_card
    field_name = filt.language_field_names.source
    field_text = ""
    expected = (
        "(llm filter was applied to an empty field. The LLM will be more "
        "effective at generating cards if both "
        f"the '{filt.language_field_names.source}' field and "
        f"the '{filt.language_field_names.target}' field are filled with "
        f"words in the source and target languages, respectively.)"
    )

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


def test_invalid_name():
    filter_name = "invalid_filter_name"
    expected = "(Invalid filter name: invalid_filter_name)"

    result = invalid_name(filter_name)

    assert result == expected


# TODO The LLMFilter should produce the same card, given:
#      - the same card generator and the same card
#      - the same context
#      This means:
#      - The card generator should be the same instance within the same context
#      - If the card generator is the same instance, the card generator should return
#        the same cards given the same input card


def all_unique(iterable):
    """Return True if all elements of the iterable are unique, False otherwise."""
    return len(set(iterable)) == len(iterable)


def test_cached2_card_generator_factory():
    """Test that the card generator factory returns the same instance of the card
    generator when called multiple times with the same context and config.

    The context really needs to be the same instance, not just have the same contents.
    But the config can be a different instance, as long as it has the same contents.
    """

    contexts = [
        MockTemplateRenderContext(note={"Front": "friend", "Back": "друг"}),
        MockTemplateRenderContext(note={"Front": "choice", "Back": "вибір"}),
    ]

    configs = [
        CardGeneratorConfig(),
        CardGeneratorConfig(llm="mistral"),
        CardGeneratorConfig(n_cards=2),
        CardGeneratorConfig(llm="mistral", n_cards=2),
    ]

    card_generator_factory = cached2_card_generator_factory(
        id(contexts[0]), create_counting_card_generator
    )
    card_generator_factory_same = cached2_card_generator_factory(
        id(contexts[0]), create_counting_card_generator
    )
    card_generator_factory_copy = cached2_card_generator_factory(
        id(contexts[0].copy()), create_counting_card_generator
    )
    card_generator_factory_diff = cached2_card_generator_factory(
        id(contexts[1]), create_counting_card_generator
    )

    for config in configs:
        # Card generator was created from the same context and (a copy of) the same
        # config - should give the same card_generator
        card_generator1 = card_generator_factory(config)
        card_generator2 = card_generator_factory_same(dataclasses.replace(config))

        assert card_generator1 is card_generator2

    for config in configs:
        # Card generator was created from a copy of the context and (a copy of) the same
        # config - should give different card_generators because context is not the same
        card_generator1 = card_generator_factory(config)
        card_generator2 = card_generator_factory_copy(dataclasses.replace(config))

        assert card_generator1 is not card_generator2

    for config in configs:
        # Card generator was created from a different context and (a copy of) the same
        # config - should give different card_generators because context is not the same
        card_generator1 = card_generator_factory(config)
        card_generator2 = card_generator_factory_diff(dataclasses.replace(config))

        assert card_generator1 is not card_generator2

    # Card generator was created from the same context and different configs
    # - should give different card_generators because config is not the same
    card_generators = [card_generator_factory(config) for config in configs]
    assert all_unique([id(cg) for cg in card_generators])


def _test_llm_filter_hook(
    note: Mapping[str, str],
    filter_name: str,
    context: HasNote,
    card_generator_factory: CardGeneratorFactory,
    field_name: str,
    expected: str,
):
    """Test that the LLMFilter returns the expected field text (depending on the
    field)"""
    field_text = note[field_name]
    input_card = TranslationCard(source=note["Front"], target=note["Back"])
    expected = expected.format(input_card=input_card)

    actual = llm_filter(
        field_text=field_text,
        field_name=field_name,
        filter_name=filter_name,
        context=context,
        card_generator_factory=card_generator_factory,
    )

    assert actual == expected

    actual_context_copy = llm_filter(
        field_text=field_text,
        field_name=field_name,
        filter_name=filter_name,
        context=context.copy(),
        card_generator_factory=card_generator_factory,
    )

    assert actual_context_copy == expected


def _test_llm_filter_hook_front(
    note: Mapping[str, str],
    filter_name: str,
    context: HasNote,
    card_generator_factory: CardGeneratorFactory,
):
    """Test that the LLMFilter returns the expected front of the card."""
    _test_llm_filter_hook(
        note=note,
        filter_name=filter_name,
        context=context,
        card_generator_factory=card_generator_factory,
        field_name="Front",
        expected="Source of card for {input_card} after 1 call(s) (card 0)",
    )


def _test_llm_filter_hook_back(
    note: Mapping[str, str],
    filter_name: str,
    context: HasNote,
    card_generator_factory: CardGeneratorFactory,
):
    """Test that the LLMFilter returns the expected back of the card."""
    _test_llm_filter_hook(
        note=note,
        filter_name=filter_name,
        context=context,
        card_generator_factory=card_generator_factory,
        field_name="Back",
        expected="Target of card for {input_card} after 1 call(s) (card 0)",
    )


def test_llm_filter_hook():
    """Test that the LLMFilter returns the expected card."""
    # Arrange
    card_generator_factory = create_counting_card_generator

    filter_name = (
        "llm vocab-to-sentence source_lang=English target_lang=Ukrainian "
        "source_field=Front target_field=Back"
    )
    filter_name_diff = (
        "llm vocab-to-sentence source_lang=English target_lang=Spanish "
        "source_field=Front target_field=Back"
    )

    context = MockTemplateRenderContext({"Front": "friend", "Back": "друг"})
    context_diff = MockTemplateRenderContext({"Front": "friend", "Back": "amigo"})
    note = context.note()
    note_diff = context_diff.note()

    # Act & Assert
    nt_filtn_ctxs = [
        (note, filter_name, context),
        (note_diff, filter_name_diff, context_diff),
    ]

    for nt, filtn, ctx in nt_filtn_ctxs:
        _test_llm_filter_hook_front(nt, filtn, ctx, card_generator_factory)
        _test_llm_filter_hook_back(nt, filtn, ctx, card_generator_factory)


def test_llm_filter_hook_does_not_start_with_llm(context: HasNote):
    """Test that the LLMFilter returns the original field text when the field text
    does not start with "(llm".
    """
    filter_name = "not llm"
    actual = llm_filter(
        field_text="friend",
        field_name="Front",
        filter_name=filter_name,
        context=context,
    )
    expected = "friend"

    assert actual == expected


def test_llm_filter_hook_invalid_filter_name(context: HasNote):
    """Test that the LLMFilter returns the original field text when the filter name
    is invalid.
    """
    filter_name = "llm invalid_filter_name"
    actual = llm_filter(
        field_text="friend",
        field_name="Front",
        filter_name=filter_name,
        context=context,
    )
    expected = invalid_name(filter_name)

    assert actual == expected
