import functools
import sys


from typing import List
from typing import Callable
from typing import Coroutine
from typing import Awaitable

from intervoice import utils


registry = utils.Registry()

registry.define(
    {
        "?text": r"/\w.+/",
        "key": utils.regex("|".join(utils.pronunciation_to_value().keys())),
        "chord": 'key ("+" chord)*',
    }
)


async def press(chord: str):
    await utils.run_subprocess(["xdotool", "key", chord])


async def write(message: str):
    await utils.run_subprocess(["xdotool", "type", message])


async def speak(message):
    await utils.run_subprocess(["say", message])


@registry.register('"say" chord')
async def _say(message: List[str]):
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(chord_value)


@registry.register('"announce" text')
async def announce(text: List[str]):
    await utils.run_subprocess(["dbus-launch", "notify-send", " ".join(text)])


@registry.register('"switch" chord')
async def _switch(message: List[str]):
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(f"super+{chord_value}")


key: Callable = utils.async_runner(press)


registry.pattern_to_function['"monitor"'] = key("M")
registry.pattern_to_function['"mouse"'] = key("O")


@registry.register('"div0"')
async def _div0(*args):
    1 / 0
