from dataclasses import dataclass
from typing import Any, Dict

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
        return self.llm(prompt, **kwargs)
