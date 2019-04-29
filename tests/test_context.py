import functools
import os

import pytest
import trio


from voca import context


async def test_get_current_window_title(turtle_window):

    title = await context.get_current_window_title()
    assert title == "Python Turtle Graphics"
