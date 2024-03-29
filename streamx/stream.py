import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from contextlib import contextmanager
from typing import Generic, Iterator, TypeVar

from . import (
    SharedEvent,
    SharedEventListener,
    StreamClosedError,
    StreamShortCircuitError,
)

T = TypeVar("T")

# TODO: push_many()?
# TODO: push_nowait()?

# TODO: Could we pull the ShortCircuit logic out into a StreamManager class or something to optimize the common case?


class AsyncStreamIterator(AsyncIterator[T], Generic[T], AsyncIterable[T]):
    def __init__(self, event_listener: SharedEventListener[T]) -> None:
        self._event_listener = event_listener

    async def __anext__(self) -> T:
        item = await self._event_listener.wait()
        if item is StopAsyncIteration:
            raise item  # type: ignore
        return item


class AsyncStreamListener(Generic[T]):
    def __init__(self, event_listener: SharedEventListener[T]) -> None:
        self._event_listener = event_listener
        self._current_task = asyncio.current_task()
        self._closed = False

    @property
    def current_task(self) -> asyncio.Task | None:
        return self._current_task

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True

    def __aiter__(self) -> AsyncStreamIterator[T]:
        if self._closed:
            raise StreamClosedError("Can't iterate over a closed stream.")
        return AsyncStreamIterator(self._event_listener)


# TODO: should this queue up items if no one is listening?
class AsyncStream(Generic[T]):
    def __init__(self) -> None:
        self._consuming_tasks: list[asyncio.Task] = []
        self._closed: bool = False
        self._event = SharedEvent[T]()
        self._listeners = set[AsyncStreamListener[T]]()

    @property
    def listeners(self) -> set[AsyncStreamListener[T]]:
        return self._listeners

    @property
    def closed(self) -> bool:
        return self._closed

    async def push(self, item: T) -> None:
        if self._closed:
            raise StreamClosedError("Can't push item into a closed stream.")
        if self._is_current_task_consuming():
            raise StreamShortCircuitError(
                "Can't push an item while the task is listening to this stream."
            )
        await self._event.share(item)

    async def close(self) -> None:
        if self._closed:
            return
        try:
            await self.push(StopAsyncIteration)  # type: ignore
        except StreamShortCircuitError as e:
            raise StreamShortCircuitError(
                "Can't close a stream from a task that is listening to it."
            ) from e
        self._closed = True
        for listener in self._listeners:
            listener.close()

    @contextmanager
    def listen(self) -> Iterator[AsyncStreamListener[T]]:
        if self._closed:
            raise StreamClosedError("Can't listen to a closed stream.")
        if self._is_current_task_consuming():
            raise StreamShortCircuitError("Task is already listening to this stream.")

        listener = None
        try:
            with self._event.listen() as event_listener:
                listener = AsyncStreamListener(event_listener)
                self._add_listener(listener)
                yield listener
        finally:
            if listener:
                listener.close()
                self._remove_listener(listener)

    def _add_listener(self, listener: AsyncStreamListener[T]) -> None:
        self._listeners.add(listener)
        if listener.current_task:
            self._consuming_tasks.append(listener.current_task)

    def _remove_listener(self, listener: AsyncStreamListener[T]) -> None:
        self._listeners.remove(listener)
        if listener.current_task:
            self._consuming_tasks.remove(listener.current_task)

    def _is_current_task_consuming(self) -> bool:
        return asyncio.current_task() in self._consuming_tasks
