"""Trace requests for debugging."""

import functools
import json
import os
from datetime import datetime

import aiofiles


def tracing_request(func=None, *, enabled: bool = True):
    """Record header and body of requests for easy tracing/debugging."""

    def decorator(inner_func):
        @functools.wraps(inner_func)
        async def wrapper(*args, **kwargs):
            if not enabled:
                return await inner_func(*args, **kwargs)

            request = None
            if len(args) >= 2:
                request = args[1]
            elif "request" in kwargs:
                request = kwargs["request"]

            if request is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                log_folder = "logs"
                log_timestamp_folder = os.path.join(log_folder, timestamp)
                os.makedirs(log_timestamp_folder, exist_ok=True)

                # Log headers
                headers_filename = os.path.join(log_timestamp_folder, "tracing_headers.json")
                async with aiofiles.open(headers_filename, "w") as f:
                    await f.write(json.dumps(dict(request.headers), indent=4))

                body = await request.body()

                body_filename = os.path.join(log_timestamp_folder, "tracing_body.json")
                async with aiofiles.open(body_filename, "wb") as f:
                    await f.write(body)

            result = await inner_func(*args, **kwargs)
            return result

        return wrapper

    if func is not None and callable(func):
        return decorator(func)
    return decorator
