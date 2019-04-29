from __future__ import annotations

import subprocess

from typing_extensions import Protocol

import attr
import trio


from voca import platforms
from voca import log


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


@attr.dataclass
class WindowContext:
    title: str

    async def check(self, data=None) -> bool:
        current_title = await get_current_window_title()
        return self.title in current_title


@attr.dataclass
class AlwaysContext:
    async def check(self, data=None) -> bool:
        return True


@attr.dataclass
class NeverContext:
    async def check(self, data=None) -> bool:
        return False


@log.log_async_call
async def filter_wrappers(
    wrapper_group: utils.WrapperGroup, data: dict
) -> utils.WrapperGroup:
    allowed = []
    for wrapper in wrapper_group.wrappers:

        if await wrapper.context.check(data):
            allowed.append(wrapper)
    return utils.WrapperGroup(allowed)


from voca import utils
