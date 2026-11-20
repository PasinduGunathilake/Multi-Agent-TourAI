import asyncio
from typing import TypeVar, Coroutine, Any
from concurrent.futures import ThreadPoolExecutor

T = TypeVar("T")

def run_async_safely(coro: Coroutine[Any, Any, T]) -> T:
    """
    Safely executes an async coroutine from synchronous code:
    - If no event loop is running on the current thread, executes via asyncio.run().
    - If an event loop is already running on the current thread (e.g. inside FastAPI or an
      async worker), executes the coroutine in a separate worker thread to prevent
      nested asyncio.run() deadlocks.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # Running inside an active event loop: delegate to a background thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        # No event loop on current thread: standard asyncio.run
        return asyncio.run(coro)

__all__ = ["run_async_safely"]
