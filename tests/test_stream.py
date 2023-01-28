import asyncio
import time

import pytest

from streamz import AsyncStream, StreamClosedError, StreamConsumerError, StreamShortCircuitError


@pytest.mark.asyncio
async def test_push_and_consume():
    stream: AsyncStream[int] = AsyncStream()

    async def producer():
        try:
            for i in range(10):
                await stream.push(i)
        finally:
            await stream.close()

    async def consumer():
        items = []
        async for item in stream:
            items.append(item)
        return items

    _, items = await asyncio.gather(producer(), consumer())
    assert items == list(range(10))


@pytest.mark.asyncio
async def test_push_from_same_task_outside_async_for_loop_works():
    stream: AsyncStream[int] = AsyncStream()

    async def consumer():
        await stream.push(123)

        items = []
        async for item in stream:
            items.append(item)
        return items

    items, _ = await asyncio.gather(consumer(), stream.close())
    assert 123 in items


@pytest.mark.asyncio
async def test_push_from_same_task_inside_async_for_loop_raises_error():
    stream: AsyncStream[int] = AsyncStream()
    await stream.push(123)

    async def consumer():
        async for _ in stream:
            with pytest.raises(StreamShortCircuitError):
                await stream.push(456)

    await asyncio.gather(consumer(), stream.close())


@pytest.mark.asyncio
async def test_push_after_close_raises_error():
    stream: AsyncStream[int] = AsyncStream()
    await stream.close()

    with pytest.raises(StreamClosedError):
        await stream.push(123)


@pytest.mark.asyncio
async def test_iterate_after_close_raises_error():
    stream: AsyncStream[int] = AsyncStream()
    await stream.close()

    with pytest.raises(StreamClosedError):
        async for _ in stream:
            pass


@pytest.mark.asyncio
async def test_multiple_consumers_raises_error():
    stream = AsyncStream()

    async def consumer1():
        async for _ in stream:
            pass

    async def consumer2():
        with pytest.raises(StreamConsumerError):
            async for _ in stream:
                pass

    await asyncio.gather(consumer1(), consumer2(), stream.close())


@pytest.mark.asyncio
async def test_backpressure():
    stream = AsyncStream(backpressure=True)

    async def producer():
        try:
            start_time = time.perf_counter_ns()
            for i in range(10):
                await stream.push(i)
            end_time = time.perf_counter_ns()
            return (end_time - start_time) / 1_000_000_000
        finally:
            asyncio.create_task(stream.close())

    async def consumer():
        async for _ in stream:
            await asyncio.sleep(0.1)

    producer_duration, _ = await asyncio.gather(
        producer(),
        consumer(),
    )
    assert producer_duration >= 0.8
    assert producer_duration < 0.9


@pytest.mark.asyncio
async def test_backpressure_can_be_disabled():
    stream = AsyncStream(backpressure=False)

    async def producer():
        try:
            start_time = time.perf_counter_ns()
            for i in range(10):
                await stream.push(i)
            end_time = time.perf_counter_ns()
            return (end_time - start_time) / 1_000_000_000
        finally:
            asyncio.create_task(stream.close())

    async def consumer():
        async for _ in stream:
            await asyncio.sleep(0.1)

    producer_duration, _ = await asyncio.gather(
        producer(),
        consumer(),
    )
    assert producer_duration < 0.1


@pytest.mark.asyncio
async def test_backpressure_with_buffered_items():
    stream = AsyncStream(backpressure=True, buffer_size=5)

    async def producer():
        try:
            start_time = time.perf_counter_ns()
            for i in range(10):
                await stream.push(i)
            end_time = time.perf_counter_ns()
            return (end_time - start_time) / 1_000_000_000
        finally:
            asyncio.create_task(stream.close())

    async def consumer():
        async for _ in stream:
            await asyncio.sleep(0.1)

    producer_duration, _ = await asyncio.gather(
        producer(),
        consumer(),
    )
    assert producer_duration >= 0.4
    assert producer_duration < 0.5
