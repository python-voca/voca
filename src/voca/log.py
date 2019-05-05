"""Provide logging functions.

Eliot is used for structured logging.
"""

from __future__ import annotations

import collections
import contextlib
import datetime
import functools
import json
import sys
import inspect
import os
import io
import traceback
import types
import pathlib

from typing import Optional
from typing import Callable
from typing import Any
from typing import Union
from typing import Iterable
from typing import Container
from typing import List
from typing import Dict

import attr
import eliot
import six

from voca import config
from voca import utils


@utils.public
@functools.singledispatch
def to_serializable(obj: Any) -> Union[str, list, dict, int, float]:
    try:
        return {"type": type(obj).__name__, "attributes": attr.asdict(obj)}
    except attr.exceptions.NotAnAttrsClassError:
        return str(obj)


@to_serializable.register(types.SimpleNamespace)
def _(obj):
    return vars(obj)


@utils.public
def json_to_file(file: Optional[io.TextIOWrapper] = None) -> Callable:
    """Serialize to json and print into a file, defaulting to stdout."""

    if file is None:

        file = sys.stdout

    def _json_to_file(x):

        print(json.dumps(x, default=to_serializable), file=file)

    return _json_to_file


def _exception_lines(exc: BaseException) -> List[str]:
    """Get a list of traceback string lines from an exception."""
    return traceback.format_exception(type(exc), exc, exc.__traceback__)


def _extract_traceback(exc: BaseException) -> str:
    """Make a traceback string from an exception."""
    return "".join(_exception_lines(exc))


def _exception_data(exc: BaseException) -> Dict[str, Any]:
    """Collect interesting data to report about the exception."""
    exclude = set(dir(Exception())) - {"args", "__cause__", "__context__"}
    return {k: v for k, v in inspect.getmembers(exc) if k not in exclude}


def summarize_exception(exc: BaseException) -> Dict[str, dict]:
    """Combine exception data with traceback into a dict for logging."""
    return {
        "traceback": _extract_traceback(exc),
        "exception_data": _exception_data(exc),
    }


@utils.public
def log_call(
    wrapped_function: Optional[Callable] = None,
    action_type: Optional[str] = None,
    include_args: Optional[Iterable[str]] = None,
    include_result: bool = True,
) -> Callable:
    """Decorator/decorator factory that logs inputs and the return result.
    If used with inputs (i.e. as a decorator factory), it accepts the following
    parameters:
    @param action_type: The action type to use.  If not given the function name
        will be used.
    @param include_args: If given, should be a list of strings, the arguments to log.
    @param include_result: True by default. If False, the return result isn't logged.
    """
    if wrapped_function is None:
        return functools.partial(
            log_call,
            action_type=action_type,
            include_args=include_args,
            include_result=include_result,
        )

    if action_type is None:
        action_type = "{}.{}".format(
            wrapped_function.__module__, wrapped_function.__qualname__
        )

    if include_args is not None:

        sig = inspect.signature(wrapped_function)
        if set(include_args) - set(sig.parameters):
            raise ValueError(
                (
                    "include_args ({}) lists arguments not in the " "wrapped function"
                ).format(include_args)
            )

    @functools.wraps(wrapped_function)
    def logging_wrapper(*args, **kwargs):
        bound_args = inspect.signature(wrapped_function).bind(*args, **kwargs)

        # Remove self if it's included:
        if "self" in bound_args.arguments:
            bound_args.arguments.pop("self")

        # Filter arguments to log, if necessary:
        if include_args is not None:
            bound_args.arguments = {k: bound_args.arguments[k] for k in include_args}

        with eliot.start_action(
            action_type=action_type, **bound_args.arguments
        ) as action:

            result = wrapped_function(*args, **kwargs)
            if not include_result:
                return result
            action.add_success_fields(result=result)
            return result

    return logging_wrapper


@utils.public
def log_async_call(
    wrapped_function: Optional[Callable] = None,
    action_type: Optional[str] = None,
    include_args: Optional[Iterable[str]] = None,
    include_result: bool = True,
) -> Callable:
    """Decorator/decorator factory that logs inputs and the return result.
    If used with inputs (i.e. as a decorator factory), it accepts the following
    parameters:
    @param action_type: The action type to use.  If not given the function name
        will be used.
    @param include_args: If given, should be a list of strings, the arguments to log.
    @param include_result: True by default. If False, the return result isn't logged.
    """
    if wrapped_function is None:
        return functools.partial(
            log_call,
            action_type=action_type,
            include_args=include_args,
            include_result=include_result,
        )

    if action_type is None:

        action_type = "{}.{}".format(
            wrapped_function.__module__, wrapped_function.__qualname__
        )

    if include_args is not None:

        sig = inspect.signature(wrapped_function)
        if set(include_args) - set(sig.parameters):
            raise ValueError(
                f"include_args ({include_args}) lists arguments not in the "
                "wrapped function"
            )

    @functools.wraps(wrapped_function)
    async def logging_wrapper(*args, **kwargs):
        bound_args = inspect.signature(wrapped_function).bind(*args, **kwargs)

        # Remove self if it's included:
        if "self" in bound_args.arguments:
            bound_args.arguments.pop("self")

        # Filter arguments to log, if necessary:
        if include_args is not None:
            bound_args.arguments = {k: bound_args.arguments[k] for k in include_args}

        with eliot.start_action(
            action_type=action_type, **bound_args.arguments
        ) as action:

            result = await wrapped_function(*args, **kwargs)

            if include_result:
                action.add_success_fields(result=result)

            return result

    return logging_wrapper


def get_log_filename() -> pathlib.Path:
    """Return the filename of the session log, creating any parent directories."""

    log_dir = config.get_config_dir() / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)

    timestamp = datetime.datetime.now().isoformat()
    name = timestamp + ".voca-log.jsonl"

    return log_dir / name
