import asyncio
from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, Generic, TypeVar

TIn_contra = TypeVar("TIn_contra", contravariant=True)
TOut_co = TypeVar("TOut_co", covariant=True)


class Chain(ABC, Generic[TIn_contra, TOut_co], Callable[[TIn_contra], TOut_co]):
    """Base Chain abstract class.

    Adapted from langchain's Chain base class, but simplified to only expose the _call
    and _acall methods where the arguments are only the input and kwargs.
    """

    @abstractmethod
    def _call(
        self,
        x: TIn_contra,
        /,
        **kwargs: Any,
    ) -> TOut_co:
        """Run the chain on the given input `x`."""

    def __call__(
        self,
        x: TIn_contra,
        /,
        **kwargs: Any,
    ) -> TOut_co:
        """Run the chain on the given input `x`."""
        return self._call(x, **kwargs)

    async def _acall(
        self,
        x: TIn_contra,
        **kwargs: Any,
    ) -> TOut_co:
        """Run the LLM async on the given input `x`."""
        return await asyncio.get_running_loop().run_in_executor(
            None, partial(self._call, **kwargs), x
        )

    async def acall(
        self,
        x: TIn_contra,
        **kwargs: Any,
    ) -> TOut_co:
        """Run the LLM async on the given input `x`."""
        return await self._acall(x, **kwargs)
