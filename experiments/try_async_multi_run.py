import asyncio
import json

import aiofiles

print("Getting the event loop")
LOOP = asyncio.get_event_loop()


# Define the async update_json function
async def update_json(file_path, cards, new_data):
    # Update the cards dictionary
    cards.update(new_data)

    # Perform the file I/O asynchronously
    async with aiofiles.open(file_path, "w") as file:
        await file.write(json.dumps(cards, indent=2))

    return cards


# Function to schedule the update_json asynchronously without blocking
def schedule_update_json(file_path, cards, new_data):
    # Create and schedule the task
    task = asyncio.create_task(update_json(file_path, cards, new_data))
    # Optionally, add a callback to handle the result
    task.add_done_callback(
        lambda t: print(f"Update completed with result: {t.result()}")
    )

    return task


async def generate_sleep():
    sleep1 = asyncio.create_task(asyncio.sleep(1))
    sleep1.add_done_callback(lambda t: print(f"Sleep 1 done: {t.result()}"))
    sleep3 = asyncio.create_task(asyncio.sleep(3))
    sleep3.add_done_callback(lambda t: print(f"Sleep 3 done: {t.result()}"))

    done, pending = await asyncio.wait(
        [sleep1, sleep3], return_when=asyncio.FIRST_COMPLETED
    )

    yield done

    sleep1 = asyncio.create_task(asyncio.sleep(1))
    sleep1.add_done_callback(lambda t: print(f"Sleep 1 done again: {t.result()}"))

    done, pending = await asyncio.wait(
        [sleep1, *pending], return_when=asyncio.FIRST_COMPLETED
    )

    yield done

    sleep1 = asyncio.create_task(asyncio.sleep(1))
    sleep1.add_done_callback(lambda t: print(f"Sleep 1 done third time: {t.result()}"))

    done, pending = await asyncio.wait(
        [sleep1, *pending], return_when=asyncio.FIRST_COMPLETED
    )

    yield done


async def get_next_sleep(sleeps):
    return await sleeps.__anext__()


async def long_sleep():
    await asyncio.sleep(4)
    print("Done with long sleep")


# Example usage in an async function
def main():

    sleeps = generate_sleep()

    # When `run_until_complete(long_sleep())` is called, we are only at the first
    # yield statement, so the second and third yield statement are not even seen.
    # So if we want to get an effect of the task that we have queued up (such as updating)
    # a JSON file, we should make sure that it do so within the task and before the next
    # yield statement.
    LOOP.run_until_complete(get_next_sleep(sleeps))
    LOOP.run_until_complete(long_sleep())

    LOOP.run_until_complete(get_next_sleep(sleeps))
    LOOP.run_until_complete(get_next_sleep(sleeps))

    print("Running pending tasks before closing the event loop")
    pending = asyncio.all_tasks(LOOP)
    LOOP.run_until_complete(asyncio.gather(*pending))
    print("Closing the event loop")
    LOOP.close()


# This is typically the entry point for an async application
if __name__ == "__main__":
    print("Starting the program")
    main()
