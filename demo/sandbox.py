import asyncio

from streamx.pipe import AsyncPipeline, filter, range


async def generator_two(source):
    async for value in source:
        yield value * 2


async def main():
    async for value in (
        AsyncPipeline[int]() | range(10) | filter(lambda x: x % 2 == 0) | generator_two
    ):
        print(value)


asyncio.run(main())
