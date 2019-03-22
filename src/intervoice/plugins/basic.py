import sys


from intervoice import utils


registry = utils.Registry()

registry.define(
    {
        "?text": r"/\w.+/",
        "key": utils.regex("|".join(utils.pronunciation_to_value().keys())),
        "chord": 'key ("+" chord)*',
    }
)


async def press(chord):
    await utils.run_subprocess(["xdotool", "key", chord])


@registry.register('"say" chord')
async def _say(message):
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(chord_value)


@registry.register('"announce" text')
async def _announce(text):
    await utils.run_subprocess(["notify-send", " ".join(text)])


@registry.register('"switch" chord')
async def _switch(message):
    [chord_string] = message
    chord_value = utils.pronunciation_to_value()[chord_string]
    await press(f"super+{chord_value}")


@registry.register('"act"')
@registry.register('"reload"')
async def _reload(message):
    sys.exit(3)


@registry.register('"stop"')
async def _stop(message):
    sys.exit(4)
