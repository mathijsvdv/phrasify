from dataclasses import dataclass
from typing import Any, Coroutine, Dict

from ..error import LLMError
from ..llms.base import LLM
from .base import Chain

LLMChainInput = Dict[str, Any]


@dataclass
class LLMChain(Chain[LLMChainInput, str]):
    """Chain that uses an LLM together with a prompt template to generate a response."""

    llm: LLM
    prompt: str

    def _call(self, x: LLMChainInput, **kwargs: Any) -> str:
        """Run the chain on the given input `x`."""
        prompt = self.prompt.format(**x)
        try:
            text = self.llm(prompt, **kwargs)
        except LLMError as e:
            self._raise(e)

        return text

    async def _acall(
        self, x: Dict[str, Any], **kwargs: Any
    ) -> Coroutine[Any, Any, str]:
        """Run the chain on the given input `x`"""
        prompt = self.prompt.format(**x)
        try:
            text = await self.llm.acall(prompt, **kwargs)
        except LLMError as e:
            self._raise(e)

        return text
