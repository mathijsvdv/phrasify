"""Collection of factory functions for creating objects from strings.

These functions are used to parse user input.
"""

from functools import lru_cache
from typing import Optional

from .config import config
from .constants import PROMPT_DIR
from .llms.openai import OpenAI

__all__ = ["get_llm", "get_prompt"]


def get_llm_name(llm_name: Optional[str] = None):
    """Get the LLM name. If none is given, use the default from the config."""
    if llm_name is None:
        llm_name = config["llm"]

    return llm_name


def get_llm(llm_name: Optional[str] = None):
    """Get the LLM object for the given LLM name."""
    llm_name = get_llm_name(llm_name)

    if llm_name.startswith("gpt-"):
        return OpenAI(llm_name)
    else:
        msg = f"Invalid LLM name: {llm_name}"
        raise ValueError(msg)


def get_prompt_name(prompt_name: Optional[str] = None):
    """Get the prompt name. If none is given, use the default from the config."""
    if prompt_name is None:
        prompt_name = config["promptName"]

    return prompt_name


@lru_cache(maxsize=None)
def get_prompt(prompt_name: Optional[str] = None):
    """Get the prompt text for the given prompt name."""
    prompt_name = get_prompt_name(prompt_name)
    prompt_path = PROMPT_DIR / f"{prompt_name}.txt"
    with open(prompt_path) as f:
        prompt = f.read()
    return prompt


def get_api_location(api_location: Optional[str] = None):
    """Get the API location. If none is given, use the default from the config."""
    if api_location is None:
        api_location = config.get("apiLocation", None)

    return api_location


def get_api_url(api_location: Optional[str] = None):
    """Get the Cards API URL for the given API location."""
    api_location = get_api_location(api_location)

    if api_location is None:
        return None

    if api_location == "local":
        return "http://localhost:8800/v1/cards"

    if api_location == "remote":
        return "https://phrasify.mvdvlies.com/api/v1/cards"

    message = f"Invalid API location: {api_location!r}"
    raise ValueError(message)
