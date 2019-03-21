from intervoice import utils


registry = utils.Registry()


@registry.register
async def say(message):
    await utils.run_subprocess(["notify-send", " ".join(message)])


async def press(chord):
    await utils.run_subprocess(["xdotool", "key", chord])


@registry.register
async def switch(message):
    [message] = message
    key = utils.pronunciation_to_value()[message]
    await press(f"super+{key}")
