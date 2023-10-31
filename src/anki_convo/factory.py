"""Collection of factory functions for creating objects from strings.

These functions are used to parse user input.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from .card import CardSide
from .config import config
from .llms.openai import OpenAI

__all__ = ["get_llm", "get_prompt", "get_card_side"]


def get_llm(llm_name: Optional[str] = None):
    """Get the LLM object for the given LLM name."""
    if llm_name is None:
        llm_name = config["llm"]

    if llm_name.startswith("gpt-"):
        return OpenAI(llm_name)
    else:
        msg = f"Invalid LLM name: {llm_name}"
        raise ValueError(msg)


prompt_folder = Path(__file__).parent / "user_files" / "prompts"


@lru_cache(maxsize=None)
def get_prompt(prompt_name: str):
    """Get the prompt text for the given prompt name."""
    prompt_path = prompt_folder / f"{prompt_name}.txt"
    with open(prompt_path) as f:
        prompt = f.read()
    return prompt


def get_card_side(side: str):
    """Get the CardSide from a string identifier."""
    return CardSide.from_str(side)
