import asyncio
import json

import aiofiles

print("Getting the event loop")
LOOP = asyncio.new_event_loop()
print("Setting the event loop")
asyncio.set_event_loop(LOOP)
print("Running the event loop")
LOOP.run_forever()


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


# Example usage in an async function
def main():
    cards = {}  # Initial empty dictionary
    # Schedule the update without blocking
    schedule_update_json("cards.json", cards, {"new_key": "new_value"})
    print(f"Just after scheduling, the cards dictionary is {cards}")
    print("The update_json function is running asynchronously.")
    # Other async tasks can be awaited here
    LOOP.run_until_complete(asyncio.sleep(1))
    print(f"After a second, the cards dictionary is {cards}")

    print("Stopping the event loop")
    LOOP.stop()

    print("Closing the event loop")
    LOOP.close()


# This is typically the entry point for an async application
if __name__ == "__main__":
    print("Starting the program")
    main()
