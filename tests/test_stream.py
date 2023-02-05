import asyncio
import time

import pytest

from streamz import AsyncStream, StreamClosedError, StreamShortCircuitError


@pytest.mark.asyncio
async def test_push_and_consume():
    stream = AsyncStream[int]()

    async def producer():
        try:
            for i in range(10):
                await stream.push(i)
        finally:
            await stream.close()

    async def consumer():
        items = []
        with stream.listen() as listener:
            async for item in listener:
                items.append(item)
        return items

    _, items = await asyncio.gather(producer(), consumer())
    assert items == list(range(10))


@pytest.mark.asyncio
async def test_push_from_same_task_inside_async_for_loop_raises_error():
    stream = AsyncStream[int]()
    await stream.push(123)

    async def consumer():
        with stream.listen() as listener:
            async for _ in listener:
                with pytest.raises(StreamShortCircuitError):
                    await stream.push(456)

    await asyncio.gather(consumer(), stream.close())


@pytest.mark.asyncio
async def test_push_after_close_raises_error():
    stream = AsyncStream[int]()
    await stream.close()

    with pytest.raises(StreamClosedError):
        await stream.push(123)


@pytest.mark.asyncio
async def test_iterate_after_close_raises_error():
    stream = AsyncStream[int]()
    await stream.close()

    with pytest.raises(StreamClosedError):
        with stream.listen() as listener:
            async for _ in listener:
                pass


@pytest.mark.asyncio
async def test_backpressure():
    stream = AsyncStream()
    item_count = 10
    consumed_count = 0
    fast_consumer_duration = 0.1
    slow_consumer_duration = fast_consumer_duration * 2

    async def producer():
        try:
            start_time = time.perf_counter()
            for i in range(item_count):
                await stream.push(i)
            end_time = time.perf_counter()
            return end_time - start_time
        finally:
            asyncio.create_task(stream.close())

    async def fast_consumer():
        nonlocal consumed_count
        with stream.listen() as listener:
            async for _ in listener:
                consumed_count += 1
                await asyncio.sleep(fast_consumer_duration)

    async def slow_consumer():
        nonlocal consumed_count
        with stream.listen() as listener:
            async for _ in listener:
                consumed_count += 1
                await asyncio.sleep(slow_consumer_duration)

    producer_duration, _, _ = await asyncio.gather(
        producer(),
        fast_consumer(),
        slow_consumer(),
    )
    # ensure both consumers have consumed all items
    assert consumed_count == item_count * 2
    assert producer_duration >= (item_count - 1) * slow_consumer_duration
    assert producer_duration < item_count * slow_consumer_duration
