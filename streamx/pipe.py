import builtins
import functools
from collections.abc import AsyncIterator, Callable
from typing import Generic, TypeVar, cast

T = TypeVar("T")
V = TypeVar("V")


class AsyncPipeline(Generic[T]):
    def __init__(self, source: AsyncIterator[T] | None = None) -> None:
        self.source = source

    def __or__(
        self, operator: Callable[[AsyncIterator[T]], AsyncIterator[V]] | AsyncIterator[V]
    ) -> "AsyncPipeline[V]":
        if not self.source:
            # set the source
            if not isinstance(operator, AsyncIterator):
                raise ValueError(
                    "Cannot set the source of a pipeline to anything but an AsyncIterator"
                )
            return AsyncPipeline(operator)

        async def pipe(source: AsyncIterator[T]) -> AsyncIterator[V]:
            if not isinstance(operator, Callable):
                raise ValueError("Cannot pipe to anything but a Callable")

            async for value in operator(source):
                yield value

        return AsyncPipeline(pipe(self.source))

    async def __aiter__(self) -> AsyncIterator[T]:
        if not self.source:
            raise ValueError("Cannot iterate over an empty pipeline - provide a source first")
        async for value in self.source:
            yield value


def filter(predicate: Callable[[T], bool]) -> Callable[[AsyncIterator[T]], AsyncIterator[T]]:
    @functools.wraps(filter)
    async def _filter(source: AsyncIterator[T]) -> AsyncIterator[T]:
        async for value in source:
            if predicate(value):
                yield value

    return _filter


def range(stop: int, *, start=0, step=1) -> AsyncIterator[int]:
    @functools.wraps(range)
    async def _range() -> AsyncIterator[int]:
        for i in builtins.range(start, stop, step):
            yield i

    return _range()
