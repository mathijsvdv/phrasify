from dataclasses import dataclass
from typing import Any, Dict, List

from ..error import LLMError
from ..llms.base import LLM
from .base import Chain

LLMChainInput = Dict[str, Any]
LLMChainOutput = Dict[str, str]


@dataclass
class LLMChain(Chain[LLMChainInput, LLMChainOutput]):
    """Chain that uses an LLM together with a prompt template to generate a response."""

    llm: LLM
    prompt: str
    output_key: str = "text"

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    def _call(self, x: LLMChainInput, **kwargs: Any) -> LLMChainOutput:
        """Run the chain on the given input `x`."""
        prompt = self.prompt.format(**x)
        try:
            text = self.llm(prompt, **kwargs)
        except LLMError as e:
            self._raise(e)

        output = dict(inputs=x, **{self.output_key: text})
        return output
