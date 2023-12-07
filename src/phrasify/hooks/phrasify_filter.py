import json
import re
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Mapping

from anki import hooks
from anki.template import TemplateRenderContext

from ..card import TranslationCard
from ..chains.base import Chain
from ..constants import GENERATED_CARDS_DIR
from ..error import CardGenerationError, ChainError
from ..factory import get_card_side, get_chain, get_llm_name, get_prompt
from ..logging import get_logger

# Possible hooks and filters to use
# from anki.hooks import card_did_render, field_filter


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


def parse_text_card_response(response: Dict[str, str]) -> List[TextCard]:
    """Parse the response from an LLM into a list of TextCard objects"""
    # TODO If using CSV, need to be robust to:
    #   - Multiple sentences
    #   - Commas in the sentences
    #   - Quotes vs no quotes
    #   - Headers vs no headers
    #   - Newlines in the sentences?
    #   - Multiple paragraphs
    #   - Spaces around the sentences.
    #   - ', ' vs ',' delimiter

    # TODO We can also start with JSON, which is a bit easier to parse.
    # But the response may be longer and require more tokens (more expensive).
    # TODO In any case, probably want to parse the response into a list of
    # dictionaries first, then convert each to cards.
    response = response["result"]["text"]
    card_dicts = json.loads(response)

    return [TextCard.from_dict(card_dict) for card_dict in card_dicts]


CardGenerator = Callable[[str], Iterable[TextCard]]
CardFactory = Callable[[str], TextCard]


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
class ChainCardGenerator(CardGenerator):
    """Can be called to generate language cards from an LLMInputChain."""

    chain: Chain[Dict[str, Any], str]
    llm: str
    prompt: str
    prompt_inputs: Dict[str, Any]

    @property
    def n_cards(self) -> int:
        return self.prompt_inputs.get("n_cards", 1)

    def get_chain_inputs(self, field_text: str) -> Dict[str, Any]:
        return {
            "llm": self.llm,  # TODO Should this be a string or an LLM object?
            "prompt": self.prompt,
            "prompt_inputs": dict(**self.prompt_inputs, field_text=field_text),
        }

    def __call__(self, field_text: str) -> List[TextCard]:
        """Generate multiple language cards from the front text inserted into a
        prompt."""
        logger.debug(
            f"{self.__class__.__name__} generating {self.n_cards} cards "
            f"from field text {field_text!r},"
            f"using chain {self.chain} with llm {self.llm!r}. "
        )
        if self.n_cards == 0:
            return []

        chain_inputs = self.get_chain_inputs(field_text)
        try:
            response = self.chain(chain_inputs)
        except ChainError as e:
            msg = f"Error generating card using chain inputs: {chain_inputs}"
            raise CardGenerationError(msg) from e

        cards = parse_text_card_response(response)

        return cards


class TextCardEncoder(json.JSONEncoder):
    """JSON encoder for TextCard objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, TextCard):
            return o.to_dict()
        return super().default(o)


class JSONCachedCardGenerator(CardGenerator):
    """Can be called to generate language cards. Cache the result as a JSON."""

    def __init__(
        self, card_generator: CardGenerator, min_cards: int = 5, name: str = "default"
    ):
        self.card_generator = card_generator
        self.min_cards = min_cards
        self.name = name

    def get_cache_path(self, field_text: str) -> str:
        """Get the path to the cache file."""
        # TODO Need to put the card ID in the cache path, so that we can have
        # different cards with the same field_text.

        return GENERATED_CARDS_DIR / f"{self.name}_{field_text}.json"

    def get_from_cache(self, field_text: str) -> Deque[TextCard]:
        """Get the cards from the cache, if they exist."""
        cache_path = self.get_cache_path(field_text)
        try:
            with open(cache_path) as f:
                cards = json.load(f, object_hook=TextCard.from_dict)

        except FileNotFoundError:
            cards = []

        return deque(cards)

    def write_to_cache(self, field_text: str, cards: Iterable[TextCard]):
        """Write the cards to the cache."""
        cache_path = self.get_cache_path(field_text)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(list(cards), f, cls=TextCardEncoder)

    def __call__(self, field_text: str) -> List[TextCard]:
        """Generate language cards from the front text inserted into a prompt."""
        cards = self.get_from_cache(field_text)
        logger.debug(
            f"Retrieving {len(cards)} cards from cache for field text {field_text!r}"
        )

        while True:
            if len(cards) < self.min_cards:
                logger.debug(
                    f"Cache has {len(cards)} < {self.min_cards} cards, "
                    f"generating more for field text {field_text!r}"
                )
                new_cards = self.card_generator(field_text)
                cards.extend(new_cards)
                logger.debug(
                    f"Extended cache with {len(new_cards)} new cards "
                    f"for field text {field_text!r}"
                )

            card = cards.popleft()
            self.write_to_cache(field_text, cards)
            yield card


class NextCardFactory(CardFactory):
    """Can be called to take the next language card from a card generator."""

    def __init__(self, card_generator: CardGenerator):
        self.card_generator = card_generator
        self._card_iterator = None

    def __call__(self, field_text: str) -> TextCard:
        """Take next language card from the front text inserted into a prompt."""

        if self._card_iterator is None:
            try:
                self._card_iterator = iter(self.card_generator(field_text))
            except CardGenerationError as e:
                logger.error(f"Error in card generator: {e}")
                self._card_iterator = iter([])

        try:
            card = next(self._card_iterator)
        except StopIteration:
            card = TextCard(front=field_text, back=field_text)
            logger.warning(f"No cards generated. Creating placeholder card {card}")

        return card


def create_card_factory(config: CardGeneratorConfig):
    """Create a CardGenerator from the config."""
    llm_name = get_llm_name()
    prompt = get_prompt(config.prompt_name)
    chain = get_chain()

    prompt_inputs = {"n_cards": 10}
    prompt_inputs.update(
        {"lang_front": config.lang_front, "lang_back": config.lang_back}
    )

    name = f"{config.prompt_name}_{config.lang_front}_{config.lang_back}"
    card_generator = ChainCardGenerator(
        chain=chain, llm=llm_name, prompt=prompt, prompt_inputs=prompt_inputs
    )
    card_generator = JSONCachedCardGenerator(card_generator, name=name)

    card_factory = NextCardFactory(card_generator)
    card_factory = lru_cache(maxsize=None)(card_factory)
    return card_factory


CardGeneratorFactory = Callable[[CardGeneratorConfig], CardGenerator]
CardFactoryCreator = Callable[[CardGeneratorConfig], CardFactory]


@dataclass(frozen=True)
class LLMFilterConfig:
    """Configuration for the LLMFilter."""

    card_generator: CardGeneratorConfig
    card_side: str


@dataclass
class LLMFilter:
    """Filter that generates the front or back of a language card from the front text
    inserted into a prompt."""

    def __init__(self, card_factory: CardFactory, card_side: CardSide):
        self.card_factory = card_factory
        self.card_side = card_side

    def __call__(self, field_text: str, field_name: str) -> str:
        if field_text == f"({field_name})":
            # It's just the example text for the field, make a placeholder
            return (
                f"<llm filter applied to '{field_text}' field "
                f"(f{self.card_side.value} side)>"
            )

        card = self.card_factory(field_text)
        return getattr(card, self.card_side.value)


@dataclass
class PhrasifyFilter:
    """Filter that generates a new card using an LLM and replaces the given field with
    the generated one."""

    def __init__(
        self, card_generator: CardGenerator, language_field_names: LanguageFieldNames
    ):
        self.card_generator = card_generator
        self.language_field_names = language_field_names

    def __call__(self, field_text: str, field_name: str, context: HasNote) -> str:
        if field_text == f"({field_name})":
            # It's just the example text for the field, make a placeholder
            return f"(phrasify filter applied to '{field_name}' field)"

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

        new_card = next(iter(cards))
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
    card_generator_factory: CardGeneratorFactory | None = None,
):
    """Create an PhrasifyFilter from the config."""
    if card_generator_factory is None:
        card_generator_factory = create_card_generator

    card_generator = card_generator_factory(config.card_generator)
    return PhrasifyFilter(
        card_generator=card_generator, language_field_names=config.language_field_names
    )


def create_llm_filter(
    config: LLMFilterConfig,
    card_factory_creator: Optional[CardFactoryCreator] = None,
):
    """Create an LLMFilter from the config."""
    if card_factory_creator is None:
        card_factory_creator = create_card_factory

    card_factory = card_factory_creator(config.card_generator)
    card_side = get_card_side(config.card_side)
    return LLMFilter(card_factory=card_factory, card_side=card_side)


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
        prompt_name=prompt_name, lang_front=lang_front, lang_back=lang_back
    )
    llm_filter_config = LLMFilterConfig(
        card_generator=card_generator_config, card_side=card_side
    )

    return llm_filter_config


class CachedCardFactoryCreator:
    """Create a CardGenerator from the config. Cache the result."""

    def __init__(self, context_id: int):
        self.context_id = context_id
        self._call = lru_cache(maxsize=None)(create_card_factory)

    def __call__(self, config: CardGeneratorConfig) -> CardFactory:
        return self._call(config)


cached2_card_factory_creator = lru_cache(maxsize=1)(CachedCardFactoryCreator)


def phrasify_filter(
    field_text: str,
    field_name: str,
    filter_name: str,
    context: HasNote,
    card_generator_factory: CardGeneratorFactory | None = None,
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

    if card_generator_factory is None:
        card_generator_factory = create_card_generator

    card_generator_factory = cached2_card_generator_factory(
        id(context), card_generator_factory
    )
    filt = create_phrasify_filter(
        filter_config, card_generator_factory=card_generator_factory
    )

    return filt(field_text=field_text, field_name=field_name, context=context)


def invalid_name(filter_name: str) -> str:
    return f"(Invalid filter name: {filter_name})"


def init_phrasify_filter():
    from anki import hooks

    # register our function to be called when the hook fires
    hooks.field_filter.append(phrasify_filter)


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

    card_factory_creator = cached2_card_factory_creator(context_id=id(context))
    filt = create_llm_filter(filter_config, card_factory_creator=card_factory_creator)

    return filt(field_text=field_text, field_name=field_name)


def invalid_name(filter_name: str) -> str:
    return f"Invalid filter name: {filter_name}"


def init_llm_filter():
    # register our function to be called when the hook fires
    hooks.field_filter.append(llm_filter)
