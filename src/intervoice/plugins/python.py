from intervoice.casterlike import R
from intervoice.casterlike import Text
from intervoice.casterlike import Key
from intervoice.casterlike import add_to_registry


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
    "name": R(Text('if __name__ == "__main__":\n\t'), rdescript="Python: name==main"),
}


registry = add_to_registry(mapping, registry)

wrapper = utils.Wrapper(registry)
