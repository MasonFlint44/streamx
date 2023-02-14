import builtins
import functools
from collections.abc import AsyncIterator, Callable
from typing import Generic, TypeVar, cast

T = TypeVar("T")
V = TypeVar("V")


class AsyncPipeline(Generic[T]):
    def __init__(self, source: AsyncIterator[T]) -> None:
        if not isinstance(source, AsyncIterator):
            raise ValueError("`source` must be an AsyncIterator")
        self.source = source

    def __or__(
        self, operator: Callable[[AsyncIterator[T]], AsyncIterator[V]]
    ) -> "AsyncPipeline[V]":
        async def pipe(source: AsyncIterator[T]) -> AsyncIterator[V]:
            if not isinstance(operator, Callable):
                raise ValueError(
                    "Piped operators must be a Callable that accepts an AsyncIterator"
                )
            async for value in operator(source):
                yield value

        return AsyncPipeline(pipe(self.source))

    async def __aiter__(self) -> AsyncIterator[T]:
        async for value in self.source:
            yield value


def filter(predicate: Callable[[T], bool]) -> Callable[[AsyncIterator[T]], AsyncIterator[T]]:
    @functools.wraps(filter)
    async def _filter(source: AsyncIterator[T]) -> AsyncIterator[T]:
        async for value in source:
            if predicate(value):
                yield value

    return _filter


def range(stop: int, *, start=0, step=1) -> AsyncPipeline[int]:
    @functools.wraps(range)
    async def _range() -> AsyncIterator[int]:
        for i in builtins.range(start, stop, step):
            yield i

    return AsyncPipeline(_range())
