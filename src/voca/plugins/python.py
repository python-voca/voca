from voca.caster_adapter import R
from voca.caster_adapter import Text
from voca.caster_adapter import Key
from voca.caster_adapter import add_to_registry


from voca import utils

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
    "name": R(Text('if __name__ == "__main__":\n\t'), rdescript="Python: name==main"),
}


registry = add_to_registry(mapping, registry)

wrapper = utils.Wrapper(registry)
