import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from typing import Generic, TypeVar

T = TypeVar("T")


class AsyncStream(AsyncIterator[T], Generic[T], AsyncIterable[T]):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[T] = asyncio.Queue()
        self._consuming_task: asyncio.Task | None = None

    async def push(self, item: T) -> None:
        current_task = asyncio.current_task()
        if self._consuming_task == current_task:
            raise ValueError("Can't push item while stream is being consumed by the same task")
        await self._queue.put(item)

    async def close(self) -> None:
        await self.push(StopAsyncIteration)  # type: ignore

    def __aiter__(self) -> "AsyncStream[T]":
        if self._consuming_task is not None:
            raise ValueError("Stream is already being consumed by another task.")
        self._consuming_task = asyncio.current_task()
        return self

    async def __anext__(self) -> T:
        item = await self._queue.get()
        if item is StopAsyncIteration:
            self._consuming_task = None
            raise StopAsyncIteration
        return item
