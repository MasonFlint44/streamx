import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Generic, TypeVar

T = TypeVar("T")


class SharedEventListener(Generic[T]):
    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._waiter: asyncio.Future[T] = self._loop.create_future()
        self._ready = asyncio.Event()

    @property
    def ready(self) -> asyncio.Event:
        return self._ready

    def push(self, value: T) -> None:
        self._waiter.set_result(value)

    async def wait(self) -> T:
        try:
            self._ready.set()
            return await self._waiter
        finally:
            self._ready.clear()
            self._waiter = self._loop.create_future()


class SharedEvent(Generic[T]):
    def __init__(self, loop: asyncio.AbstractEventLoop | None = None):
        self.loop = loop or asyncio.get_event_loop()
        self._listeners: set[SharedEventListener[T]] = set()

    @contextmanager
    def listen(self) -> Iterator[SharedEventListener[T]]:
        listener = None
        try:
            listener = SharedEventListener(self.loop)
            self._listeners.add(listener)
            yield listener
        finally:
            if listener:
                self._listeners.remove(listener)

    async def share(self, coro: ...) -> T:
        value: T = await coro
        await asyncio.gather(*[listener.ready.wait() for listener in self._listeners])
        for listener in self._listeners:
            listener.push(value)
        return value
