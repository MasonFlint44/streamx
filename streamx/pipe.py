import builtins
import functools
from typing import Any, Callable, Generic, TypeVar, cast

T_in = TypeVar("T_in")
T_out = TypeVar("T_out")
V_out = TypeVar("V_out")


class AsyncPipeline:
    def __init__(self, source=None):
        self.source = source

    def __or__(self, operator):
        if not self.source:
            return AsyncPipeline(operator)

        async def pipe(source):
            async for value in operator(source):
                yield value

        return AsyncPipeline(pipe(self.source))

    def __call__(self, func):
        return AsyncPipeline(func())

    async def __aiter__(self):
        if not self.source:
            raise ValueError("Cannot iterate over an empty pipeline - provide a source first")
        async for value in self.source:
            yield value


def filter(predicate):
    @functools.wraps(filter)
    async def _filter(source):
        async for value in source:
            if predicate(value):
                yield value

    return _filter


def range(start, stop=None, step=1):
    if stop is None:
        stop = start
        start = 0

    @functools.wraps(range)
    async def _range():
        for i in builtins.range(start, stop, step):
            yield i

    return _range()
