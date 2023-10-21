import asyncio
import time

from streamx import AsyncStream


async def listener_task(stream: AsyncStream[int]) -> None:
    with stream.listen() as listener:
        async for _ in listener:
            pass


async def main():
    stream = AsyncStream[int]()

    # Create and start N listeners
    listener_count = 1000
    _ = [asyncio.create_task(listener_task(stream)) for _ in range(listener_count)]

    # wait for listeners to start
    await asyncio.sleep(0)

    # Push M items
    item_count = 10000
    start_time = time.time()
    for i in range(item_count):
        await stream.push(i)

    end_time = time.time()

    await stream.close()  # Inform listeners to stop

    print(
        f"Time taken to push {item_count} items to {listener_count} listeners: {end_time - start_time:.2f} seconds"
    )


asyncio.run(main())
