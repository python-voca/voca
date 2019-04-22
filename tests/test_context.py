import functools
import os

import pytest
import trio


from intervoice import context



@pytest.mark.usefixtures("virtual_display")
async def test_get_current_window_title():
    import pyautogui

    proc = trio.Process(["xterm", "+bc"])
    title = await context.get_current_window_title()
    await proc.terminate()
    assert title == "xterm"
