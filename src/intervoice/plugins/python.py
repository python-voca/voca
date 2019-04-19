from intervoice.caster_compat import R
from intervoice.caster_compat import Text
from intervoice.caster_compat import Key
from intervoice.caster_compat import add_to_registry


from intervoice import utils

registry = utils.Registry()


mapping = {
    "with": R(Text("with "), rdescript="Python: With"),
    "open file": R(Text("open('filename','r') as f:"), rdescript="Python: Open File"),
    "read lines": R(Text("content = f.readlines()"), rdescript="Python: Read Lines"),
    "try catch": R(
        Text("try:")
        + Key("enter:2/10, backspace")
        + Text("except Exception:")
        + Key("enter"),
        rdescript="Python: Try Catch",
    ),
}

registry = add_to_registry(mapping, registry)
