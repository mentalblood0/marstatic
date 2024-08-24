import functools

import pytest
from pytest_benchmark import fixture

from ..TsidParser import T, TsidParser


@pytest.fixture
@functools.cache
def parser():
    return TsidParser()


def test_fundamental_atom(parser: TsidParser):
    assert parser.parse("ABC1234") == T(T.A(T.R("ABC"), T.N(1234)))
    assert parser.parse("ABC") == T(T.A(T.R("ABC")))


def test_clarification(parser: TsidParser):
    assert parser.parse("A2.b1") == T(T.C(T.A(T.R("A"), T.N(2)), T.a(T.r("b"), T.N(1))))
    assert parser.parse("A2.b") == T(T.C(T.A(T.R("A"), T.N(2)), T.a(T.r("b"))))
    assert parser.parse("A2.b.c") == T(T.C(T.A(T.R("A"), T.N(2)), T.a(T.r("b")), T.a(T.r("c"))))
    assert parser.parse("A2.1.2") == T(T.C(T.A(T.R("A"), T.N(2)), T.N(1), T.N(2)))


def test_version(parser: TsidParser):
    assert parser.parse("A2.b-c") == T(T.V(T.C(T.A(T.R("A"), T.N(2)), T.a(T.r("b"))), T.a(T.r("c"))))
    assert parser.parse("(R-r).1") == T(T.C(T.V(T.A(T.R("R")), T.a(T.r("r"))), T.N(1)))


def test_answer(parser: TsidParser):
    assert parser.parse("A/(B.1)") == T(T.Ans(T.A(T.R("A")), T.C(T.A(T.R("B")), T.N(1))))
    assert parser.parse("(A/B).1") == T(T.C(T.Ans(T.A(T.R("A")), T.A(T.R("B"))), T.N(1)))
    assert parser.parse("((A1.1.2)/(R-r4)).1") == T(
        T.C(T.Ans(T.C(T.A(T.R("A"), T.N(1)), T.N(1), T.N(2)), T.V(T.A(T.R("R")), T.a(T.r("r"), T.N(4)))), T.N(1))
    )


@pytest.mark.parametrize(
    "e,out",
    [
        (
            "((A3.2)/(R-r)/A/(R-r)).1",
            T.C(
                T.Ans(
                    T.C(T.A(T.R("A"), T.N(3)), T.N(2)),
                    T.V(T.A(T.R("R")), T.a(T.r("r"))),
                    T.A(T.R("A")),
                    T.V(T.A(T.R("R")), T.a(T.r("r"))),
                ),
                T.N(1),
            ),
        ),
        ("A0", T.A(T.R("A"), T.N(0))),
        ("A0.0", T.C(T.A(T.R("A"), T.N(0)), T.N(0))),
        ("A0.s", T.C(T.A(T.R("A"), T.N(0)), T.a(T.r("s")))),
        ("A0.n", T.C(T.A(T.R("A"), T.N(0)), T.a(T.r("n")))),
        ("A0/(R-r)", T.Ans(T.A(T.R("A"), T.N(0)), T.V(T.A(T.R("R")), T.a(T.r("r"))))),
        ("A1", T.A(T.R("A"), T.N(1))),
        ("A1.1", T.C(T.A(T.R("A"), T.N(1)), T.N(1))),
        ("A1.1.1", T.C(T.A(T.R("A"), T.N(1)), T.N(1), T.N(1))),
        ("(A1.1.1)/(R-r)", T.Ans(T.C(T.A(T.R("A"), T.N(1)), T.N(1), T.N(1)), T.V(T.A(T.R("R")), T.a(T.r("r"))))),
        ("A1.1.2", T.C(T.A(T.R("A"), T.N(1)), T.N(1), T.N(2))),
        (
            "((A1.1.2)/(R-r)).1",
            T.C(T.Ans(T.C(T.A(T.R("A"), T.N(1)), T.N(1), T.N(2)), T.V(T.A(T.R("R")), T.a(T.r("r")))), T.N(1)),
        ),
    ],
)
def test_realistic(parser: TsidParser, e: str, out: T.A | T.a | T.Ans | T.V | T.C):
    assert parser.parse(e) == T(out)


def test_benchmark_parse(benchmark: fixture.BenchmarkFixture, parser: TsidParser):
    benchmark(lambda: parser.parse("((A1.1.2)/(R-r4)).1"))
