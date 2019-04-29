import functools
import sys
import time

from typing import List
from typing import Callable
from typing import Coroutine
from typing import Awaitable


import trio
import pyautogui
import pynput
import pynput.keyboard

from voca import utils
from voca import platforms
from voca import log

registry = utils.Registry()

registry.define(
    {
        "?any_text": r"/\w.+/",
        "key": utils.regex("|".join(utils.pronunciation_to_value().keys())),
        "chord": 'key ("+" chord)*',
    }
)


@log.log_call
def type_chord(chord):
    keyboard = pynput.keyboard.Controller()
    modifiers = [getattr(pynput.keyboard.Key, mod.name) for mod in chord.modifiers]

    try:
        key = pynput.keyboard.Key[chord.name]
    except KeyError:
        key = chord.name

    if modifiers:
        with keyboard.pressed(*modifiers):
            # XXX This seems like it wouldn't work, but it is working in tests.
            keyboard.press(key)
            keyboard.release(key)
            pyautogui.press(chord.name)

    else:
        # I'm not sure why pynput wasn't working on simple keys, but this seems to work.
        pyautogui.press(chord.name)


@log.log_async_call
async def press(chord: str):
    if isinstance(chord, str):
        await trio.run_sync_in_worker_thread(
            functools.partial(pyautogui.typewrite, [chord])
        )
        return

    await trio.run_sync_in_worker_thread(type_chord, chord)


@log.log_async_call
async def write(message: str):
    await trio.run_sync_in_worker_thread(
        functools.partial(pyautogui.typewrite, message)
    )


@registry.register('"alert" any_text')
@log.log_async_call
async def _alert(text):
    await trio.run_sync_in_worker_thread(functools.partial(pyautogui.alert, text))


@log.log_async_call
async def speak(message):
    await utils.run_subprocess(["say", message])


@registry.register("chord")
@registry.register('"say" chord')
@log.log_async_call
async def _say(message: List[str]):
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(chord_value)


@registry.register('"switch" chord')
@log.log_async_call
async def _switch(message: List[str]):
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(f"super+{chord_value}")


press_key: Callable = utils.async_runner(press)


registry.pattern_to_function['"monitor"'] = press_key("M")
registry.pattern_to_function['"mouse"'] = press_key("O")


@registry.register('"div0"')
async def _div0(*args):
    1 / 0


wrapper = utils.Wrapper(registry)
