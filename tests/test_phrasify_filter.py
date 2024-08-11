import dataclasses
import re
from functools import lru_cache
from typing import Mapping

import pytest

from phrasify.card import TranslationCard
from phrasify.card_gen import (
    CardFactory,
    CardFactoryCreator,
    CardGenerator,
    CardGeneratorConfig,
    JSONCachedCardGenerator,
    NextCardFactory,
    cached2_card_factory_creator,
)
from phrasify.constants import DEFAULT_N_CARDS
from phrasify.error import CardGenerationError
from phrasify.hooks.phrasify_filter import (
    HasNote,
    LanguageFieldNames,
    PhrasifyFilter,
    PhrasifyFilterConfig,
    invalid_name,
    parse_phrasify_filter_name,
    phrasify_filter,
)
from tests.mocks import (
    CountingCardGenerator,
    EmptyCardGenerator,
    ErrorCardGenerator,
    MockTemplateRenderContext,
    create_counting_card_factory,
)


def test_parse_phrasify_filter_name_valid():
    filter_name = (
        "phrasify vocab-to-sentence source_lang=English target_lang=Ukrainian "
        "source_field=Front target_field=Back"
    )
    result = parse_phrasify_filter_name(filter_name)
    expected = PhrasifyFilterConfig(
        card_generator=CardGeneratorConfig(
            prompt_name="vocab-to-sentence",
            source_language="English",
            target_language="Ukrainian",
        ),
        language_field_names=LanguageFieldNames(source="Front", target="Back"),
    )

    assert result == expected


def test_parse_phrasify_filter_name_invalid():
    filter_name = "invalid_filter_name"
    with pytest.raises(ValueError):
        parse_phrasify_filter_name(filter_name)


@pytest.fixture
def fast_n_cards():
    """
    Number of cards to generate quickly in JSONCachedCardGenerator while
    waiting for the card generator to generate the rest of the cards.
    """
    return 1


@pytest.fixture
def sleeping_card_generator(n_cards, fast_n_cards):
    card_generator = CountingCardGenerator(n_cards=n_cards, sleep_interval=0.1)

    card_generator = JSONCachedCardGenerator(
        card_generator, fast_n_cards=fast_n_cards, name="counting"
    )
    yield card_generator
    card_generator.clear_cache()


@pytest.fixture()
def empty_card_generator(n_cards, fast_n_cards):
    card_generator = EmptyCardGenerator(n_cards=n_cards)

    card_generator = JSONCachedCardGenerator(
        card_generator, fast_n_cards=fast_n_cards, name="empty"
    )
    yield card_generator

    card_generator.clear_cache()


@pytest.fixture()
def error_card_generator():
    card_generator = ErrorCardGenerator(CardGenerationError("Error"))

    card_generator = JSONCachedCardGenerator(card_generator, name="error")
    yield card_generator
    card_generator.clear_cache()


def card_generator_to_factory(card_generator: CardGenerator) -> CardFactory:
    if not isinstance(card_generator, JSONCachedCardGenerator):
        card_generator = JSONCachedCardGenerator(card_generator)

    return lru_cache(maxsize=None)(NextCardFactory(card_generator))


@pytest.fixture(
    params=[("Front", "Back"), ("Back", "Front"), ("Source", "Target")],
    ids=["Front-Back", "Back-Front", "Source-Target"],
)
def language_field_names(request):
    source, target = request.param
    return LanguageFieldNames(source=source, target=target)


@pytest.fixture()
def phrasify_filt(sleeping_card_generator, language_field_names) -> PhrasifyFilter:
    filt = PhrasifyFilter(
        card_factory=card_generator_to_factory(sleeping_card_generator),
        language_field_names=language_field_names,
    )
    return filt


@pytest.fixture()
def phrasify_filt_empty_card(
    empty_card_generator, language_field_names
) -> PhrasifyFilter:
    filt = PhrasifyFilter(
        card_factory=card_generator_to_factory(empty_card_generator),
        language_field_names=language_field_names,
    )
    return filt


@pytest.fixture()
def phrasify_filt_error(error_card_generator, language_field_names) -> PhrasifyFilter:
    filt = PhrasifyFilter(
        card_factory=card_generator_to_factory(error_card_generator),
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


def test_phrasify_filter(phrasify_filt: PhrasifyFilter, context: HasNote):
    """Test that the PhrasifyFilter returns the expected card.

    We call the phrasify_filter multiple times (for both the 'Front' and 'Back' field)
    to test that the LRU cache works and the card generator is only called once.
    """
    note = context.note()
    source_field_name = phrasify_filt.language_field_names.source
    target_field_name = phrasify_filt.language_field_names.target

    field_name = phrasify_filt.language_field_names.source
    field_text = note[field_name]
    source = phrasify_filt(
        field_text=field_text, field_name=field_name, context=context
    )

    field_name = phrasify_filt.language_field_names.target
    field_text = note[field_name]
    target = phrasify_filt(
        field_text=field_text, field_name=field_name, context=context
    )

    actual_card = TranslationCard(source=source, target=target)

    input_card = TranslationCard(
        source=note[source_field_name], target=note[target_field_name]
    )
    pattern = (
        r"(?P<source_target>Source|Target) of card for (?P<input_card>.+?) "
        r"after (?P<n_times_called>\d+) call\(s\) "
        r"with (?P<n_cards>\d+) card\(s\) \(card (?P<i_card>\d+)\)"
    )

    # Perform the match
    source_match = re.match(pattern, actual_card.source)
    target_match = re.match(pattern, actual_card.target)

    # Check the match
    if source_match and target_match:
        assert source_match.group("source_target") == "Source"
        assert target_match.group("source_target") == "Target"
        assert source_match.group("input_card") == str(input_card)
        assert target_match.group("input_card") == str(input_card)
        assert int(source_match.group("n_times_called")) == int(
            target_match.group("n_times_called")
        )
        assert int(source_match.group("n_cards")) == int(target_match.group("n_cards"))
        assert int(source_match.group("i_card")) == int(target_match.group("i_card"))


@pytest.mark.parametrize("source_target", ["source", "target"])
def test_phrasify_filter_example_text(
    phrasify_filt: PhrasifyFilter, source_target: str, example_context: HasNote
):
    """Test that the PhrasifyFilter returns the expected example text when the field
    text is just the field name in parentheses.

    This occurs when a Card Type is being previewed
    in Tools -> Manage Note Types -> Cards.
    """
    field_name = getattr(phrasify_filt.language_field_names, source_target)
    field_text = f"({field_name})"
    expected = f"(phrasify filter applied to '{field_name}' field)"

    result = phrasify_filt(
        field_text=field_text, field_name=field_name, context=example_context
    )

    assert result == expected


@pytest.mark.parametrize("source_target", ["source", "target"])
def test_phrasify_filter_card_generation_error(
    phrasify_filt_error: PhrasifyFilter, context: HasNote, source_target: str
):
    """Test that the PhrasifyFilter returns the original field text when the card
    generator raises a CardGenerationError.
    """
    note = context.note()
    filt = phrasify_filt_error
    field_name = getattr(filt.language_field_names, source_target)
    field_text = note[field_name]
    expected = field_text

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


@pytest.mark.parametrize("source_target", ["source", "target"])
@pytest.mark.parametrize(("n_cards", "fast_n_cards"), [(0, 0)])
def test_phrasify_filter_no_cards(
    phrasify_filt: PhrasifyFilter, context: HasNote, source_target: str
):
    """Test that the PhrasifyFilter returns the original field text when the card
    generator returns no cards.
    """
    note = context.note()
    filt = phrasify_filt
    field_name = getattr(filt.language_field_names, source_target)
    field_text = note[field_name]
    expected = field_text

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


@pytest.mark.parametrize("source_target", ["source", "target"])
def test_phrasify_filter_empty_field_text(
    phrasify_filt_empty_card: PhrasifyFilter, context: HasNote, source_target: str
):
    """Test that the PhrasifyFilter returns the original field text when the new field
    text is empty (and the original field text is not).
    """
    note = context.note()
    filt = phrasify_filt_empty_card
    field_name = getattr(filt.language_field_names, source_target)
    field_text = note[field_name]
    expected = field_text

    result = filt(field_text=field_text, field_name=field_name, context=context)

    assert result == expected


def test_phrasify_filter_empty_field_text_both(
    phrasify_filt_empty_card: PhrasifyFilter, context_empty_card: HasNote
):
    """Test that the PhrasifyFilter returns a recommendation to fill both the source and
    target fields when the new field text is empty and the original field text is also
    empty.
    """
    filt = phrasify_filt_empty_card
    context = context_empty_card
    field_name = filt.language_field_names.source
    field_text = ""
    expected = (
        "(phrasify filter was applied to an empty field. The LLM will be more "
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


# TODO The PhrasifyFilter should produce the same card, given:
#      - the same card generator and the same card
#      - the same context
#      This means:
#      - The card generator should be the same instance within the same context
#      - If the card generator is the same instance, the card generator should return
#        the same cards given the same input card


def all_unique(iterable):
    """Return True if all elements of the iterable are unique, False otherwise."""
    return len(set(iterable)) == len(iterable)


def test_cached2_card_factory_creator():
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

    card_factory_creator = cached2_card_factory_creator(
        id(contexts[0]), create_counting_card_factory
    )
    card_factory_creator_same = cached2_card_factory_creator(
        id(contexts[0]), create_counting_card_factory
    )
    card_factory_creator_copy = cached2_card_factory_creator(
        id(contexts[0].copy()), create_counting_card_factory
    )
    card_factory_creator_diff = cached2_card_factory_creator(
        id(contexts[1]), create_counting_card_factory
    )

    for config in configs:
        # Card factory was created from the same context and (a copy of) the same
        # config - should give the same card_factory
        card_factory1 = card_factory_creator(config)
        card_factory2 = card_factory_creator_same(dataclasses.replace(config))

        assert card_factory1 is card_factory2

    for config in configs:
        # Card factory was created from a copy of the context and (a copy of) the same
        # config - should give different card_factory because context is not the same
        card_factory1 = card_factory_creator(config)
        card_factory2 = card_factory_creator_copy(dataclasses.replace(config))

        assert card_factory1 is not card_factory2

    for config in configs:
        # Card factory was created from a different context and (a copy of) the same
        # config - should give different card_factory because context is not the same
        card_factory1 = card_factory_creator(config)
        card_factory2 = card_factory_creator_diff(dataclasses.replace(config))

        assert card_factory1 is not card_factory2

    # Card factory was created from the same context and different configs
    # - should give different card_factory objects because config is not the same
    card_generators = [card_factory_creator(config) for config in configs]
    assert all_unique([id(cg) for cg in card_generators])


def _test_phrasify_filter_hook(
    note: Mapping[str, str],
    filter_name: str,
    context: HasNote,
    card_factory_creator: CardFactoryCreator,
    field_name: str,
    expected: str,
):
    """Test that the PhrasifyFilter returns the expected field text (depending on the
    field)"""
    field_text = note[field_name]
    input_card = TranslationCard(source=note["Front"], target=note["Back"])
    expected = expected.format(input_card=input_card, n_cards=DEFAULT_N_CARDS)

    actual = phrasify_filter(
        field_text=field_text,
        field_name=field_name,
        filter_name=filter_name,
        context=context,
        card_factory_creator=card_factory_creator,
    )

    assert actual == expected

    actual_context_copy = phrasify_filter(
        field_text=field_text,
        field_name=field_name,
        filter_name=filter_name,
        context=context.copy(),
        card_factory_creator=card_factory_creator,
    )

    assert actual_context_copy == expected


def _test_phrasify_filter_hook_front(
    note: Mapping[str, str],
    filter_name: str,
    context: HasNote,
    card_factory_creator: CardFactoryCreator,
):
    """Test that the PhrasifyFilter returns the expected front of the card."""
    _test_phrasify_filter_hook(
        note=note,
        filter_name=filter_name,
        context=context,
        card_factory_creator=card_factory_creator,
        field_name="Front",
        expected="Source of card for {input_card} after 1 call(s) with {n_cards} card(s) (card 0)",  # noqa: E501
    )


def _test_phrasify_filter_hook_back(
    note: Mapping[str, str],
    filter_name: str,
    context: HasNote,
    card_factory_creator: CardFactoryCreator,
):
    """Test that the PhrasifyFilter returns the expected back of the card."""
    _test_phrasify_filter_hook(
        note=note,
        filter_name=filter_name,
        context=context,
        card_factory_creator=card_factory_creator,
        field_name="Back",
        expected="Target of card for {input_card} after 1 call(s) with {n_cards} card(s) (card 0)",  # noqa: E501
    )


def test_phrasify_filter_hook():
    """Test that the PhrasifyFilter returns the expected card."""
    # Arrange
    card_factory_creator = create_counting_card_factory

    filter_name = (
        "phrasify vocab-to-sentence source_lang=English target_lang=Ukrainian "
        "source_field=Front target_field=Back"
    )
    filter_name_diff = (
        "phrasify vocab-to-sentence source_lang=English target_lang=Spanish "
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
        _test_phrasify_filter_hook_front(nt, filtn, ctx, card_factory_creator)
        _test_phrasify_filter_hook_back(nt, filtn, ctx, card_factory_creator)


def test_phrasify_filter_hook_does_not_start_with_llm(context: HasNote):
    """Test that the PhrasifyFilter returns the original field text when the field text
    does not start with "phrasify".
    """
    filter_name = "not phrasify"
    actual = phrasify_filter(
        field_text="friend",
        field_name="Front",
        filter_name=filter_name,
        context=context,
    )
    expected = "friend"

    assert actual == expected


def test_phrasify_filter_hook_invalid_filter_name(context: HasNote):
    """Test that the PhrasifyFilter returns the original field text when the filter name
    is invalid.
    """
    filter_name = "phrasify invalid_filter_name"
    actual = phrasify_filter(
        field_text="friend",
        field_name="Front",
        filter_name=filter_name,
        context=context,
    )
    expected = invalid_name(filter_name)

    assert actual == expected
