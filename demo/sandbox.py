import functools
from typing import Any, Callable, Generic, TypeVar

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
            return self  # type: ignore
        # TODO: check if other is a function or callable
        self._wrapped.append(other)
        return self  # type: ignore

    def __call__(self, arg: T_in) -> T_out:
        return functools.reduce(lambda acc, func: func(acc), self._wrapped, arg)  # type: ignore


@Pipeable
def foo(arg: str) -> int:
    print("foo() running")
    return 123


@Pipeable
def bar(arg: int) -> float:
    print("bar() running")
    return 0.123


result = (foo | bar)("xyz")
pass
