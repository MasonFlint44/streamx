# streamx

## Overview

![PyPI](https://img.shields.io/pypi/v/streamx?style=for-the-badge) ![PyPI - License](https://img.shields.io/pypi/l/streamx?style=for-the-badge)

`streamx` is a Python library that provides a framework for asynchronously streaming data between producers and consumers. It is designed to handle scenarios where data is produced at irregular intervals and consumed by one or more consumers in real-time. The library supports asynchronous iteration and includes a basic backpressure mechanism to ensure that consumers are not overwhelmed by the producer's data flow.

## Features

- **Asynchronous Stream Processing**: Allows for the production and consumption of data streams in an asynchronous manner.
- **Asynchronous Iteration**: Supports asynchronous `for` loops, enabling consumers to process data as it becomes available.
- **Implicit Backpressure**: Prevents the producer from overwhelming consumers by ensuring that all consumers are ready before producing the next value.

## Installation

To use this library, simply install it via `pip`:
```bash
pip install streamx
```

## Usage

### Creating an Async Stream

To create an asynchronous stream, instantiate the `AsyncStream` class with the desired data type:

```python
from streamx import AsyncStream

stream = AsyncStream[int]()
```

### Producing Data

To produce data, use the `put()` method. This method will asynchronously place a value into the stream:

```python
await stream.put(1)
await stream.put(2)
await stream.put(3)
```

### Consuming Data

To consume data, use an asynchronous `for` loop with the `AsyncStream` instance:

```python
async for value in stream:
    print(value)
```

### Closing the Stream

To signal the end of the stream and close it, use the `close()` method:

```python
await stream.close()
```

### Example

Here’s a complete example of how to use the `AsyncStream` library:

```python
import asyncio
from async_stream import AsyncStream

async def producer(stream: AsyncStream[int]):
    for i in range(5):
        print(f"Producing: {i}")
        await stream.put(i)
        await asyncio.sleep(1)
    await stream.close()

async def consumer(stream: AsyncStream[int]):
    async for value in stream:
        print(f"Consuming: {value}")
        await asyncio.sleep(2)

async def main():
    stream = AsyncStream[int]()
    await asyncio.gather(consumer(stream), producer(stream))

asyncio.run(main())
```

In this example, the producer generates a value every second, while the consumer processes each value with a two-second delay. The backpressure mechanism ensures that the producer does not push a new value until the consumer is ready.

## Backpressure Mechanism

The `AsyncStream` library implements an implicit backpressure mechanism to manage the flow of data between the producer and consumers:

- **Producer Control**: The `put()` method in `AsyncStream` waits for all consumers to signal that they are ready for the next value. This ensures that the producer does not overwhelm consumers by producing data faster than they can handle.
  
- **Global Backpressure**: Backpressure is applied across all consumers. If any consumer is slow, the producer is effectively paused until all consumers are ready. This ensures no consumer is left behind but may lead to delays if one consumer is significantly slower than others.

- **Resource Management**: The implicit backpressure mechanism helps prevent memory buildup by ensuring that consumers process data at their own pace. However, in high-throughput scenarios, additional logic (e.g., buffering or timeouts) might be necessary to handle slow consumers effectively.

## Contributing

Contributions are welcome! If you have ideas for features, optimizations, or bug fixes, feel free to submit a pull request or open an issue.

## License

This library is open-source and licensed under the MIT License. See the `LICENSE` file for more details.
