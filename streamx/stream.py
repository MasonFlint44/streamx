import asyncio
from typing import Generic, TypeVar

T = TypeVar("T")


class AsyncStreamIterator(Generic[T]):
    def __init__(self, stream: "AsyncStream[T]") -> None:
        self._stream = stream
        self._ready = asyncio.Event()

    async def __anext__(self) -> T:
        # signal that iteration is ready for next value
        self._ready.set()
        # get next value from future
        result = await self._stream.future
        if result is StopAsyncIteration:
            raise StopAsyncIteration
        # set future for next iteration
        self._stream.set_future()
        # await current future and return result
        return result

    async def wait_for_ready(self) -> None:
        await self._ready.wait()
        self._ready.clear()


class AsyncStream(Generic[T]):
    def __init__(self) -> None:
        self._future = asyncio.Future()
        self._iterators = []

    @property
    def future(self) -> asyncio.Future:
        return self._future

    def set_future(self) -> None:
        if not self._future.done():
            return
        # set new future if current future is done
        self._future = asyncio.Future()

    async def __aenter__(self) -> "AsyncStream[T]":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # close stream on exit
        await self.close()

    def __aiter__(self) -> AsyncStreamIterator[T]:
        iterator = AsyncStreamIterator(self)
        self._iterators.append(iterator)
        return iterator

    async def put(self, value: T) -> None:
        # wait for all iterators to be ready for the next value
        await asyncio.gather(*[iterator.wait_for_ready() for iterator in self._iterators])
        self._future.set_result(value)

    async def close(self) -> None:
        await self.put(StopAsyncIteration)  # type: ignore
        self._iterators.clear()
