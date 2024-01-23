import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Dict, List

from .card import TranslationCard
from .chains.llm import LLMChain, LLMChainInput
from .error import CardGenerationError, ChainError
from .factory import get_llm, get_llm_name, get_prompt
from .logging import get_logger

logger = get_logger(__name__)


CardGenerator = Callable[[TranslationCard], List[TranslationCard]]


def parse_text_card_response(response: Dict[str, str]) -> List[TranslationCard]:
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
    response = response["text"]
    card_dicts = json.loads(response)

    return [TranslationCard(**card_dict) for card_dict in card_dicts]


DEFAULT_N_CARDS = 1
DEFAULT_SOURCE_LANGUAGE = "English"
DEFAULT_TARGET_LANGUAGE = "Ukrainian"


@dataclass(frozen=True)
class CardGeneratorConfig:
    """Configuration for the CardGenerator."""

    prompt_name: str
    llm: str = field(default_factory=get_llm_name)
    n_cards: int = DEFAULT_N_CARDS
    source_language: str = DEFAULT_SOURCE_LANGUAGE
    target_language: str = DEFAULT_TARGET_LANGUAGE


@dataclass
class LLMLanguageCardGenerator(CardGenerator):
    """Can be called to generate language cards from an input card inserted into a
    prompt."""

    chain: LLMChain
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

    def __call__(self, card: TranslationCard) -> List[TranslationCard]:
        """Generate multiple language cards from an input card inserted into a
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
            cards = parse_text_card_response(response)
        except json.JSONDecodeError as e:
            msg = f"Error parsing response from chain: {response}"
            raise CardGenerationError(msg) from e

        return cards


def create_card_generator(config: CardGeneratorConfig):
    """Create a CardGenerator from the config."""
    llm = get_llm(config.llm)
    prompt = get_prompt(config.prompt_name)
    chain = LLMChain(llm=llm, prompt=prompt)
    card_generator = LLMLanguageCardGenerator(
        chain=chain,
        n_cards=config.n_cards,
        source_language=config.source_language,
        target_language=config.target_language,
    )

    return lru_cache(maxsize=None)(card_generator)


CardGeneratorFactory = Callable[[CardGeneratorConfig], CardGenerator]


class CachedCardGeneratorFactory:
    """Create a CardGenerator from the config. Cache the result."""

    def __init__(self, context_id: int):
        self.context_id = context_id
        self._call = lru_cache(maxsize=None)(create_card_generator)

    def __call__(self, config: CardGeneratorConfig) -> CardGenerator:
        return self._call(config)


cached2_card_generator_factory = lru_cache(maxsize=1)(CachedCardGeneratorFactory)
