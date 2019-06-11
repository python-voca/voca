import typing as t

import attr
import lark

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


