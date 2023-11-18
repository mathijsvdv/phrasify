import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains import LLMChain
from langchain.chains.base import Chain
from langchain.chat_models.ollama import ChatOllama
from langchain.chat_models.openai import ChatOpenAI
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langserve import add_routes


def get_llm(llm_name: str) -> LLM:
    if llm_name.startswith("gpt-"):
        return ChatOpenAI(model=llm_name)
    elif llm_name.startswith("ollama-"):
        ollama_re = re.compile(r"ollama-(?P<ollama_name>.*)")
        ollama_name = ollama_re.match(llm_name).group("ollama_name")
        return ChatOllama(model=ollama_name)
    else:
        msg = f"Invalid LLM name: {llm_name}"
        raise ValueError(msg)


class LLMInputChain(Chain):
    """
    Chain where the name of the underlying LLM is provided in the input
    """

    output_key: str = "result"

    class Config:
        """Configuration for this pydantic object."""

        extra = "forbid"
        arbitrary_types_allowed = True

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

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        llm = get_llm(inputs["llm"])
        prompt = PromptTemplate.from_template(inputs["prompt"])
        prompt_inputs = inputs["prompt_inputs"]
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain(prompt_inputs)

        # If you want to log something about this run, you can do so by calling
        # methods on the `run_manager`, as shown below. This will trigger any
        # callbacks that are registered for that event.
        if run_manager:
            run_manager.on_text("Log something about this run")

        return {self.output_key: result}

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        llm = get_llm(inputs["llm"])
        prompt = PromptTemplate.from_template(inputs["prompt"])
        prompt_inputs = inputs["prompt_inputs"]
        chain = LLMChain(llm=llm, prompt=prompt)
        result = await chain.acall(prompt_inputs)

        # If you want to log something about this run, you can do so by calling
        # methods on the `run_manager`, as shown below. This will trigger any
        # callbacks that are registered for that event.
        if run_manager:
            await run_manager.on_text("Log something about this run")

        return {self.output_key: result}

    @property
    def _chain_type(self) -> str:
        return "llm_input_chain"


app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A server for running the LLMInputChain",
)

add_routes(
    app,
    LLMInputChain(),
    path="/chain",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8800)
