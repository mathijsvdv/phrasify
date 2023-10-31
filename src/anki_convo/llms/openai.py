from dataclasses import dataclass
from typing import Any

import openai

from .base import LLM


@dataclass
class OpenAI(LLM):
    """LLM that uses OpenAI's API."""

    model: str = "gpt-3.5-turbo"

    def _call(self, prompt: str, **kwargs: Any) -> str:
        """Run the LLM on the given prompt and input."""
        messages = [{"role": "user", "content": prompt}]
        completion = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return completion.choices[0].message.content
