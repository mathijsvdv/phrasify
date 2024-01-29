from dataclasses import dataclass
from typing import Any

import requests

from .base import LLM


@dataclass
class Ollama(LLM):
    """LLM that uses OpenAI's API."""

    model: str = "mistral"
    url: str = "http://localhost:11434"

    @property
    def endpoint(self) -> str:
        return f"{self.url}/api/generate"

    def _call(self, prompt: str, **kwargs: Any) -> str:  # noqa: ARG002
        """Run the LLM on the given prompt and input."""
        data = {"prompt": prompt, "model": self.model, "stream": False}

        response = requests.post(self.endpoint, json=data, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._raise(e)

        response_str = response.json()["response"]
        return response_str
