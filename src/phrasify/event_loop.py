import asyncio
from asyncio import AbstractEventLoop, Future
from threading import Thread
from typing import Coroutine


def start_background_loop(loop: AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    finally:
        # Wait one second, then cancel all tasks and shutdown the loop
        loop.run_until_complete(asyncio.sleep(1.0))
        cancel_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


def cancel_tasks(loop: AbstractEventLoop) -> None:
    to_cancel = asyncio.all_tasks(loop)
    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, loop=loop, return_exceptions=True)
    )


def create_event_loop_thread() -> AbstractEventLoop:
    """
    From https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058
    """
    event_loop = asyncio.new_event_loop()
    thread = Thread(target=start_background_loop, args=(event_loop,), daemon=True)
    thread.start()
    return event_loop


EVENT_LOOP = create_event_loop_thread()


def run_coroutine_in_thread(coro: Coroutine) -> Future:
    """
    From https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058
    """
    return asyncio.run_coroutine_threadsafe(coro, EVENT_LOOP)
