import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from typing import Generic, TypeVar

from . import StreamClosedError, StreamConsumerError, StreamShortCircuitError

T = TypeVar("T")

# TODO: push_many()?
# TODO: push_nowait()?


class AsyncStream(AsyncIterator[T], Generic[T], AsyncIterable[T]):
    def __init__(self, backpressure: bool = True, buffer_size=1) -> None:
        # TODO: can we swap out the queue with a future?
        self._queue: asyncio.Queue[T] = asyncio.Queue(maxsize=buffer_size if backpressure else 0)
        self._consuming_task: asyncio.Task | None = None
        self._closed: bool = False

    async def push(self, item: T) -> None:
        if self._closed:
            raise StreamClosedError("Can't push item into a closed stream.")
        current_task = asyncio.current_task()
        if self._consuming_task == current_task:
            raise StreamShortCircuitError(
                "Can't push item while stream is being consumed by the same task"
            )
        await self._queue.put(item)

    async def close(self) -> None:
        if self._closed:
            return
        await self.push(StopAsyncIteration)  # type: ignore
        self._closed = True

    def __aiter__(self) -> "AsyncStream[T]":
        if self._closed:
            raise StreamClosedError("Can't iterate over a closed stream.")
        if self._consuming_task is not None:
            raise StreamConsumerError("Stream is already being consumed by another task.")
        self._consuming_task = asyncio.current_task()
        return self

    async def __anext__(self) -> T:
        try:
            item = await self._queue.get()
            if item is StopAsyncIteration:
                self._consuming_task = None
                raise StopAsyncIteration
            return item
        finally:
            self._queue.task_done()
