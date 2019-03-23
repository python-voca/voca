import functools
import subprocess
import types

from typing import Any
from typing import List
from typing import Dict
from typing import Optional
from typing import Callable
from typing import MutableMapping
from typing import Mapping
from typing import Awaitable


import attr
import toml
import trio
import lark
import importlib_resources

import intervoice


@attr.s
class Registry:
    pattern_to_function: MutableMapping[str, Callable] = attr.ib(factory=dict)
    patterns: MutableMapping = attr.ib(factory=dict)

    def register(self, pattern: str) -> Callable:
        def _register(function: Callable) -> Callable:
            self.pattern_to_function[pattern] = function
            return function

        return _register

    def define(self, patterns: Optional[Mapping[str, str]] = None, **kwargs):
        if patterns:
            self.patterns.update(patterns)
        self.patterns.update(kwargs)


def pronunciation_to_value() -> MutableMapping[str, Any]:
    text = importlib_resources.read_text(intervoice, "pronunciation.toml")
    return toml.loads(text)


async def run_subprocess(
    command: List[str], *, input=None, capture_output=False, **options
):
    if input is not None:
        options["stdin"] = subprocess.PIPE
    if capture_output:
        options["stdout"] = options["stderr"] = subprocess.PIPE

    stdout_chunks: List = []
    stderr_chunks: List = []

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


def quote(word: str) -> str:
    if word.startswith('"'):
        return f"'{word}'"
    return f'"{word}"'


def regex(word):
    return f"/{word}/"


@attr.dataclass
class Handler:
    registry: Registry
    parser: lark.Lark
    rule_name_to_function: dict


@attr.dataclass
class Rule:
    name: str
    pattern: str
    function: Callable


def async_runner(async_function: Callable):
    def build(*args, **kwargs) -> Callable:
        @functools.wraps(async_function)
        async def run(_message: str):
            await async_function(*args, **kwargs)

        return run

    return build
