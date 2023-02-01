import asyncio

from streamz import SharedEvent


async def receiver1(event: SharedEvent, message_count: int) -> None:
    with event.listen() as listener:
        for _ in range(message_count):
            print("receiver1: waiting for event")
            value = await listener.wait()
            print(f"receiver1: event received: {value}")


async def receiver2(event: SharedEvent, message_count: int) -> None:
    with event.listen() as listener:
        for _ in range(message_count):
            print("receiver2: waiting for event")
            value = await listener.wait()
            print(f"receiver2: event received: {value}")


async def receiver3(event: SharedEvent, message_count: int) -> None:
    with event.listen() as listener:
        for _ in range(message_count):
            print("receiver3: waiting for event")
            value = await listener.wait()
            print(f"receiver3: event received: {value}")


async def main():
    queue = asyncio.Queue()
    event = SharedEvent()

    # add items to queue
    await queue.put("hello world")
    await queue.put("another one")
    await queue.put("dj khaled")

    # Start receiver tasks
    tasks = [
        asyncio.create_task(receiver1(event, 3)),
        asyncio.create_task(receiver2(event, 3)),
        asyncio.create_task(receiver3(event, 3)),
    ]

    # Wait for receivers to start
    await asyncio.sleep(0)

    # Send event
    print("main: sending event")
    value = await event.share(queue.get())
    value = await event.share(queue.get())
    value = await event.share(queue.get())

    # Wait for receivers to finish
    await asyncio.gather(*tasks)


asyncio.run(main(), debug=True)
