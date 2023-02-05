import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from typing import ContextManager, Generic, TypeVar

from . import StreamClosedError, StreamConsumerError, StreamShortCircuitError
from .event import SharedEvent, SharedEventListener

T = TypeVar("T")

# TODO: push_many()?
# TODO: push_nowait()?


class AsyncStreamIterator(AsyncIterator[T], Generic[T], AsyncIterable[T]):
    def __init__(self, listener_context: ContextManager[SharedEventListener[T]]) -> None:
        self._listener_context = listener_context
        self._event_listener = listener_context.__enter__()

    async def __anext__(self) -> T:
        item = await self._event_listener.wait()
        if item is StopAsyncIteration:
            raise StopAsyncIteration
        return item

    def close(self) -> None:
        self._listener_context.__exit__(None, None, None)


# TODO: should this queue up items if no one is listening?
class AsyncStream(Generic[T]):
    def __init__(self) -> None:
        self._consuming_tasks: list[asyncio.Task] = []
        self._closed: bool = False
        self._event = SharedEvent[T]()

    async def push(self, item: T) -> None:
        if self._closed:
            raise StreamClosedError("Can't push item into a closed stream.")
        current_task = asyncio.current_task()
        if current_task in self._consuming_tasks:
            raise StreamShortCircuitError(
                "Can't push item while stream is being consumed by the same task"
            )
        await self._event.share(asyncio.sleep(0, result=item))

    async def close(self) -> None:
        if self._closed:
            return
        await self.push(StopAsyncIteration)  # type: ignore
        self._closed = True

    def __aiter__(self) -> AsyncStreamIterator[T]:
        if self._closed:
            raise StreamClosedError("Can't iterate over a closed stream.")
        iterator = AsyncStreamIterator(self._event.listen())
        current_task = asyncio.current_task()
        if current_task:
            self._consuming_tasks.append(current_task)
            # TODO: is there a better way to track when listeners exit the async for loop?
            # - this doesn't really really track when the loop exits, just when the task is done
            # - context manager could be used, but I'd rather not have to futher nest all of the consumer code
            current_task.add_done_callback(lambda _: iterator.close())
        return iterator
