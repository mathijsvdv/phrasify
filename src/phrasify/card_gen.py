import json
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Union

import requests

from .card import TranslationCard
from .chains.llm import LLMChain, LLMChainInput
from .constants import DEFAULT_N_CARDS, DEFAULT_SOURCE_LANGUAGE, DEFAULT_TARGET_LANGUAGE
from .error import CardGenerationError, ChainError, LLMParsingError
from .factory import get_api_url, get_llm, get_llm_name, get_prompt, get_prompt_name
from .logging import get_logger

logger = get_logger(__name__)


CardGenerator = Callable[[TranslationCard], List[TranslationCard]]


def _find_json_in_response(response: str) -> str:
    """Find the JSON in the response from an LLM."""
    open_brackets = "{["
    close_brackets = "}]"
    bracket_stack = []
    for i, char in enumerate(response):
        if char in open_brackets:
            i_start = i
            break
    else:
        message = f"No open bracket found in response: {response}"
        raise LLMParsingError(message)

    for i, char in enumerate(response[i_start:], start=i_start):
        if char in open_brackets:
            bracket_stack.append(char)
        elif char in close_brackets:
            error_message = f"Unmatched close bracket at index {i}"
            if len(bracket_stack) == 0:
                raise LLMParsingError(error_message)
            elif bracket_stack[-1] == open_brackets[close_brackets.index(char)]:
                bracket_stack.pop()
            else:
                raise LLMParsingError(error_message)

        if len(bracket_stack) == 0:
            i_end = i
            break

    if len(bracket_stack) > 0:
        error_message = f"Unmatched open bracket {bracket_stack[-1]}"
        raise LLMParsingError(error_message)

    return response[i_start : i_end + 1]


def _resolve_card_dicts(card_dicts: Union[List, Dict]):
    """Resolve parsed JSON into a list of card dicts."""

    if isinstance(card_dicts, dict):
        if "cards" in card_dicts:
            # The list of cards is nested under the key "cards"
            card_dicts = card_dicts["cards"]
        elif len(card_dicts) == 1:
            # The list of cards is nested under a single key
            card_dicts = card_dicts[next(iter(card_dicts.keys()))]

    if (
        isinstance(card_dicts, dict)
        and "source" in card_dicts
        and "target" in card_dicts
    ):
        # We have a single card
        card_dicts = [card_dicts]

    if not isinstance(card_dicts, list):
        message = f"Expected a list of dictionaries, but got {card_dicts!r}"
        raise LLMParsingError(message)

    return card_dicts


def _parse_translation_card_response(response: str) -> List[TranslationCard]:
    """Parse the response from an LLM into a list of TranslationCard objects"""
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

    json_response = response
    match = re.search(r"(?<=```json\n)(.*)(?=\n```)", json_response, re.DOTALL)
    if match:
        json_response = match.group(1)

    json_response = _find_json_in_response(json_response)

    try:
        card_dicts = json.loads(json_response)
    except json.JSONDecodeError as e:
        message = f"Error parsing response from chain: {response}"
        raise LLMParsingError(message) from e

    card_dicts = _resolve_card_dicts(card_dicts)

    try:
        cards = [TranslationCard(**card_dict) for card_dict in card_dicts]
    except TypeError as e:
        message = f"Error parsing cards from dicts: {card_dicts}"
        raise LLMParsingError(message) from e

    return cards


@dataclass(frozen=True)
class CardGeneratorConfig:
    """Configuration for the CardGenerator."""

    llm: str = field(default_factory=get_llm_name)
    prompt_name: str = field(default_factory=get_prompt_name)
    n_cards: int = DEFAULT_N_CARDS
    source_language: str = DEFAULT_SOURCE_LANGUAGE
    target_language: str = DEFAULT_TARGET_LANGUAGE


@dataclass
class LLMTranslationCardGenerator:
    """Can be called to generate translation cards from an input card inserted into a
    prompt."""

    chain: Callable[[LLMChainInput], str]
    n_cards: int
    source_language: str
    target_language: str

    def _get_chain_inputs(self, card: TranslationCard) -> LLMChainInput:
        return {
            "n_cards": self.n_cards,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "card_json": card.to_json(),
        }

    @classmethod
    def from_config(cls, config: CardGeneratorConfig) -> "LLMTranslationCardGenerator":
        """Create an LLMTranslationCardGenerator from a config."""
        llm = get_llm(config.llm)
        prompt = get_prompt(config.prompt_name)
        chain = LLMChain(llm=llm, prompt=prompt)
        return cls(
            chain=chain,
            n_cards=config.n_cards,
            source_language=config.source_language,
            target_language=config.target_language,
        )

    def __call__(self, card: TranslationCard) -> List[TranslationCard]:
        """Generate multiple translation cards from an input card inserted into a
        prompt."""
        logger.debug(
            f"{self.__class__.__name__} generating {self.n_cards} cards "
            f"from card {card!r}, using chain {self.chain}"
        )
        if self.n_cards == 0:
            return []

        chain_inputs = self._get_chain_inputs(card)
        try:
            response = self.chain(chain_inputs)
        except ChainError as e:
            msg = f"Error generating card using chain inputs: {chain_inputs}"
            raise CardGenerationError(msg) from e

        try:
            cards = _parse_translation_card_response(response)
        except LLMParsingError as e:
            msg = f"Error parsing response from chain: {response}"
            raise CardGenerationError(msg) from e

        return cards


@dataclass
class RemoteCardGenerator:
    """Can be called to generate translation cards from an input card by sending a
    request to a remote server."""

    url: str
    config: CardGeneratorConfig = field(default_factory=CardGeneratorConfig)

    @property
    def n_cards(self) -> int:
        """Number of cards to generate."""
        return self.config.n_cards

    def __call__(self, card: TranslationCard) -> List[TranslationCard]:
        """Generate multiple translation cards from an input card inserted into a
        prompt."""
        logger.debug(
            f"{self.__class__.__name__} generating {self.n_cards} cards "
            f"from card {card!r}, using remote server {self.url}"
        )
        if self.n_cards == 0:
            return []

        request_body = {
            "card_generator": asdict(self.config),
            "card": asdict(card),
        }

        response = requests.post(self.url, json=request_body, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            msg = f"Error generating card using remote server: {response}"
            raise CardGenerationError(msg) from e

        response_json = response.json()
        cards = [TranslationCard.from_dict(card_dict) for card_dict in response_json]

        return cards


def create_card_generator(config: CardGeneratorConfig, url: Optional[str] = None):
    """Create a CardGenerator from the config."""
    if url is None:
        url = get_api_url()

    if url is None:
        card_generator = LLMTranslationCardGenerator.from_config(config)
    else:
        card_generator = RemoteCardGenerator(url=url, config=config)

    return lru_cache(maxsize=None)(card_generator)


CardGeneratorFactory = Callable[[CardGeneratorConfig], CardGenerator]


class CachedCardGeneratorFactory:
    """Create a CardGenerator from the config. Cache the result."""

    def __init__(self, context_id: int, card_generator_factory: CardGeneratorFactory):
        self.context_id = context_id
        self._call = lru_cache(maxsize=None)(card_generator_factory)

    def __call__(self, config: CardGeneratorConfig) -> CardGenerator:
        return self._call(config)


cached2_card_generator_factory = lru_cache(maxsize=1)(CachedCardGeneratorFactory)
