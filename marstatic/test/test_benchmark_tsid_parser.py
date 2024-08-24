from pytest_benchmark import fixture

from ..TsidParser import TsidParser


def test_benchmark_parse(benchmark: fixture.BenchmarkFixture, parser: TsidParser):
    benchmark(lambda: parser.parse("((A1.1.2)/(R-r)).4.1"))
