import asyncio

import pytest

from streamx import AsyncStream


@pytest.mark.asyncio
async def test_async_stream():
    async_stream = AsyncStream[int]()
    consumed_values = []
    expected_count = 100
    consumer_count = 2

    async def producer():
        async with async_stream:
            for i in range(expected_count):
                await async_stream.put(i)

    async def consumer():
        async for value in async_stream:
            consumed_values.append(value)

    # start consumers before producer
    await asyncio.gather(consumer(), consumer(), producer())

    assert len(consumed_values) == expected_count * consumer_count
