import functools

import pytest
from pytest_benchmark import fixture

from ..TsidParser import (
    Answer,
    Atom,
    Clarification,
    FundamentalAtom,
    FundamentalRoot,
    Number,
    Root,
    Thesis,
    TsidParser,
    Version,
)


@pytest.fixture
@functools.cache
def parser():
    return TsidParser()


def test_fundamental_atom(parser: TsidParser):
    assert parser.parse("ABC1234") == Thesis(FundamentalAtom(FundamentalRoot("ABC"), Number(1234)))
    assert parser.parse("ABC") == Thesis(FundamentalAtom(FundamentalRoot("ABC")))


def test_clarification(parser: TsidParser):
    assert parser.parse("A2.b1") == Thesis(
        Clarification(FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b"), Number(1)))
    )
    assert parser.parse("A2.b") == Thesis(
        Clarification(FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b")))
    )
    assert parser.parse("A2.b.c") == Thesis(
        Clarification(FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b")), Atom(Root("c")))
    )
    assert parser.parse("A2.1.2") == Thesis(
        Clarification(FundamentalAtom(FundamentalRoot("A"), Number(2)), Number(1), Number(2))
    )


def test_version(parser: TsidParser):
    assert parser.parse("A2.b-c") == Thesis(
        Version(Clarification(FundamentalAtom(FundamentalRoot("A"), Number(2)), Atom(Root("b"))), Atom(Root("c")))
    )


def test_answer(parser: TsidParser):
    assert parser.parse("A/(B.1)") == Thesis(
        Answer(FundamentalAtom(FundamentalRoot("A")), Clarification(FundamentalAtom(FundamentalRoot("B")), Number(1)))
    )
    assert parser.parse("(A/B).1") == Thesis(
        Clarification(Answer(FundamentalAtom(FundamentalRoot("A")), FundamentalAtom(FundamentalRoot("B"))), Number(1))
    )


def test_benchmark_parse(benchmark: fixture.BenchmarkFixture, parser: TsidParser):
    benchmark(lambda: parser.parse("(A2.b-c)/D"))
