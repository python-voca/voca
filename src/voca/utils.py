import re
import functools
import subprocess
import types
import importlib


from typing import Any
from typing import List
from typing import Dict
from typing import Optional
from typing import Callable
from typing import MutableMapping
from typing import Mapping
from typing import Awaitable

from typing_extensions import Protocol

import attr
import toml
import trio
import lark
import pkg_resources
import importlib_resources


import voca
from voca import context


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
    text = importlib_resources.read_text(voca, "pronunciation.toml")
    return toml.loads(text)


def value_to_pronunciation():
    return {v: k for k, v in pronunciation_to_value().items()}


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
class HandlerGroup:
    handlers: List[Handler]

    async def pick_handler(self, data):
        return self.handlers[0]


class Context(Protocol):
    async def check(self, data=None) -> bool:
        ...


@attr.dataclass
class Wrapper:
    registry: Registry
    context: Context = attr.ib(default=context.AlwaysContext)


@attr.s
class WrapperGroup:
    wrappers: List[Wrapper] = attr.ib(factory=list)


@attr.dataclass
class Rule:
    name: str
    pattern: str
    function: Callable


@attr.dataclass
class PluginModule(Protocol):
    wrapper: Wrapper


@attr.dataclass
class KeyModifier:
    name: str


@attr.dataclass
class SimpleKey:
    name: str


@attr.dataclass
class KeyChord:
    modifiers: List[KeyModifier]
    name: str


def async_runner(async_function: Callable):
    def build(*args, **kwargs) -> Callable:
        @functools.wraps(async_function)
        async def run(_message: str):
            await async_function(*args, **kwargs)

        return run

    return build


def replace(message: str) -> str:
    lookup = pronunciation_to_value()
    pattern = re.compile(r"\b(" + "|".join(lookup.keys()) + r")\b")
    return pattern.sub(lambda x: lookup[x.group()], message)


def plugin_module_paths() -> List[str]:
    return [
        entry_point.module_name + "." + entry_point.name
        for entry_point in pkg_resources.iter_entry_points("voca_plugins")
    ]


MODULE_TRANSFORMERS = []


def transform_module(module):
    for transform in MODULE_TRANSFORMERS:
        module = transform(module)

    return module
