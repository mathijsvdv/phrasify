import asyncio
import json
import re
from collections import deque
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, Iterator, List, Optional, Union

import aiofiles
import aiofiles.os as aos
import aiofiles.ospath
import requests

from .card import TranslationCard
from .chains.llm import LLMChain, LLMChainInput
from .constants import (
    DEFAULT_MIN_CARDS,
    DEFAULT_N_CARDS,
    DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
    GENERATED_CARDS_DIR,
)
from .error import CardGenerationError, ChainError, LLMParsingError
from .event_loop import run_coroutine_in_thread
from .factory import get_api_url, get_llm, get_llm_name, get_prompt, get_prompt_name
from .logging import get_logger

logger = get_logger(__name__)


CardGenerator = Callable[[TranslationCard], List[TranslationCard]]
CardFactory = Callable[[TranslationCard], TranslationCard]


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

    def to_path_friendly_str(self) -> str:
        """Turn into a string that can be used in a file path."""
        return (
            f"{self.llm}_{self.prompt_name}_"
            f"{self.source_language}_{self.target_language}"
        )


@dataclass
class LLMTranslationCardGenerator:
    """Can be called to generate translation cards from an input card inserted into a
    prompt."""

    chain: Callable[[LLMChainInput], str]
    n_cards: int
    source_language: str
    target_language: str

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

    def _get_chain_inputs(self, card: TranslationCard, n_cards: int) -> LLMChainInput:
        return {
            "n_cards": n_cards,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "card": card,
        }

    def _log_generating_cards(self, card: TranslationCard):
        """Log that we are generating cards for the given card."""
        logger.debug(
            f"{self.__class__.__name__} generating {self.n_cards} cards "
            f"from card {card!r}, using chain {self.chain}"
        )

    def _log_response_from_chain(self, response: str):
        logger.debug(f"Response from chain: {response}")

    def _parse_translation_card_response(self, response: str):
        try:
            cards = _parse_translation_card_response(response)
        except LLMParsingError as e:
            msg = f"Error parsing response from chain: {response}"
            raise CardGenerationError(msg) from e

        return cards

    def _raise_card_generation_error(self, error: ChainError, chain_inputs):
        msg = f"Error generating card using chain inputs: {chain_inputs}"
        raise CardGenerationError(msg) from error

    def __call__(
        self, card: TranslationCard, n_cards: Optional[int] = None
    ) -> List[TranslationCard]:
        """Generate multiple translation cards from an input card inserted into a
        prompt."""
        self._log_generating_cards(card)

        if n_cards is None:
            n_cards = self.n_cards

        if n_cards == 0:
            return []

        chain_inputs = self._get_chain_inputs(card, n_cards=n_cards)
        try:
            response = self.chain(chain_inputs)
        except ChainError as e:
            self._raise_card_generation_error(e, chain_inputs=chain_inputs)

        self._log_response_from_chain(response)
        cards = self._parse_translation_card_response(response)

        return cards

    async def acall(
        self, card: TranslationCard, n_cards: Optional[int] = None
    ) -> List[TranslationCard]:
        self._log_generating_cards(card)

        if n_cards is None:
            n_cards = self.n_cards

        if n_cards == 0:
            return []

        chain_inputs = self._get_chain_inputs(card, n_cards=n_cards)
        try:
            response = await self.chain.acall(chain_inputs)
        except ChainError as e:
            self._raise_card_generation_error(e, chain_inputs=chain_inputs)

        self._log_response_from_chain(response)
        cards = self._parse_translation_card_response(response)

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


class TranslationCardEncoder(json.JSONEncoder):
    """JSON encoder for TranslationCard objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, TranslationCard):
            return o.to_dict()
        return super().default(o)


@lru_cache(maxsize=None)
def get_file_lock(path: Path):  # noqa: ARG001
    """
    Get a lock for file operations.

    We want to get the same lock for the same path,
    hence the use of lru_cache with the `path` argument.
    """
    return asyncio.Lock()


@lru_cache(maxsize=None)
def get_file_tasks(path: Path):  # noqa: ARG001
    """
    Get a set of tasks for file operations.

    We want to get the same set for the same path,
    hence the use of lru_cache with the `path` argument.
    """
    return set()


@dataclass
class JSONCachedCardGenerator:
    """Can be called to generate language cards. Cache the result as a JSON."""

    card_generator: CardGenerator
    min_cards: int = DEFAULT_MIN_CARDS
    fast_n_cards: int = 1
    name: str = "default"

    def get_cache_path(self, card: TranslationCard) -> Path:
        """Get the path to the cache file."""
        return GENERATED_CARDS_DIR / f"{self.name}_{card.to_path_friendly_str()}.json"

    def clear_cache(self):
        """Clear the cache."""
        for path in GENERATED_CARDS_DIR.glob(f"{self.name}_*.json"):
            path.unlink()

    async def get_from_cache(self, card: TranslationCard) -> Deque[TranslationCard]:
        """Get the cards from the cache, if they exist."""
        cache_path = self.get_cache_path(card)
        try:
            async with aiofiles.open(cache_path) as f:
                content = await f.read()

            cards = json.loads(content, object_hook=TranslationCard.from_dict)

        except FileNotFoundError:
            cards = []

        return deque(cards)

    async def write_to_cache(
        self,
        card: TranslationCard,
        cards: Iterable[TranslationCard],
    ):
        """Write the cards to the cache.

        Parameters
        ----------
        card : TranslationCard
            The card that was used to generate the cards.
        cards: Iterable[TranslationCard]
            The cards to write to the cache.
        """
        cache_path = self.get_cache_path(card)
        await aos.makedirs(cache_path.parent, exist_ok=True)
        cards_json = json.dumps(list(cards), cls=TranslationCardEncoder)
        async with aiofiles.open(cache_path, "w") as f:
            await f.write(cards_json)

    async def extend_cache(
        self,
        card: TranslationCard,
        n_cards: Optional[int],
        cache_lock: asyncio.Lock,
    ):
        """Extend the cache with new cards."""
        new_cards = await self.card_generator.acall(card, n_cards=n_cards)
        async with cache_lock:
            cards = await self.get_from_cache(card)
            cards.extend(new_cards)
            await self.write_to_cache(card, cards)
        logger.debug(f"Extended cache with {len(new_cards)} new cards for card {card}")

    async def acall(self, card: TranslationCard) -> Iterator[TranslationCard]:
        """Generate language cards from the front text inserted into a prompt."""
        cache_path = self.get_cache_path(card)
        cache_lock = get_file_lock(cache_path)
        async with cache_lock:
            cards = await self.get_from_cache(card)
        logger.debug(f"Retrieved {len(cards)} cards from cache for card {card}")

        tasks = get_file_tasks(cache_path)
        while True:
            if len(cards) < self.min_cards and not tasks:
                logger.debug(
                    f"Cache has {len(cards)} < {self.min_cards} cards, "
                    f"generating more for card {card}"
                )
                get_n_cards = asyncio.create_task(
                    self.extend_cache(card, n_cards=None, cache_lock=cache_lock)
                )
                tasks.add(get_n_cards)
                get_n_cards.add_done_callback(tasks.discard)

            if len(cards) == 0:
                logger.debug("No more cards in cache, generating one card to be quick")
                get_1_card = asyncio.create_task(
                    self.extend_cache(
                        card, n_cards=self.fast_n_cards, cache_lock=cache_lock
                    )
                )
                tasks.add(get_1_card)
                get_1_card.add_done_callback(tasks.discard)

                # We're out of cards, so need to wait for one of the two tasks
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            async with cache_lock:
                cards = await self.get_from_cache(card)
                if not cards:
                    logger.warning(
                        f"Failed to generate cards. "
                        f"Stopping the generator for card {card}"
                    )
                    break

                new_card = cards.popleft()
                await self.write_to_cache(card, cards)

            yield new_card

    def __call__(self, card: TranslationCard) -> Iterator[TranslationCard]:
        """Generate language cards from the front text inserted into a prompt."""
        card_iterator = self.acall(card).__aiter__()
        while True:
            try:
                new_card = run_coroutine_in_thread(card_iterator.__anext__()).result()
            except StopAsyncIteration:
                break

            yield new_card


class NextCardFactory(CardFactory):
    """Can be called to take the next language card from a card generator."""

    def __init__(self, card_generator: CardGenerator):
        self.card_generator = card_generator
        self._card_iterator = None

    def __call__(self, card: TranslationCard) -> TranslationCard:
        """Take next language card from the cards generated from a card generator."""

        if self._card_iterator is None:
            try:
                self._card_iterator = iter(self.card_generator(card))
            except CardGenerationError as e:
                logger.error(f"Error in card generator: {e}")
                self._card_iterator = iter([])

        try:
            new_card = next(self._card_iterator)
        except StopIteration:
            logger.warning(
                f"No cards generated. Using input card {card} as placeholder."
            )
            new_card = card

        return new_card


def create_card_generator(config: CardGeneratorConfig, url: Optional[str] = None):
    """Create a CardGenerator from the config."""
    if url is None:
        url = get_api_url()

    if url is None:
        card_generator = LLMTranslationCardGenerator.from_config(config)
    else:
        card_generator = RemoteCardGenerator(url=url, config=config)

    return card_generator


def create_card_factory(config: CardGeneratorConfig) -> CardFactory:
    """Create a CardFactory from the config."""
    card_generator = create_card_generator(config)

    name = config.to_path_friendly_str()
    card_generator = JSONCachedCardGenerator(card_generator, name=name)
    card_factory = NextCardFactory(card_generator)
    card_factory = lru_cache(maxsize=None)(card_factory)
    return card_factory


CardGeneratorFactory = Callable[[CardGeneratorConfig], CardGenerator]
CardFactoryCreator = Callable[[CardGeneratorConfig], CardFactory]


class CachedCardFactoryCreator:
    """Create a CardGenerator from the config. Cache the result."""

    def __init__(self, context_id: int, card_factory_creator: CardFactoryCreator):
        self.context_id = context_id
        self._call = lru_cache(maxsize=None)(card_factory_creator)

    def __call__(self, config: CardGeneratorConfig) -> CardFactory:
        return self._call(config)


cached2_card_factory_creator = lru_cache(maxsize=1)(CachedCardFactoryCreator)
