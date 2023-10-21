import asyncio

from streamx import AsyncStream


async def producer(stream: AsyncStream[int]):
    for i in range(5):
        await stream.push(i)
        await asyncio.sleep(1)


async def listener(stream: AsyncStream[int]):
    with stream.listen() as listener:
        async for item in listener:
            print(item)


async def main():
    # TODO: could use context manager that closes stream on exit
    stream = AsyncStream[int]()

    # start the listeners
    asyncio.create_task(listener(stream))
    asyncio.create_task(listener(stream))

    await producer(stream)
    await stream.close()


asyncio.run(main(), debug=True)
