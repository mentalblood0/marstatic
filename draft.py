import functools
from dataclasses import dataclass

import pyparsing as pp
import pytest


@dataclass(frozen=True, kw_only=False)
class Number:
    value: int


@dataclass(frozen=True, kw_only=False)
class FundamentalRoot:
    value: str


@dataclass(frozen=True, kw_only=False)
class Root:
    value: str


@dataclass(frozen=True, kw_only=False)
class FundamentalAtom:
    root: FundamentalRoot
    number: Number | None = None


@dataclass(frozen=True, kw_only=False)
class Atom:
    root: Root
    number: Number | None = None


@dataclass(frozen=True, kw_only=False)
class Clarification:
    value: list[Atom | FundamentalAtom | Number]


@dataclass(frozen=True, kw_only=False)
class Version:
    value: list[Clarification | Atom | FundamentalAtom | Number]


@dataclass(frozen=True, kw_only=False)
class Answer:
    value: list[Version | Clarification | Atom | FundamentalAtom | Number]


@dataclass(frozen=True, kw_only=False)
class Thesis:
    value: Answer | Version | Clarification | Atom | FundamentalAtom | Number


@dataclass(frozen=False, kw_only=True)
class Parser:
    clarification_delimiter: str = "."
    version_delimiter: str = "-"
    answer_delimiter: str = "/"

    def __post_init__(self):
        fundamental_root = pp.Combine(pp.Char(pp.alphas.upper())[1, ...]).set_parse_action(
            lambda x: FundamentalRoot(str(x[0]))
        )
        root = pp.Combine(pp.Char(pp.alphas.lower())[1, ...]).set_parse_action(lambda x: Root(str(x[0])))
        number = pp.Combine(pp.Char(pp.nums)[1, ...]).set_parse_action(lambda x: Number(int(str(x[0]))))
        fundamental_atom = (fundamental_root + pp.Opt(number)).set_parse_action(lambda x: FundamentalAtom(*x.as_list()))
        atom = (root + pp.Opt(number)).set_parse_action(lambda x: Atom(*x.as_list()))

        clarification_delimiter = pp.Char(self.clarification_delimiter).suppress()
        clarification = (
            (atom | fundamental_atom)
            + clarification_delimiter
            + pp.DelimitedList(atom | number, clarification_delimiter)
        ).set_parse_action(lambda x: Clarification(x.as_list()))

        version_delimiter = pp.Char(self.version_delimiter).suppress()
        version = (
            (clarification | atom | fundamental_atom)
            + version_delimiter
            + pp.DelimitedList(atom | number, version_delimiter)
        ).set_parse_action(lambda x: Version(x.as_list()))

        answer_delimiter = pp.Char(self.answer_delimiter).suppress()
        answer_element = version | clarification | atom | fundamental_atom
        answer = pp.DelimitedList(answer_element, answer_delimiter, min=2).set_parse_action(
            lambda x: Answer(x.as_list())
        )

        thesis = (answer | version | clarification | fundamental_atom).set_parse_action(
            lambda x: Thesis(x.as_list()[0])
        )
        self.parser = thesis

    def parse(self, s: str):
        return self.parser.parse_string(s)[0]


@pytest.fixture
@functools.cache
def parser():
    return Parser()


def test_fundamental_atom(parser: Parser):
    assert parser.parse("ABC1234") == Thesis(FundamentalAtom(FundamentalRoot("ABC"), Number(1234)))
    assert parser.parse("ABC") == Thesis(FundamentalAtom(FundamentalRoot("ABC")))


def test_clarification(parser: Parser):
    assert parser.parse("A2.b1") == Thesis(
        Clarification([FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b"), Number(1))])
    )
    assert parser.parse("A2.b") == Thesis(
        Clarification([FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b"))])
    )
    assert parser.parse("A2.b.c") == Thesis(
        Clarification([FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b")), Atom(Root("c"))])
    )


def test_version(parser: Parser):
    assert parser.parse("A2.b-c") == Thesis(
        Version([Clarification([FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b"))]), Atom(Root("c"))])
    )


def test_answer(parser: Parser):
    assert parser.parse("A2.b-c/D") == Thesis(
        Answer(
            [
                Version(
                    [
                        Clarification([FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b"))]),
                        Atom(Root("c")),
                    ]
                ),
                FundamentalAtom(FundamentalRoot("D")),
            ]
        )
    )
