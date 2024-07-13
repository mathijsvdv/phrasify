import asyncio
from dataclasses import dataclass, field
from typing import Any, Coroutine

import aiohttp
import requests

from ..openai import OPENAI_CHAT_COMPLETIONS_URL, get_openai_api_key
from .base import LLM


def _completion_to_content(completion: dict):
    return completion["choices"][0]["message"]["content"]


@dataclass
class OpenAI(LLM):
    """LLM that uses OpenAI's API."""

    model: str = "gpt-3.5-turbo"
    api_key: str = field(repr=False, compare=False, default_factory=get_openai_api_key)

    def _get_request_input(self, prompt: str):
        """Get the request input for the API call."""
        url = OPENAI_CHAT_COMPLETIONS_URL
        messages = [{"role": "user", "content": prompt}]
        json = {"model": self.model, "messages": messages}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        return url, json, headers

    def _call(self, prompt: str, **kwargs: Any) -> str:  # noqa: ARG002
        """Run the LLM on the given prompt and input."""
        url, json, headers = self._get_request_input(prompt)

        try:
            response = requests.post(url, json=json, headers=headers, timeout=30)
        except requests.ReadTimeout as e:
            self._raise(e)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._raise(e)

        completion = response.json()
        content = _completion_to_content(completion)
        return content

    async def _acall(
        self, prompt: str, **kwargs: Any  # noqa: ARG002
    ) -> Coroutine[Any, Any, str]:
        """Run the LLM on the given prompt and input."""
        url, json, headers = self._get_request_input(prompt)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, json=json, headers=headers, timeout=30
                ) as response:
                    response.raise_for_status()
                    completion = await response.json()
                    content = _completion_to_content(completion)
                    return content
            except asyncio.TimeoutError as e:
                self._raise(e)
            except aiohttp.ClientResponseError as e:
                self._raise(e)
