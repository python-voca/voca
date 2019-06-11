import string
import typing as t
import random

import attr
import dragonfly
import lark

def show(x):
    print(repr(x))


# word <rule> {list} (group) (alt1 | alt2) zero_or_more* one_or_more+ [optional]

spec_grammar = r"""

?word : body
rule : "<" body ">"
wordlist : "{" body "}"
group : "(" body ")"
alternative : "(" body ("|" body )+ ")"
zero_or_more : body "*"
one_or_more : body "+"
optional : "[" body "]"


?body : NAME

?item : word 
    | rule
    | wordlist
    | group
    | alternative
    | zero_or_more
    | one_or_more
    | optional

spec : item+

?start : spec

%import common.CNAME -> NAME
%import common.NUMBER
%import common.WS_INLINE
%ignore WS_INLINE

"""
wordlist = t.Iterable[str]


@attr.dataclass
class Lexicon:
    wordlists: t.Dict[str, wordlist] = attr.ib(factory=list)


@attr.dataclass
class SpecTransformer(lark.Transformer):
    lexicon: Lexicon

    def __attrs_post_init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def wordlist(self, name):
        return "(" + "|".join(self.lexicon.wordlists[name[0]]) + ")"

    def spec(self, arg):
        return " ".join(arg)


def transform_spec(spec: str, lexicon: Lexicon):
    parser = lark.Lark(spec_grammar)
    tree = parser.parse(spec)
    transformer = SpecTransformer(lexicon)
    return transformer.transform(tree)


@attr.dataclass
class LexiconSpec:
    lexicon: Lexicon
    spec: str


def random_string(length):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
    )


def make_grammar(*args, **kwargs):
    name = kwargs.pop("name", None)
    if name is None:
        name = random_string(10)
    return dragonfly.Grammar(*args, name=name, **kwargs)


def build_dragonfly_grammar(lexpecs: t.List[LexiconSpec]):
    grammar = make_grammar()
    for ls in lexpecs:
        dragonfly_spec = transform_spec(ls.spec, ls.lexicon)
        show(dragonfly_spec)
        rule = dragonfly.CompoundRule(name=random_string(5), spec=dragonfly_spec)
        rule._grammar = grammar
        grammar._rules.append(rule)

    return grammar

