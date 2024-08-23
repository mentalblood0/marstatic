import typing
from dataclasses import dataclass

import pyparsing as pp


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


@dataclass(init=False)
class Tuple[T]:
    value: tuple[T, ...]

    def __init__(self, *args: T):
        self.value = tuple(args)

    def __hash__(self):
        return hash(self.value)


class Clarification(Tuple[typing.Union["Answer", Atom, FundamentalAtom, Number]]): ...


class Version(Tuple[Clarification | Atom | FundamentalAtom | Number]): ...


class Answer(Tuple[Version | Clarification | Atom | FundamentalAtom | Number]): ...


@dataclass(frozen=True, kw_only=False)
class Thesis:
    value: Answer | Version | Clarification | Atom | FundamentalAtom | Number


@dataclass(frozen=False, kw_only=True)
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
            .set_parse_action(lambda x: FundamentalRoot(str(x[0])))
            .set_name("fundamental root")
        )
        root = (
            pp.Combine(pp.Char(pp.alphas.lower())[1, ...]).set_parse_action(lambda x: Root(str(x[0]))).set_name("root")
        )
        number = (
            pp.Combine(pp.Char(pp.nums)[1, ...]).set_parse_action(lambda x: Number(int(str(x[0])))).set_name("number")
        )
        fundamental_atom = (
            (fundamental_root + pp.Opt(number))
            .set_parse_action(lambda x: FundamentalAtom(*x.as_list()))
            .set_name("fundamental atom")
        )
        atom = (root + pp.Opt(number)).set_parse_action(lambda x: Atom(*x.as_list())).set_name("atom")

        clarification_delimiter = pp.Char(self.clarification_delimiter).suppress()
        clarification = pp.Forward().set_name("clarification")

        version_delimiter = pp.Char(self.version_delimiter).suppress()
        version = (
            (
                (clarification | atom | fundamental_atom)
                + version_delimiter
                + pp.DelimitedList(atom | number, version_delimiter)
            )
            .set_parse_action(lambda x: Version(*x.as_list()))
            .set_name("version")
        )

        answer_delimiter = pp.Char(self.answer_delimiter).suppress()
        answer_element = b(version) | b(clarification) | atom | fundamental_atom
        answer = (
            pp.DelimitedList(answer_element, answer_delimiter, min=2)
            .set_parse_action(lambda x: Answer(*x.as_list()))
            .set_name("answer")
        )

        clarification <<= (
            (b(answer) | atom | fundamental_atom)
            + clarification_delimiter
            + pp.DelimitedList(atom | number, clarification_delimiter)
        ).set_parse_action(lambda x: Clarification(*x.as_list()))

        self.thesis = (
            (answer | version | clarification | fundamental_atom)
            .set_parse_action(lambda x: Thesis(x.as_list()[0]))
            .set_name("thesis")
        )

    def parse(self, s: str):
        return self.thesis.parse_string(s, parse_all=True)[0]
