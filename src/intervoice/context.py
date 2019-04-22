import trio

from intervoice import utils
from intervoice import platforms


@platforms.implementation(platforms.System.WINDOWS, platforms.System.DARWIN)
async def get_current_window_title():
    import pygetwindow

    window = await trio.run_sync_in_worker_thread(pygetwindow.getFocusedWindow)
    return window.title


@platforms.implementation(platforms.System.LINUX)
async def get_current_window_title():
    await utils.run_subprocess(["xdotool", "getwindowfocus", "getwindowname"])
