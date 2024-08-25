import asyncio
import concurrent.futures
import functools
import json
import platform
from datetime import date, datetime
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    cast,
)

import psutil
from app.schemas import JSONSerializable

T = TypeVar("T")
P = ParamSpec("P")


def get_system_info(cpu_percent_interval: int = 1) -> Dict:
    # Gather OS information
    os_info = {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine_type": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    # Gather CPU information
    cpu_info = {
        "cpu_count": psutil.cpu_count(),
        "cpu_usage_percent": psutil.cpu_percent(interval=cpu_percent_interval),
    }

    # Gather Memory information
    memory = psutil.virtual_memory()
    memory_info = {
        "total_memory_mb": memory.total / (1024 * 1024),
        "available_memory_mb": memory.available / (1024 * 1024),
        "used_memory_mb": memory.used / (1024 * 1024),
        "memory_usage_percent": memory.percent,
    }

    # Combining all the information
    system_info = {"operating_system": os_info, "cpu": cpu_info, "memory": memory_info}

    return system_info


def is_json_serializable(obj: Union[JSONSerializable, Any]) -> bool:
    """Check if an object is JSON serializable."""

    try:
        json.dumps(obj, cls=DateTimeEncoder)
        return True
    except TypeError:
        return False


def is_coro_func(func: Union[Callable[P, T], Callable[P, Awaitable[T]]]) -> bool:
    """Check the function a coroutine function or not."""
    if not callable(func):
        raise ValueError(f"The {func} is not callable.")

    output = False

    if isinstance(func, functools.partial):
        if asyncio.iscoroutinefunction(func.func):
            output = True

    elif asyncio.iscoroutinefunction(func):
        output = True

    else:
        if hasattr(func, "__call__") and asyncio.iscoroutinefunction(func.__call__):
            output = True

    return output


async def run_as_coro(
    func: Union[Callable[P, T], Callable[P, Awaitable[T]]],
    *args,
    max_workers: Optional[int] = None,
    **kwargs,
) -> T:
    """Run a function in a thread or coroutine."""

    if not callable(func):
        raise ValueError(f"The {func} is not callable.")

    output = None

    if is_coro_func(func):
        partial_func = functools.partial(func, *args, **kwargs)
        partial_func = cast(Callable[[], Awaitable[T]], partial_func)
        output = await partial_func()

    else:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            partial_func = functools.partial(func, *args, **kwargs)
            output = await loop.run_in_executor(pool, partial_func)

    output = cast(T, output)
    return output


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)
