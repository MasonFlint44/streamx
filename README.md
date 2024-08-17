# streamx

![PyPI](https://img.shields.io/pypi/v/streamx?style=for-the-badge) ![PyPI - License](https://img.shields.io/pypi/l/streamx?style=for-the-badge)

The simple solution for sharing async data streams in Python.

## Installation

```bash
pip install streamx
```

## Usage

### Creating a stream

```python
from streamx import AsyncStream

stream = AsyncStream[int]()
```

### Putting items in a stream

You can place items in a stream using the put method. This method is a coroutine, so you'll need to await it. All iterators receive each item placed in the stream.

```python
await stream.put(1)
await stream.put(2)
await stream.put(3)
```

### Consuming a stream

To consume a stream, you can use an async for loop. Many tasks can listen to the stream at the same time, and each task will receive each item put in the stream while it is iterating.

```python
async for item in stream:
    print(item)
```

### Closing a Stream

Once you're done placing data into a stream, you should close it to signal to iterators that there will be no more data. This signals to exit the async for loop.

```python
await stream.close()
```

### Example

```python
import asyncio

from streamx import AsyncStream


async def producer(stream: AsyncStream[int]):
    async with stream:
        for i in range(5):
            await stream.put(i)
            await asyncio.sleep(1)


async def consumer(stream: AsyncStream[int]):
    async for item in stream:
        print(item)


async def main():
    stream = AsyncStream[int]()
    await asyncio.gather(consumer(stream), consumer(stream), producer(stream))


asyncio.run(main())
```
