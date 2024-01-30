from dataclasses import dataclass, field
from typing import Any

import requests

from ..openai import OPENAI_CHAT_COMPLETIONS_URL, get_openai_api_key
from .base import LLM


@dataclass
class OpenAI(LLM):
    """LLM that uses OpenAI's API."""

    model: str = "gpt-3.5-turbo"
    api_key: str = field(repr=False, compare=False, default_factory=get_openai_api_key)

    def _call(self, prompt: str, **kwargs: Any) -> str:  # noqa: ARG002
        """Run the LLM on the given prompt and input."""
        url = OPENAI_CHAT_COMPLETIONS_URL
        messages = [{"role": "user", "content": prompt}]
        json = {"model": self.model, "messages": messages}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = requests.post(url, json=json, headers=headers, timeout=30)
        except requests.ReadTimeout as e:
            self._raise(e)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._raise(e)

        completion = response.json()
        content = completion["choices"][0]["message"]["content"]
        return content
