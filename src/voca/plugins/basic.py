import functools
import sys
import time
import signal
import os

from typing import List
from typing import Callable
from typing import Coroutine
from typing import Awaitable


import trio
import eliot

from voca import utils
from voca import platforms
from voca import log


try:
    import pyautogui
except KeyError as e:
    # Display failed
    pyautogui = utils.ModuleLazyRaise("pyautogui", e)

try:
    import pynput
    import pynput.keyboard
except Exception as e:
    pynput = utils.ModuleLazyRaise("pynput", e)


registry = utils.Registry()

v2p = utils.value_to_pronunciation()
registry.define(
    {
        "?any_text": r"/\w.+/",
        "key": utils.regex("|".join(utils.pronunciation_to_value().keys())),
        "chord": 'key ("+" chord)*',
        "?sigstr": utils.regex(
            "|".join(["SIGUSR1", "SIGUSR2"] + list(v2p[str(x)] for x in range(20)))
        ),
        "?pid": r"/\d+/",
    }
)


@log.log_call
def type_chord(chord: str):
    """Press a key chord. To avoid blocking, call this in a thread."""
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
    """Press a key chord."""
    if isinstance(chord, str):
        await trio.run_sync_in_worker_thread(
            functools.partial(pyautogui.typewrite, [chord])
        )
        return

    await trio.run_sync_in_worker_thread(type_chord, chord)


@log.log_async_call
async def write(message: str):
    """Type the ``message``."""
    await trio.run_sync_in_worker_thread(
        functools.partial(pyautogui.typewrite, message)
    )


@registry.register('"alert" any_text')
@log.log_async_call
async def _alert(text: str):
    """Show a gui alert with ``text``."""
    await trio.run_sync_in_worker_thread(functools.partial(pyautogui.alert, text))


@log.log_async_call
async def speak(message: str):
    """Speak ``message`` aloud."""
    await utils.run_subprocess(["say", message])


@registry.register("chord")
@registry.register('"say" chord')
@log.log_async_call
async def _say(message: List[str]):
    """Press a key."""
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(chord_value)


@registry.register('"switch" chord')
@log.log_async_call
async def _switch(message: List[str]):
    """Press super + key."""
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(f"super+{chord_value}")


@registry.register('"signal" pid sigstr')
async def send_signal(message):
    """Send a signal to a process."""

    pid, sigstr = message
    try:
        sig = int(sigstr)
    except ValueError:
        sig = getattr(signal, sigstr)

    with eliot.start_action(action_type="kill_signal", signum=sig, pid=pid):
        os.kill(int(pid), sig)


press_key: Callable = utils.async_runner(press)


registry.pattern_to_function['"monitor"'] = press_key("M")
registry.pattern_to_function['"mouse"'] = press_key("O")


@registry.register('"div0"')
async def _div0(*args):
    1 / 0


wrapper = utils.Wrapper(registry)
