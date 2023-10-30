import asyncio
from abc import ABC, abstractmethod
from functools import partial
from typing import Any


class LLM(ABC):
    """Base LLM abstract class.

    Adapted from langchain's LLM base class, but simplified to only expose the _call and _acall methods
    where the arguments are only the prompt and kwargs.
    """

    @abstractmethod
    def _call(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Run the LLM on the given prompt and input."""

    def __call__(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Run the LLM on the given prompt and input."""
        return self._call(prompt, **kwargs)

    async def _acall(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Run the LLM on the given prompt and input."""
        return await asyncio.get_running_loop().run_in_executor(None, partial(self._call, **kwargs), prompt)
