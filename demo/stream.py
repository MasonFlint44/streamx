import asyncio

from streamx import AsyncStream


async def producer(stream: AsyncStream[int]):
    for i in range(5):
        await stream.push(i)
        await asyncio.sleep(1)
    await stream.close()


async def listener(stream: AsyncStream[int]):
    with stream.listen() as listener:
        async for item in listener:
            print(item)


async def main():
    stream = AsyncStream[int]()
    await asyncio.gather(producer(stream), listener(stream), listener(stream))


asyncio.run(main(), debug=True)
