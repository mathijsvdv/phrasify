import asyncio


async def task_function():
    print("Task is running...")
    await asyncio.sleep(1)
    print("Task completed.")


tasks = set()


def main():
    # Start the event loop and run it forever
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

    # Schedule tasks dynamically
    tasks.add(asyncio.create_task(task_function()))
    tasks.add(asyncio.create_task(task_function()))
    tasks.add(asyncio.create_task(task_function()))

    # In a real application, you would dynamically schedule tasks based on events or other triggers


if __name__ == "__main__":
    main()
