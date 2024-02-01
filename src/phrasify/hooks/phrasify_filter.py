from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Protocol

from ..card import TranslationCard
from ..card_gen import (
    CardFactory,
    CardFactoryCreator,
    CardGeneratorConfig,
    cached2_card_factory_creator,
    create_card_factory,
)
from ..logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LanguageFieldNames:
    """Names of the fields that contain words in the source and target languages.

    Used to determine which fields to use for the card that will be fed as
    input to the card generator.
    """

    source: str
    target: str

    def create_card(self, note: Mapping[str, str]) -> TranslationCard:
        """Create a TranslationCard from an Anki note

        A note is a mapping of field names to field values for a card).
        """
        return TranslationCard(source=note[self.source], target=note[self.target])

    def get_field_text(self, card: TranslationCard, field_name: str) -> str:
        """Get the appropriate attribute of the card based on the field name."""
        if field_name == self.source:
            return card.source
        elif field_name == self.target:
            return card.target
        else:
            message = f"Invalid field name: {field_name}"
            raise ValueError(message)


@dataclass(frozen=True)
class PhrasifyFilterConfig:
    """Configuration for the PhrasifyFilter."""

    card_generator: CardGeneratorConfig
    language_field_names: LanguageFieldNames


class HasNote(Protocol):
    """Protocol for an object that has a note (`anki.template.TemplateRenderContext`)

    This protocol has been introduced to more loosely couple the PhrasifyFilter to Anki
    and make it easier to test.
    """

    def note(self) -> Mapping[str, str]:
        """Return the note that is being rendered.

        A note is a mapping of field names to field values for a card.
        """
        ...


@dataclass
class PhrasifyFilter:
    """Filter that generates a new card using an LLM and replaces the given field with
    the generated one."""

    def __init__(
        self, card_factory: CardFactory, language_field_names: LanguageFieldNames
    ):
        self.card_factory = card_factory
        self.language_field_names = language_field_names

    def __call__(self, field_text: str, field_name: str, context: HasNote) -> str:
        if field_text == f"({field_name})":
            # It's just the example text for the field, make a placeholder
            return f"(phrasify filter applied to '{field_name}' field)"

        input_card = self.language_field_names.create_card(context.note())
        new_card = self.card_factory(input_card)
        new_field_text = self.language_field_names.get_field_text(new_card, field_name)

        if new_field_text.strip() == "":
            logger.warning(
                f"Empty field text. Returning field text {field_text!r} unchanged"
            )
            if field_text.strip() == "":
                return (
                    f"(phrasify filter was applied to an empty field. The LLM will be "
                    f"more effective at generating cards if both "
                    f"the '{self.language_field_names.source}' field and "
                    f"the '{self.language_field_names.target}' field are filled with "
                    f"words in the source and target languages, respectively.)"
                )

            return field_text
        return new_field_text


def create_phrasify_filter(
    config: PhrasifyFilterConfig,
    card_factory_creator: CardFactoryCreator | None = None,
):
    """Create a PhrasifyFilter from the config."""
    if card_factory_creator is None:
        card_factory_creator = create_card_factory

    card_factory = card_factory_creator(config.card_generator)
    return PhrasifyFilter(
        card_factory=card_factory, language_field_names=config.language_field_names
    )


def parse_phrasify_filter_name(filter_name: str) -> PhrasifyFilterConfig:
    # TODO Make source_lang and target_lang optional by considering the config and
    # possibly the name of the deck that we're in.

    pattern = (
        r"phrasify (?P<prompt_name>[a-zA-Z0-9_-]+) "
        r"source_lang=(?P<source_language>[a-zA-Z0-9_-]+) "
        r"target_lang=(?P<target_language>[a-zA-Z0-9_-]+) "
        r"source_field=(?P<source_field_name>[a-zA-Z0-9_-]+) "
        r"target_field=(?P<target_field_name>[a-zA-Z0-9_-]+)"
    )
    match = re.match(pattern, filter_name)

    if match:
        prompt_name = match.group("prompt_name")
        source_language = match.group("source_language")
        target_language = match.group("target_language")
        source_field_name = match.group("source_field_name")
        target_field_name = match.group("target_field_name")
    else:
        msg = f"Invalid filter name: '{filter_name}'"
        raise ValueError(msg)

    card_generator_config = CardGeneratorConfig(
        prompt_name=prompt_name,
        source_language=source_language,
        target_language=target_language,
    )
    language_field_names = LanguageFieldNames(
        source=source_field_name, target=target_field_name
    )

    phrasify_filter_config = PhrasifyFilterConfig(
        card_generator=card_generator_config, language_field_names=language_field_names
    )

    return phrasify_filter_config


def phrasify_filter(
    field_text: str,
    field_name: str,
    filter_name: str,
    context: HasNote,
    card_factory_creator: CardFactoryCreator | None = None,
) -> str:
    """Filter that generates the front or back of a language card from the front text

    It can be activated by a filter name like:
    {{phrasify <prompt> source_lang=<source_lang> target_lang=<target_lang> source_field=<source_field> target_field=<target_field>:<field>}}

    Here:
    - <prompt> is the name of the prompt
    - <source_lang> and <target_lang> are the source (known) and target (to learn)
        languages, respectively.
    - <source_field> and <target_field> are the field names that contain words in the
        source and target languages, respectively. These fields are used as input to
        generate new cards with the LLM.
    - <field> refers to the field name, e.g. 'Front' or 'Back' for basic cards. This
        is used to determine whether to replace the front or back of the card.

    For example, suppose we have a card with fields Front='friend' (English)
    and Back='друг' (Ukrainian). If we replace {{Front}} and {{Back}} with the filters
    {{phrasify vocab-to-sentence source_lang=English target_lang=Ukrainian source_field=Front target_field=Back:Front}}
    {{phrasify vocab-to-sentence source_lang=English target_lang=Ukrainian source_field=Front target_field=Back:Back}}
    respectively, then:
    - The Front field is replaced with a sentence like: "She has many friends."
    - The Back field is replaced with a sentence like: "У неї багато друзів."

    Notes
    -----
    If the LLM fails to generate a card, the field text is returned unchanged.
    """  # noqa: E501, RUF002
    logger.debug("phrasify_filter called")
    if not filter_name.startswith("phrasify"):
        # not our filter, return string unchanged
        return field_text

    try:
        filter_config = parse_phrasify_filter_name(filter_name)
    except ValueError:
        return invalid_name(filter_name)

    if card_factory_creator is None:
        card_factory_creator = create_card_factory

    card_factory_creator = cached2_card_factory_creator(
        id(context), card_factory_creator
    )
    filt = create_phrasify_filter(
        filter_config, card_factory_creator=card_factory_creator
    )

    return filt(field_text=field_text, field_name=field_name, context=context)


def invalid_name(filter_name: str) -> str:
    return f"(Invalid filter name: {filter_name})"


def init_phrasify_filter():
    from anki import hooks

    # register our function to be called when the hook fires
    hooks.field_filter.append(phrasify_filter)
