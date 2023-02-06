# Streamx

![PyPI - License](https://img.shields.io/pypi/l/streamx?style=for-the-badge) ![PyPI](https://img.shields.io/pypi/v/streamx?style=for-the-badge)

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

### Pushing items into a stream

You can push items into a stream using the push method. This method is a coroutine, so you'll need to await it. All listening tasks will receive each item.

```python
await stream.push(1)
await stream.push(2)
await stream.push(3)
```

### Consuming a stream

To consume a stream, you can use the listen method. This method returns an async iterator, so you can use it with an async for loop. Many tasks can listen to the same stream at the same time, and each task will receive each item pushed into the stream while it is listening.

```python
with stream.listen() as listener:
    async for item in listener:
        print(item)
```

### Closing a Stream

Once you're done pushing data into a stream, you should close it to signal to consumers that there will be no more data. This signals to exit the async for loop, and prevents any new consumers from listening to the stream.

```python
await stream.close()
```

### Example

```python
import asyncio

from streamx import AsyncStream


async def main():
    stream = AsyncStream[int]()

    async def producer():
        for i in range(5):
            await stream.push(i)
            await asyncio.sleep(1)
        await stream.close()

    async def listener():
        with stream.listen() as listener:
            async for item in listener:
                print(item)

    await asyncio.gather(producer(), listener(), listener())


asyncio.run(main())
```
