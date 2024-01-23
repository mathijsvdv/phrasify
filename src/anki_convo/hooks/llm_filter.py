import re
from dataclasses import dataclass
from typing import Optional

from anki import hooks
from anki.template import TemplateRenderContext

from ..card import CardSide, TextCard
from ..card_generator import (
    CardGenerator,
    CardGeneratorConfig,
    CardGeneratorFactory,
    LanguagePromptInputConfig,
    cached2_card_generator_factory,
    create_card_generator,
)
from ..error import CardGenerationError
from ..factory import get_card_side
from ..logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LLMFilterConfig:
    """Configuration for the LLMFilter."""

    card_generator: CardGeneratorConfig
    card_side: str


@dataclass
class LLMFilter:
    """Filter that generates the front or back of a language card from the front text
    inserted into a prompt."""

    def __init__(self, card_generator: CardGenerator, card_side: CardSide):
        self.card_generator = card_generator
        self.card_side = card_side

    def __call__(self, field_text: str, field_name: str) -> str:
        if field_text == f"({field_name})":
            # It's just the example text for the field, make a placeholder
            return (
                f"<llm filter applied to '{field_text}' field "
                f"(f{self.card_side.value} side)>"
            )

        input_card = TextCard(**{field_name.lower(): field_text})

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

        card = next(iter(self.card_generator(input_card)))
        return getattr(card, self.card_side.value)


def create_llm_filter(
    config: LLMFilterConfig,
    card_generator_factory: Optional[CardGeneratorFactory] = None,
):
    """Create an LLMFilter from the config."""
    if card_generator_factory is None:
        card_generator_factory = create_card_generator

    card_generator = card_generator_factory(config.card_generator)
    card_side = get_card_side(config.card_side)
    return LLMFilter(card_generator=card_generator, card_side=card_side)


def parse_llm_filter_name(filter_name: str) -> LLMFilterConfig:
    # TODO Make lang_front and lang_back optional by considering the config and possibly
    #  the name of the deck that we're in.

    pattern = (
        r"llm (?P<prompt_name>[a-zA-Z0-9_-]+) "
        r"lang_front=(?P<lang_front>[a-zA-Z]+) "
        r"lang_back=(?P<lang_back>[a-zA-Z]+) "
        r"(?P<card_side>(front|back|f|b))"
    )
    match = re.match(pattern, filter_name)

    if match:
        prompt_name = match.group("prompt_name")
        lang_front = match.group("lang_front")
        lang_back = match.group("lang_back")
        card_side = match.group("card_side")
    else:
        msg = f"Invalid filter name: '{filter_name}'"
        raise ValueError(msg)

    card_generator_config = CardGeneratorConfig(
        prompt_name=prompt_name,
        prompt_inputs=LanguagePromptInputConfig(
            source_language=lang_front, target_language=lang_back
        ),
    )

    llm_filter_config = LLMFilterConfig(
        card_generator=card_generator_config, card_side=card_side
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
    {{llm <prompt_name> lang_front=<lang_front> lang_back=<lang_back> <card_side>:<field_name>}}

    Here:
    - <prompt_name> is the name of the prompt
    - <lang_front> and <lang_back> are the languages to use for the front and back of
      the card
    - <card_side> refers to the side ('front' or 'back') that will be generated. Use
      'front' to replace the field with the generated front of the card. Use 'back' to
      replace the field with the generated back of the card.
    - <field_name> refers to the field name, e.g. 'Front' or 'Back' for basic cards.

    For example, to generate sentences in English (front) and Ukrainian (back) from
    the 'Front' field, use:
    {{llm vocab-to-sentence lang_front=English lang_back=Ukrainian front:Front}}
    for the front of the card, and:
    {{llm vocab-to-sentence lang_front=English lang_back=Ukrainian back:Front}}
    for the back of the card.
    """  # noqa: E501
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

    return filt(field_text=field_text, field_name=field_name)


def invalid_name(filter_name: str) -> str:
    return f"Invalid filter name: {filter_name}"


def init_llm_filter():
    # register our function to be called when the hook fires
    hooks.field_filter.append(llm_filter)
