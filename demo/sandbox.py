import asyncio

from streamz import AsyncStream

# TODO: need to write github actions to build and deploy to pypi
stream = AsyncStream()


async def producer1():
    for i in range(10):
        await stream.push(i)
    await stream.close()


async def producer2():
    for i in range(10, 20):
        await stream.push(i)
    await stream.close()


async def consumer():
    async for item in stream:
        print(f"Consumer 1: {item}")


async def main():
    await asyncio.gather(producer1(), consumer(), producer2())


asyncio.run(main(), debug=True)
