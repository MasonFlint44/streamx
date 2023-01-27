import asyncio

from streamz import AsyncStream

stream = AsyncStream()


async def producer():
    for i in range(10):
        await stream.push(i)
    await stream.close()


async def consumer1():
    async for item in stream:
        print(f"Consumer 1: {item}")


# async def consumer2():
#     async for item in stream:
#         print(f"Consumer 2: {item}")


async def main():
    await asyncio.gather(producer(), consumer1())


asyncio.run(main(), debug=True)
