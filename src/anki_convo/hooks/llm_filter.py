from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from anki.template import TemplateRenderContext

from ..card import TranslationCard
from ..card_gen import (
    CardGenerator,
    CardGeneratorConfig,
    CardGeneratorFactory,
    cached2_card_generator_factory,
    create_card_generator,
)
from ..error import CardGenerationError
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
class LLMFilterConfig:
    """Configuration for the LLMFilter."""

    card_generator: CardGeneratorConfig
    language_field_names: LanguageFieldNames


@dataclass
class LLMFilter:
    """Filter that generates a new card using an LLM and replaces the given field with
    the generated one."""

    def __init__(
        self, card_generator: CardGenerator, language_field_names: LanguageFieldNames
    ):
        self.card_generator = card_generator
        self.language_field_names = language_field_names

    def __call__(
        self, field_text: str, field_name: str, context: TemplateRenderContext
    ) -> str:
        if field_text == f"({field_name})":
            # It's just the example text for the field, make a placeholder
            return f"<llm filter applied to '{field_text}' field>"

        input_card = self.language_field_names.create_card(context.note())

        try:
            cards = self.card_generator(input_card)
        except CardGenerationError as e:
            # Error generating card, return the field text unchanged
            logger.error(
                f"Error in card generator: {e}\nReturning field text "
                f"{field_text!r} unchanged"
            )
            return field_text

        if not cards:
            logger.warning(
                f"No cards generated. Returning field text {field_text!r} unchanged"
            )
            # No cards generated, return the field text unchanged
            return field_text

        new_card = next(iter(self.card_generator(input_card)))
        new_field_text = self.language_field_names.get_field_text(new_card, field_name)

        if new_field_text.strip() == "":
            logger.warning(
                f"Empty field text. Returning field text {field_text!r} unchanged"
            )
            if field_text.strip() == "":
                return (
                    f"<llm filter was applied to an empty field. The LLM will be more "
                    f"effective at generating cards if both "
                    f"the '{self.language_field_names.source}' field and "
                    f"the '{self.language_field_names.target}' field are filled with "
                    f"words in the source and target languages, respectively.>"
                )

            return field_text
        return new_field_text


def create_llm_filter(
    config: LLMFilterConfig,
    card_generator_factory: CardGeneratorFactory | None = None,
):
    """Create an LLMFilter from the config."""
    if card_generator_factory is None:
        card_generator_factory = create_card_generator

    card_generator = card_generator_factory(config.card_generator)
    return LLMFilter(
        card_generator=card_generator, language_field_names=config.language_field_names
    )


def parse_llm_filter_name(filter_name: str) -> LLMFilterConfig:
    # TODO Make source_lang and target_lang optional by considering the config and
    # possibly the name of the deck that we're in.

    pattern = (
        r"llm (?P<prompt_name>[a-zA-Z0-9_-]+) "
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

    llm_filter_config = LLMFilterConfig(
        card_generator=card_generator_config, language_field_names=language_field_names
    )

    return llm_filter_config


def llm_filter(
    field_text: str,
    field_name: str,
    filter_name: str,
    context: TemplateRenderContext,
) -> str:
    """Filter that generates the front or back of a language card from the front text

    It can be activated by a filter name like:
    {{llm <prompt> source_lang=<source_lang> target_lang=<target_lang> source_field=<source_field> target_field=<target_field>:<field>}}

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
    {{llm vocab-to-sentence source_lang=English target_lang=Ukrainian source_field=Front target_field=Back:Front}}
    {{llm vocab-to-sentence source_lang=English target_lang=Ukrainian source_field=Front target_field=Back:Back}}
    respectively, then:
    - The Front field is replaced with a sentence like: "She has many friends."
    - The Back field is replaced with a sentence like: "У неї багато друзів."

    Notes
    -----
    If the LLM fails to generate a card, the field text is returned unchanged.
    """  # noqa: E501, RUF002
    if not filter_name.startswith("llm"):
        # not our filter, return string unchanged
        return field_text

    try:
        filter_config = parse_llm_filter_name(filter_name)
    except ValueError:
        return invalid_name(filter_name)

    card_generator_factory = cached2_card_generator_factory(context_id=id(context))
    filt = create_llm_filter(
        filter_config, card_generator_factory=card_generator_factory
    )

    return filt(field_text=field_text, field_name=field_name, context=context)


def invalid_name(filter_name: str) -> str:
    return f"Invalid filter name: {filter_name}"


def init_llm_filter():
    from anki import hooks

    # register our function to be called when the hook fires
    hooks.field_filter.append(llm_filter)
