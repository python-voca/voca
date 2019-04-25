import subprocess

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
    proc = await utils.run_subprocess(
        ["/usr/bin/xdotool", "getwindowfocus", "getwindowname"], stdout=subprocess.PIPE
    )
    return proc.stdout.decode()[:-1]
