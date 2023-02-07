import functools


class Pipeable:
    def __init__(self, wrapped):
        self._wrapped = [wrapped]

    def __or__(self, other) -> "Pipeable":
        if isinstance(other, Pipeable):
            self._wrapped.extend(other._wrapped)
            return self
        # TODO: check if other is a function or callable
        self._wrapped.append(other)
        return self

    def __call__(self, arg):
        return functools.reduce(lambda acc, func: func(acc), self._wrapped, arg)


@Pipeable
def foo(arg):
    print("foo() running")
    return "foo"


@Pipeable
def bar(arg):
    print("bar() running")
    return "bar"


(foo | bar)("xyz")
pass
