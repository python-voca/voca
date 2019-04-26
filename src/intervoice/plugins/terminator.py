from intervoice import utils
from intervoice import context
from intervoice.plugins import basic

registry = utils.Registry()


registry.define({"?text": r"/\w.+/"})
registry.register("declare text")(basic._alert)


wrapper = utils.Wrapper(
    registry=registry, context=context.WindowContext(title="terminator")
)
