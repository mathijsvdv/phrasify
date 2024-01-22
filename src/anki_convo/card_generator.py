import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Dict, List

from .card import TextCard
from .chains.base import Chain
from .error import CardGenerationError, ChainError
from .factory import get_chain, get_llm_name, get_prompt
from .logging import get_logger

logger = get_logger(__name__)


CardGenerator = Callable[[str], List[TextCard]]


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

    return [
        TextCard(front=card_dict["front"], back=card_dict["back"])
        for card_dict in card_dicts
    ]


@dataclass(frozen=True)
class CardGeneratorConfig:
    """Configuration for the CardGenerator."""

    prompt_name: str
    lang_front: str
    lang_back: str


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
            f"Here is the prompt template:\n'''{self.prompt}'''\n"
            f"Prompt inputs are {self.prompt_inputs}"
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


def create_card_generator(config: CardGeneratorConfig):
    """Create a CardGenerator from the config."""
    llm_name = get_llm_name()
    prompt = get_prompt(config.prompt_name)
    chain = get_chain()

    prompt_inputs = {"n_cards": 1}
    prompt_inputs.update(
        {"lang_front": config.lang_front, "lang_back": config.lang_back}
    )

    card_generator = ChainCardGenerator(
        chain=chain, llm=llm_name, prompt=prompt, prompt_inputs=prompt_inputs
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
