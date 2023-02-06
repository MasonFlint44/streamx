import asyncio
import time
from contextlib import ExitStack

import pytest

from streamx import (
    AsyncStream,
    AsyncStreamIterator,
    AsyncStreamListener,
    SharedEventListener,
    StreamClosedError,
    StreamShortCircuitError,
)


@pytest.mark.asyncio
async def test_stream_iterator_emits_pushed_items():
    event_listener = SharedEventListener[int]()
    iterator = AsyncStreamIterator(event_listener)

    items = []
    event_listener.push(123)
    items.append(await anext(iterator))
    event_listener.push(456)
    items.append(await anext(iterator))
    event_listener.push(789)
    items.append(await anext(iterator))

    assert items == [123, 456, 789]


@pytest.mark.asyncio
async def test_stream_listener_gets_current_task():
    listener = AsyncStreamListener(SharedEventListener())
    assert listener.current_task == asyncio.current_task()


@pytest.mark.asyncio
async def test_stream_listener_close():
    listener = AsyncStreamListener(SharedEventListener())
    assert not listener.closed
    listener.close()
    assert listener.closed


@pytest.mark.asyncio
async def test_stream_listener_cant_iterate_over_closed_stream():
    listener = AsyncStreamListener(SharedEventListener())
    listener.close()
    with pytest.raises(StreamClosedError):
        async for _ in listener:
            pass


@pytest.mark.asyncio
async def test_stream_listener_returns_an_iterator():
    listener = AsyncStreamListener(SharedEventListener())
    iterator = aiter(listener)
    assert isinstance(iterator, AsyncStreamIterator)


@pytest.mark.asyncio
async def test_stream_listener_works_with_async_for_loop():
    event_listener = SharedEventListener[int]()
    listener = AsyncStreamListener(event_listener)

    async def producer():
        event_listener.push(123)
        # wait for the `async for` loop to call anext()
        await asyncio.sleep(0)
        event_listener.push(456)
        # wait for the `async for` loop to call anext()
        await asyncio.sleep(0)
        event_listener.push(789)

    asyncio.create_task(producer())

    items = []
    async for item in listener:
        items.append(item)
        if len(items) == 3:
            break

    assert items == [123, 456, 789]


@pytest.mark.asyncio
async def test_stream_close():
    stream = AsyncStream[int]()
    assert not stream.closed
    await stream.close()
    assert stream.closed


@pytest.mark.asyncio
async def test_stream_close_emits_stop_iteration():
    stream = AsyncStream[int]()
    asyncio.create_task(stream.close())
    with stream.listen() as listener:
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(listener))


@pytest.mark.asyncio
async def test_stream_close_closes_listeners():
    stream = AsyncStream[int]()

    async def listener():
        with stream.listen() as listener:
            pass

    asyncio.create_task(listener())

    # wait for listener task to start
    await asyncio.sleep(0)

    assert not stream.closed
    await stream.close()
    assert stream.closed


@pytest.mark.asyncio
async def test_stream_close_raises_error_when_called_in_listener_context():
    stream = AsyncStream[int]()
    with stream.listen() as listener:
        with pytest.raises(StreamShortCircuitError):
            await stream.close()


@pytest.mark.asyncio
async def test_stream_listeners():
    stream = AsyncStream[int]()
    close_listeners = asyncio.Event()
    assert len(stream.listeners) == 0

    async def listener():
        with stream.listen() as listener:
            assert listener in stream.listeners
            await close_listeners.wait()
        assert listener not in stream.listeners

    asyncio.create_task(listener())
    asyncio.create_task(listener())

    # wait for listener tasks to start
    await asyncio.sleep(0)
    assert len(stream.listeners) == 2

    close_listeners.set()

    # wait for listen() to exit
    await asyncio.sleep(0)
    assert len(stream.listeners) == 0


@pytest.mark.asyncio
async def test_stream_push_raises_error_when_stream_is_closed():
    stream = AsyncStream[int]()
    await stream.close()
    with pytest.raises(StreamClosedError):
        await stream.push(123)


@pytest.mark.asyncio
async def test_stream_push_raises_error_when_called_in_listener_context():
    stream = AsyncStream[int]()
    with stream.listen():
        with pytest.raises(StreamShortCircuitError):
            await stream.push(123)


@pytest.mark.asyncio
async def test_stream_push():
    stream = AsyncStream[int]()
    items = []

    async def listener():
        with stream.listen() as listener:
            async for item in listener:
                items.append(item)

    asyncio.create_task(listener())

    # wait for listener task to start
    await asyncio.sleep(0)

    await stream.push(123)
    await stream.push(456)
    await stream.push(789)
    await stream.close()

    assert items == [123, 456, 789]


@pytest.mark.asyncio
async def test_stream_listen_raises_error_when_stream_is_closed():
    stream = AsyncStream[int]()
    await stream.close()
    with pytest.raises(StreamClosedError):
        with stream.listen():
            pass


@pytest.mark.asyncio
async def test_stream_listen_raises_error_when_called_in_listener_context():
    stream = AsyncStream[int]()
    with stream.listen():
        with pytest.raises(StreamShortCircuitError):
            with stream.listen():
                pass


@pytest.mark.asyncio
async def test_stream_listen_returns_listener():
    stream = AsyncStream[int]()
    with stream.listen() as listener:
        assert isinstance(listener, AsyncStreamListener)


@pytest.mark.asyncio
async def test_stream_listen_closes_listener_when_context_exits():
    stream = AsyncStream[int]()
    with stream.listen() as listener:
        assert not listener.closed
    assert listener.closed


@pytest.mark.asyncio
async def test_stream_listen_can_be_called_multiple_times():
    stream = AsyncStream[int]()
    with stream.listen() as listener1:
        pass
    with stream.listen() as listener2:
        pass
    assert listener1 is not listener2


@pytest.mark.asyncio
async def test_stream_listen_context_managers_exit_when_stream_is_closed():
    stream = AsyncStream[int]()
    listener_shutdown = False

    async def listener():
        nonlocal listener_shutdown
        with stream.listen() as listener:
            pass
        listener_shutdown = True

    asyncio.create_task(listener())
    await asyncio.sleep(0)
    await stream.close()
    assert listener_shutdown


@pytest.mark.asyncio
async def test_backpressure():
    stream = AsyncStream()
    item_count = 10
    consumed_count = 0
    fast_consumer_duration = 0.05
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
