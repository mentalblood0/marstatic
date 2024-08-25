import functools
import typing
from dataclasses import dataclass, field

import pyparsing as pp
import pyparsing.exceptions


@dataclass(frozen=True, kw_only=False)
class Number:
    value: int
    loc: tuple[int, int] | None = field(default=None, compare=False)

    def __repr__(self):
        return str(self.value)


@dataclass(frozen=True, kw_only=False)
class FundamentalRoot:
    value: str
    loc: tuple[int, int] | None = field(default=None, compare=False)

    def __repr__(self):
        return self.value


@dataclass(frozen=True, kw_only=False)
class Root:
    value: str
    loc: tuple[int, int] | None = field(default=None, compare=False)

    def __repr__(self):
        return self.value


@dataclass(frozen=True, kw_only=False)
class FundamentalAtom:
    root: FundamentalRoot
    number: Number | None = None
    loc: tuple[int, int] | None = field(default=None, compare=False)

    def __repr__(self):
        if self.number is None:
            return f"({self.root})"
        return f"({self.root}, {self.number})"


@dataclass(init=False)
class Clarification:
    First = typing.Union["Version", "Answer", FundamentalAtom]
    Other = Root | Number

    first: First
    other: tuple[Other, ...]

    @functools.cached_property
    def value(self):
        return (self.first, *self.other)

    def __init__(self, first: First, *other: Other):
        self.first = first
        self.other = other

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"C{self.value}"


@dataclass(init=False)
class Version:
    First = typing.Union["Answer", Clarification, FundamentalAtom]
    Other = Root | Number

    first: First
    other: tuple[Other, ...]

    @functools.cached_property
    def value(self):
        return (self.first, *self.other)

    def __init__(self, first: First, *other: Other):
        self.first = first
        self.other = other

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"V{self.value}"


@dataclass(init=False)
class Answer:
    First = Version | Clarification | FundamentalAtom
    Other = Version | Clarification | FundamentalAtom | Root

    first: First
    other: tuple[Other, ...]

    @functools.cached_property
    def value(self):
        return (self.first, *self.other)

    def __init__(self, first: First, *other: Other):
        self.first = first
        self.other = other

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"A{self.value}"


@dataclass(frozen=True, kw_only=False)
class Thesis:
    Ans = Answer
    V = Version
    C = Clarification
    a = Root
    A = FundamentalAtom
    r = Root
    R = FundamentalRoot
    N = Number

    value: Answer | Version | Clarification | Root | FundamentalAtom | Number

    def __repr__(self):
        return f"T{self.value}"


T = Thesis


@dataclass(frozen=False, kw_only=True, unsafe_hash=True)
class TsidParser:
    clarification_delimiter: str = "."
    version_delimiter: str = "-"
    answer_delimiter: str = "/"
    opening_bracket: str = "("
    closing_bracket: str = ")"

    def __post_init__(self):
        b = lambda e: pp.Char(self.opening_bracket).suppress() + e + pp.Char(self.closing_bracket).suppress()

        fundamental_root = (
            pp.Combine(pp.Char(pp.alphas.upper())[1, ...])
            .set_parse_action(lambda _, loc, x: FundamentalRoot(str(x[0]), loc=(loc, loc + len(x[0]))))
            .set_name("fundamental root")
        )
        root = (
            pp.Combine(pp.Char(pp.alphas.lower())[1, ...])
            .set_parse_action(lambda _, loc, x: Root(str(x[0]), loc=(loc, loc + len(x[0]))))
            .set_name("root")
        )
        number = (
            pp.Combine(pp.Char(pp.nums)[1, ...])
            .set_parse_action(lambda _, loc, x: Number(int(str(x[0])), loc=(loc, loc + len(x[0]))))
            .set_name("number")
        )
        fundamental_atom = (
            (fundamental_root + pp.Opt(number))
            .set_parse_action(
                lambda _, loc, x: FundamentalAtom(
                    *x.as_list(), loc=(loc, loc + len(x[0].value) + (len(str(x[1].value)) if len(x) > 1 else 0))
                )
            )
            .set_name("fundamental atom")
        )

        clarification_delimiter = pp.Char(self.clarification_delimiter).suppress()
        clarification = pp.Forward().set_name("clarification")

        version_delimiter = pp.Char(self.version_delimiter).suppress()
        version = pp.Forward().set_name("version")
        answer_delimiter = pp.Char(self.answer_delimiter).suppress()
        answer_element = b(version) | b(clarification) | root | fundamental_atom
        answer = (
            pp.DelimitedList(answer_element, answer_delimiter, min=2)
            .set_parse_action(lambda x: Answer(*x.as_list()))
            .set_name("answer")
        )

        clarification <<= (
            (b(answer) | b(version) | root | fundamental_atom)
            + clarification_delimiter
            + pp.DelimitedList(root | number, clarification_delimiter)
        ).set_parse_action(lambda x: Clarification(*x.as_list()))

        version <<= (
            (b(answer) | b(clarification) | root | fundamental_atom)
            + version_delimiter
            + pp.DelimitedList(root | number, version_delimiter)
        ).set_parse_action(lambda x: Version(*x.as_list()))

        self.thesis = (
            (answer | version | clarification | fundamental_atom)
            .set_parse_action(lambda x: Thesis(x.as_list()[0]))
            .set_name("thesis")
        )

    @functools.cache
    def parse(self, s: str):
        try:
            return self.thesis.parse_string(s, parse_all=True)[0]
        except pyparsing.exceptions.ParseException as e:
            raise Exception(f'Parsing "{s}": {e}')


# class TFactory:
#     parser = TsidParser()
#
#     def __init__(self):
#         self.value: None | T = None
#
#     def __getattribute__(self, key: str):
#         if key in ("value", "parser", "end"):
#             return super().__getattribute__(key)
#         parsed_key = self.parser.parse(key)
#         if self.value is None:
#             self.value = parsed_key
#         elif isinstance(self.value, FundamentalAtom):
#             self.value = Clarification(self.value, )
#
#         return self
#
#     @property
#     def end(self):
#         result = self.value
#         self.value = None
#         return result
#
#
# TT = TFactory()
