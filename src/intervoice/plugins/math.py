import sys

from typing import List

import sympy
import sympy.parsing.sympy_parser

from voca import utils
from voca.plugins import basic

registry = utils.Registry()
registry.define({"?math": r"/[A-Za-z0-9\-\+ ]+/"})


@registry.register('"solve" math')
@registry.register('"arch" math')
async def _solve(items: List[str]):

    [message] = items
    message = utils.replace(message)
    expr = sympy.parsing.sympy_parser.parse_expr(message)
    result = str(expr.simplify())

    await basic.announce([result])
    await basic.speak(str(result))


wrapper = utils.Wrapper(registry)
