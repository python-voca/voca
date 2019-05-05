from __future__ import annotations

import subprocess

from typing_extensions import Protocol

import attr
import trio


from voca import platforms
from voca import log
from voca import utils


@utils.public
@platforms.implementation(platforms.System.WINDOWS, platforms.System.DARWIN)
async def get_current_window_title() -> str:
    """Get the title of the current window."""
    import pygetwindow

    window = await trio.run_sync_in_worker_thread(pygetwindow.getFocusedWindow)
    return window.title


@utils.public
@platforms.implementation(platforms.System.LINUX)
async def get_current_window_title():
    """Get the title of the current window."""
    proc = await utils.run_subprocess(
        ["/usr/bin/xdotool", "getwindowfocus", "getwindowname"], stdout=subprocess.PIPE
    )
    return proc.stdout.decode()[:-1]


@utils.public
@attr.dataclass
class WindowContext:
    title: str

    async def check(self, data=None) -> bool:
        """Check whether the required name occurs within the current window title."""
        current_title = await get_current_window_title()
        return self.title in current_title


@utils.public
@log.log_async_call
async def filter_wrappers(
    wrapper_group: utils.WrapperGroup, data: dict
) -> utils.WrapperGroup:
    """Exclude wrappers that fail to match the current context."""
    allowed = []
    for wrapper in wrapper_group.wrappers:

        if await wrapper.context.check(data):
            allowed.append(wrapper)
    return utils.WrapperGroup(allowed)


AlwaysContext = utils.AlwaysContext
NeverContext = utils.NeverContext
