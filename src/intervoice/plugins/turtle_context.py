from intervoice import utils
from intervoice import context
from intervoice.plugins import basic


registry = utils.Registry()
registry.define({"?text": r"/\w.+/"})


@registry.register('"check"')
async def _say_def(message):
    await basic.write("turt")


wrapper = utils.Wrapper(
    registry, context=context.WindowContext("Python Turtle Graphics")
)