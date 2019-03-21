import importlib_resources
import subprocess
import functools
import json
import sys
import collections
import inspect
import contextlib

import attr
import eliot
import six
import toml
import trio

import intervoice


@attr.s
class Registry:
    mapping = attr.ib(factory=dict)

    def register(self, function):
        self.mapping[function.__name__] = function
        return function


def pronunciation_to_value():
    text = importlib_resources.read_text(intervoice, "pronunciation.toml")
    return toml.loads(text)


async def run_subprocess(command, *, input=None, capture_output=False, **options):
    if input is not None:
        options["stdin"] = subprocess.PIPE
    if capture_output:
        options["stdout"] = options["stderr"] = subprocess.PIPE

    stdout_chunks = []
    stderr_chunks = []

    async with trio.Process(command, **options) as proc:

        async def feed_input():
            async with proc.stdin:
                if input:
                    try:
                        await proc.stdin.send_all(input)
                    except trio.BrokenResourceError:
                        pass

        async def read_output(stream, chunks):
            async with stream:
                while True:
                    chunk = await stream.receive_some(32768)
                    if not chunk:
                        break
                    chunks.append(chunk)

        async with trio.open_nursery() as nursery:
            if proc.stdin is not None:
                nursery.start_soon(feed_input)
            if proc.stdout is not None:
                nursery.start_soon(read_output, proc.stdout, stdout_chunks)
            if proc.stderr is not None:
                nursery.start_soon(read_output, proc.stderr, stderr_chunks)
            await proc.wait()

    stdout = b"".join(stdout_chunks) if proc.stdout is not None else None
    stderr = b"".join(stderr_chunks) if proc.stderr is not None else None

    if proc.returncode:
        raise subprocess.CalledProcessError(
            proc.returncode, proc.args, output=stdout, stderr=stderr
        )
    else:
        return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


def log_call(
    wrapped_function=None, action_type=None, include_args=None, include_result=True
):
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


@functools.singledispatch
def to_serializable(obj):
    try:
        return attr.asdict(obj)
    except attr.exceptions.NotAnAttrsClassError:
        return str(obj)


def json_to_file(file=None):

    if file is None:
        file = sys.stdout

    def _json_to_file(x):
        print(json.dumps(x, default=to_serializable), file=file)

    return _json_to_file


eliot.add_destinations(json_to_file(sys.stdout))
