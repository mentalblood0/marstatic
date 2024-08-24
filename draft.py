import colorsys
import dataclasses
import functools
import itertools
import pathlib
import re
import typing

from marstatic.TsidParser import T, TsidParser

tsid_parser = TsidParser()


@dataclasses.dataclass(frozen=True, kw_only=False)
class Color:
    h: float
    s: float
    v: float

    def saturated(self, c: float):
        return dataclasses.replace(self, s=self.s * c)

    @functools.cached_property
    def rgb(self):
        return tuple(int(255 * i) for i in colorsys.hsv_to_rgb(self.h, self.s, self.v))

    @classmethod
    def from_shift(cls, shift: float):
        return cls(shift, 0.35, 0.78)


def fundamental_roots(o: T | T.Ans | T.V | T.C | T.a | T.A | T.N):
    if isinstance(o, T):
        return fundamental_roots(o.value)
    if isinstance(o, T.Ans | T.V | T.C):
        return {r for pattern in o.value for r in fundamental_roots(pattern)}
    if isinstance(o, T.A):
        return {o.root}
    return set()


def versions(o: T | T.Ans | T.V | T.C | T.a | T.A | T.N):
    if isinstance(o, T):
        return versions(o.value)
    if isinstance(o, T.Ans):
        return {r for pattern in o.value for r in versions(pattern)}
    if isinstance(o, T.V):
        return {o}
    return set()


@dataclasses.dataclass(frozen=True, kw_only=False)
class Tsid:
    value: str

    @functools.cached_property
    def parsed(self):
        return tsid_parser.parse(self.value)

    @functools.cached_property
    def fundamental_roots(self):
        return fundamental_roots(self.parsed)

    @functools.cached_property
    def versions(self):
        return versions(self.parsed)

    def __lt__(self, o: object):
        if isinstance(o, Tsid):
            return self.value < o.value
        raise ValueError(f"{self} < {o}")


@dataclasses.dataclass(frozen=True, kw_only=False)
class Colorspace:
    members: set[T.R]

    def __len__(self):
        return len(self.members)

    @functools.cached_property
    def number_by_value(self):
        return {r.value: i for i, r in enumerate(sorted(self.members, key=lambda r: r.value))}

    def color(self, o: T.R | T.A):
        if isinstance(o, T.R):
            return Color.from_shift(self.number_by_value[o.value] / len(self))
        if isinstance(o, T.A):
            return Color.from_shift(self.number_by_value[o.root.value] / len(self))


@dataclasses.dataclass(frozen=True, kw_only=False)
class VersionColorspace:
    First = T.V.First | T.V

    first: First
    members: set[T.V.Other]

    def __len__(self):
        return len(self.members)

    @functools.cached_property
    def number_by_value(self):
        return {r.value: i for i, r in enumerate(sorted(self.members, key=lambda r: r.value))}

    def color(self, o: T.V):
        return Color.from_shift(self.number_by_value[o.value[-1].value] / len(self))


@dataclasses.dataclass(frozen=True, kw_only=False)
class Colorer:
    tsid_heuristic = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:?")

    tsids: set[Tsid]

    @functools.cached_property
    def fundamental_roots(self):
        return {r for t in self.tsids for r in t.fundamental_roots}

    @functools.cached_property
    def versions(self):
        return {r for t in self.tsids for r in t.versions}

    @typing.overload
    def colorspace(self, first: None = None) -> Colorspace: ...
    @typing.overload
    def colorspace(self, first: VersionColorspace.First) -> VersionColorspace: ...
    def colorspace(self, first: VersionColorspace.First | None = None):
        if first is None:
            return Colorspace(self.fundamental_roots)
        elif isinstance(first, VersionColorspace.First):
            return VersionColorspace(first, {o for v in self.versions if v.first == first for o in v.other})

    def flatten(self, l: list):
        result = []
        for e in l:
            if isinstance(e, tuple):
                result.append(e)
            elif isinstance(e, list):
                result += self.flatten(e)
        return result

    def color(self, o: T.R | T.A | T.V | T.C | T.r):
        result = []
        if isinstance(o, T.R | T.A):
            result = [(o, self.colorspace().color(o))]
        elif isinstance(o, T.V):
            result = self.color(o.value[0]) + [(o.value[-1], self.colorspace(o.value[0]).color(o))]
        elif isinstance(o, T.C):
            first = self.color(o.first)
            result = first + [(c, first[-1][1].saturated(0.9 ** (i + 1))) for i, c in enumerate(o.other)]
        return self.flatten(result)

    @functools.cached_property
    def tsid_by_name(self):
        return {t.value: t for t in self.tsids}

    def __getitem__(self, key: str):
        return self.tsid_by_name[key]

    @classmethod
    def from_lines(cls, lines: list[str]):
        return cls(
            {Tsid(m.group(1)) for m in itertools.chain.from_iterable(re.finditer(cls.tsid_heuristic, l) for l in lines)}
        )

    @classmethod
    def from_text(cls, text: str):
        return cls.from_lines(text.splitlines())


c = Colorer.from_text(pathlib.Path("example_source.md").read_text(encoding="utf8"))
# for t in sorted(c.tsids):
#     print(f'("{t.value}", ),')
# print(c.fundamental_roots)
# print(c.versions)
# print(c.color(tsid_parser.parse("R1").value))
# print(c.color(tsid_parser.parse("R-a").value))
# print(c.color(tsid_parser.parse("A1.1.2").value))
print(c.color(tsid_parser.parse("(R-r).0").value))
