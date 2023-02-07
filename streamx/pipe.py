import functools
from typing import Any, Callable, Generic, TypeVar, cast

T_in = TypeVar("T_in")
T_out = TypeVar("T_out")
V_out = TypeVar("V_out")


class Pipeable(Generic[T_in, T_out]):
    def __init__(self, wrapped: Callable[[T_in], T_out]) -> None:
        self._wrapped: list[Callable[[Any], Any]] = [wrapped]

    def __or__(
        self, other: Callable[[T_out], V_out] | "Pipeable[T_out, V_out]"
    ) -> "Pipeable[T_in, V_out]":
        if isinstance(other, Pipeable):
            self._wrapped.extend(other._wrapped)
            return cast("Pipeable[T_in, V_out]", self)
        # TODO: check if other is a function or callable
        self._wrapped.append(other)
        return cast("Pipeable[T_in, V_out]", self)

    def __call__(self, arg: T_in) -> T_out:
        return cast(T_out, functools.reduce(lambda acc, func: func(acc), self._wrapped, arg))


def filter(filter):
    async def _filter(stream):
        async for item in stream:
            if filter(item):
                yield item

    return _filter
