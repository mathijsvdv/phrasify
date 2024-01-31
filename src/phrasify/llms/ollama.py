from dataclasses import dataclass, field
from typing import Any, Optional

import requests

from ..ollama import get_ollama_url
from .base import LLM


@dataclass
class Ollama(LLM):
    """LLM that uses OpenAI's API."""

    model: str = "mistral"
    url: str = field(default_factory=get_ollama_url)
    format: Optional[str] = None

    @property
    def endpoint(self) -> str:
        return f"{self.url}/api/generate"

    def _call(self, prompt: str, **kwargs: Any) -> str:  # noqa: ARG002
        """Run the LLM on the given prompt and input."""
        data = {"prompt": prompt, "model": self.model, "stream": False}
        if self.format is not None:
            data["format"] = self.format

        try:
            response = requests.post(self.endpoint, json=data, timeout=300)
        except requests.ReadTimeout as e:
            self._raise(e)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._raise(e)

        response_str = response.json()["response"]
        return response_str
