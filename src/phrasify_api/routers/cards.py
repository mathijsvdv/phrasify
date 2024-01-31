from fastapi import APIRouter
from fastapi_versionizer import api_version
from pydantic import BaseModel, Field

from phrasify.card import TranslationCard as TranslationCardDataclass
from phrasify.card_gen import LLMTranslationCardGenerator
from phrasify.constants import (
    DEFAULT_N_CARDS,
    DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
)
from phrasify.factory import get_llm_name, get_prompt_name

router = APIRouter()


class TranslationCard(BaseModel):
    """Model for a translation card."""

    source: str = ""
    target: str = ""

    @classmethod
    def from_dataclass(cls, card: TranslationCardDataclass):
        return cls(source=card.source, target=card.target)

    def to_dataclass(self) -> TranslationCardDataclass:
        return TranslationCardDataclass(source=self.source, target=self.target)

    def __hash__(self):
        return hash(self.source) ^ hash(self.target)


class CardGeneratorConfig(BaseModel):
    """Model for a CardGenerator configuration."""

    prompt_name: str = Field(default_factory=get_prompt_name)
    llm: str = Field(default_factory=get_llm_name)
    n_cards: int = Field(default=DEFAULT_N_CARDS, ge=1)
    source_language: str = DEFAULT_SOURCE_LANGUAGE
    target_language: str = DEFAULT_TARGET_LANGUAGE


class CardGenerationRequest(BaseModel):
    """Request model for generating Anki cards."""

    card_generator: CardGeneratorConfig = Field(default_factory=CardGeneratorConfig)
    card: TranslationCard = Field(default_factory=TranslationCard)


@api_version(1)
@router.post("/", summary="Generate Anki cards from a prompt and input card.")
def generate_cards(request: CardGenerationRequest) -> list[TranslationCard]:
    generator = LLMTranslationCardGenerator.from_config(request.card_generator)
    cards = generator(request.card.to_dataclass())
    return cards
