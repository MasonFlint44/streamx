import asyncio

from streamx import AsyncStream

# TODO: need to write github actions to build and deploy to pypi


async def sender(stream: AsyncStream[int]) -> None:
    for i in range(5):
        await asyncio.sleep(1)
        await stream.push(i)
    await stream.close()


async def receiver(stream: AsyncStream[int]) -> None:
    async for item in stream:
        print(f"received: {item}")
        await asyncio.sleep(1)


# Start sender and receiver tasks
async def main():
    stream = AsyncStream()
    await asyncio.gather(sender(stream), receiver(stream))


asyncio.run(main(), debug=True)
