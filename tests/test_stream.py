import asyncio

import pytest

from streamz import AsyncStream


@pytest.mark.asyncio
async def test_push_and_consume():
    stream: AsyncStream[int] = AsyncStream()

    async def producer():
        for i in range(10):
            await stream.push(i)
        await stream.close()

    async def consumer():
        items = []
        async for item in stream:
            items.append(item)
        return items

    asyncio.create_task(producer())
    result = await consumer()
    assert result == list(range(10))


@pytest.mark.asyncio
async def test_push_from_same_task_raises_error():
    stream: AsyncStream[int] = AsyncStream()

    async def producer():
        for i in range(10):
            await stream.push(i)
        await stream.close()

    async def consumer():
        async for _ in stream:
            with pytest.raises(RuntimeError):
                await stream.push(123)

    asyncio.create_task(producer())
    consumer_task = asyncio.create_task(consumer())
    await consumer_task


@pytest.mark.asyncio
async def test_multiple_consumers_raises_error():
    stream = AsyncStream()

    async def producer():
        for i in range(10):
            await stream.push(i)
        await stream.close()

    async def consumer1():
        items = []
        async for item in stream:
            items.append(item)
        return items

    async def consumer2():
        with pytest.raises(RuntimeError):
            async for _ in stream:
                pass

    asyncio.create_task(producer())
    asyncio.create_task(consumer1())
    asyncio.create_task(consumer2())
