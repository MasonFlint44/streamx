# Streamx

Streamx is an asyncio-compatible package for creating and consuming streams of data.

## Installation

```bash
pip install streamx
```

## Usage

### Creating a Stream

```python
from streamx import AsyncStream

stream = AsyncStream()
```

### Pushing data into a Stream

You can push data into a stream using the push method. This method is a coroutine, so you'll need to await it.

```python
await stream.push(data)
```

### Consuming a Stream

You can consume a stream using an async for loop.

```python
async for data in stream:
    do_something(data)
```

### Closing a Stream

Once you're done pushing data into a stream, you should close it to signal to consumers that there will be no more data.

```python
await stream.close()
```

### Errors

If you try to push data into a stream from the same task that's consuming it, a `RuntimeError` will be raised.

Also, if you try to consume a stream with more than one consumer, a `RuntimeError` will be raised.

### Example

```python
import asyncio
from streamx import AsyncStream

async def main():
    stream = AsyncStream()
    async def producer():
        for i in range(10):
            await stream.push(i)
        await stream.close()

    async def consumer():
        async for item in stream:
            print(item)
    asyncio.create_task(producer())
    await consumer()

await main()
```

## Contributing

We welcome contributions and bug reports. Please open an issue or submit a pull request if you have something to add.
