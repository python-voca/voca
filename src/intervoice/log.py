from __future__ import annotations

import collections
import contextlib
import functools
import json
import sys
import inspect
import os
import io

from typing import Optional
from typing import Callable
from typing import Any
from typing import Union
from typing import Iterable


import attr
import eliot
import six


@functools.singledispatch
def to_serializable(obj: Any) -> Union[str, list, dict, int, float]:
    try:
        return attr.asdict(obj)
    except attr.exceptions.NotAnAttrsClassError:
        return str(obj)


def json_to_file(file: Optional[io.TextIOWrapper] = None) -> Callable:

    if file is None:
        file = sys.stdout

    def _json_to_file(x):
        print(json.dumps(x, default=to_serializable), file=file)

    return _json_to_file


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
        if six.PY3:
            action_type = "{}.{}".format(
                wrapped_function.__module__, wrapped_function.__qualname__
            )
        else:
            action_type = wrapped_function.__name__

    if six.PY3 and include_args is not None:
        from inspect import signature

        sig = signature(wrapped_function)
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

        with contextlib.ExitStack() as stack:
            ctx = stack.enter_context(
                eliot.start_action(action_type=action_type, **bound_args.arguments)
            )
            result = wrapped_function(*args, **kwargs)
            if not include_result:
                return result
            if isinstance(result, collections.abc.Coroutine):

                async def wrap_await(stack_dup):
                    with stack_dup:
                        actual_result = await result
                        ctx.add_success_fields(result=actual_result)
                        return actual_result

                return wrap_await(stack.pop_all())

            ctx.add_success_fields(result=result)
            return result

    return logging_wrapper
