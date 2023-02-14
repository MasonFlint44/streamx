import asyncio

from streamx.pipe import filter, range


async def double(source):
    async for value in source:
        yield value * 2


async def main():
    async for value in (range(10) | filter(lambda x: x % 2 == 0) | double):
        print(value)


asyncio.run(main())
