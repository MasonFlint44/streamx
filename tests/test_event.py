import asyncio

import pytest

from streamx import SharedEvent, SharedEventListener


@pytest.mark.asyncio
async def test_shared_event_listener_wait():
    # Test that the `wait` method blocks until a value is pushed
    listener = SharedEventListener()

    async def push_value():
        await asyncio.sleep(0.1)
        listener.push("value")

    async def wait_on_listener():
        value = await listener.wait()
        assert value == "value"

    await asyncio.gather(wait_on_listener(), push_value())


@pytest.mark.asyncio
async def test_shared_event_listener_ready():
    # Test that the `ready` property returns an event that is set when a listener is waiting
    listener = SharedEventListener()

    async def push_value():
        await asyncio.sleep(0.1)
        listener.push("value")

    async def wait_for_listener():
        await listener.wait()

    async def wait_for_ready():
        await listener.ready.wait()
        assert listener.ready.is_set()

    await asyncio.gather(wait_for_ready(), wait_for_listener(), push_value())


@pytest.mark.asyncio
async def test_shared_event_share():
    # Test that the `share` method pushes the result of the coroutine to all listeners
    event = SharedEvent()

    async def coro():
        return "value"

    results = []

    async def listener(event: SharedEvent, results: list):
        with event.listen() as listener:
            value = await listener.wait()
            results.append(value)

    tasks = [
        asyncio.create_task(listener(event, results)),
        asyncio.create_task(listener(event, results)),
        asyncio.create_task(listener(event, results)),
    ]

    # Wait for all listeners to start
    await asyncio.sleep(0)

    # Share the result of the coroutine
    await event.share(coro())

    # Wait for all listeners to finish
    await asyncio.gather(*tasks)

    # Check that the coroutine result was shared with all listeners
    assert len(results) == 3
    for result in results:
        assert result == "value"


@pytest.mark.asyncio
async def test_share_listen_and_wait():
    listeners_started = [asyncio.Event() for _ in range(3)]

    async def listener(event: SharedEvent[str], message_count: int, started: asyncio.Event) -> None:
        with event.listen() as listener:
            started.set()
            for _ in range(message_count):
                value = await listener.wait()

    queue = asyncio.Queue()
    event: SharedEvent[str] = SharedEvent()

    # add items to queue
    await queue.put("hello world")
    await queue.put("another one")
    await queue.put("dj khaled")

    # Start receiver tasks
    tasks = [
        asyncio.create_task(listener(event, queue.qsize(), listeners_started[0])),
        asyncio.create_task(listener(event, queue.qsize(), listeners_started[1])),
        asyncio.create_task(listener(event, queue.qsize(), listeners_started[2])),
    ]

    # Wait for receivers to start
    await asyncio.gather(*[event.wait() for event in listeners_started])

    # Send events
    value = await event.share(queue.get())
    assert value == "hello world"

    value = await event.share(queue.get())
    assert value == "another one"

    value = await event.share(queue.get())
    assert value == "dj khaled"

    # Wait for receivers to finish
    await asyncio.gather(*tasks)
