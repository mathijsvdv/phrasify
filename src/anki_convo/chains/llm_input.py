from dataclasses import dataclass
from typing import Any, Dict, List, Union

from .base import Chain
from .llm import LLMChain, LLMChainInput, LLMChainOutput

LLMInputChainInput = Dict[str, Union[str, LLMChainInput]]
LLMInputChainOutput = Dict[str, LLMChainOutput]


@dataclass
class LLMInputChain(Chain):
    """
    Chain where the name of the underlying LLM is provided in the input
    """

    output_key: str = "result"

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return ["llm", "prompt", "prompt_inputs"]

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(self, x: LLMInputChainInput, **kwargs: Any) -> LLMInputChainOutput:
        from ..factory import get_llm

        llm = get_llm(x["llm"])
        prompt = x["prompt"]
        prompt_inputs = x["prompt_inputs"]
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain(prompt_inputs, **kwargs)

        return {self.output_key: result}

    async def _acall(self, x: LLMInputChainInput, **kwargs: Any) -> LLMInputChainOutput:
        from ..factory import get_llm

        llm = get_llm(x["llm"])
        prompt = x["prompt"]
        prompt_inputs = x["prompt_inputs"]
        chain = LLMChain(llm=llm, prompt=prompt)
        result = await chain.acall(prompt_inputs, **kwargs)

        return {self.output_key: result}
