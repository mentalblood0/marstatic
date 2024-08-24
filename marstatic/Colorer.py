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

    @property
    def r(self):
        return self.rgb[0]

    @property
    def g(self):
        return self.rgb[1]

    @property
    def b(self):
        return self.rgb[2]

    @property
    def css(self):
        return f"rgba({self.r}, {self.g}, {self.b}, 1)"

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
    if isinstance(o, T.Ans | T.C):
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
class ColoredSegment:
    start: int
    end: int
    color: Color


@dataclasses.dataclass(frozen=True, kw_only=False)
class Colored:
    text: str
    segments: list[ColoredSegment]

    def __len__(self):
        return self.segments[-1].end + 2

    @functools.cached_property
    def css(self):
        if len(self.segments) == 1:
            return f"background: {self.segments[0].color.css}"
        return (
            "background: linear-gradient(90deg, "
            + ", ".join(f"{s.color.css} {(s.start + 2) / len(self) * 100}%" for s in self.segments)
            + ");"
        )

    @property
    def html(self):
        return f"<span class='link' style='{self.css}'>&nbsp;{self.text}&nbsp;</span>"


@dataclasses.dataclass(frozen=True, kw_only=False)
class Colorer:
    tsid_heuristic = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:?")

    lines: list[str] = dataclasses.field(repr=False)
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

    def replace(self, m: re.Match):
        e = m.group(1)
        return self.colored(e).html + (":" if m.group(0)[-1] == ":" else "")

    @typing.overload
    def colored(self, o: str) -> Colored: ...
    @typing.overload
    def colored(self, o: T.R | T.A | T.V | T.C | T.r | T.Ans | T.N | T) -> list[tuple[tuple[int, int], Color]]: ...
    @typing.overload
    def colored(self, o: None = None) -> str: ...
    def colored(self, o: T.R | T.A | T.V | T.C | T.r | T.Ans | T.N | str | T | None = None):
        if o is None:
            return "\n".join(re.sub(self.tsid_heuristic, self.replace, l) for l in self.lines)
        if isinstance(o, str):
            return Colored(o, [ColoredSegment(c[0][0], c[0][1], c[1]) for c in self.colored(tsid_parser.parse(o))])
        if isinstance(o, T):
            return self.colored(o.value)
        result = []
        if isinstance(o, T.R | T.A):
            result = [(o.loc, self.colorspace().color(o))]
        elif isinstance(o, T.V):
            result = self.colored(o.value[0]) + [(o.value[-1].loc, self.colorspace(o.value[0]).color(o))]
        elif isinstance(o, T.C):
            first = self.colored(o.first)
            result = first + [(c.loc, first[-1][1].saturated(0.57 ** (i + 1))) for i, c in enumerate(o.other)]
        elif isinstance(o, T.Ans):
            result = [self.colored(o.first)]
            for a in o.other:
                result += self.colored(a)
        return self.flatten(result)

    @functools.cached_property
    def tsid_by_name(self):
        return {t.value: t for t in self.tsids}

    def __getitem__(self, key: str):
        return self.tsid_by_name[key]

    @classmethod
    def from_lines(cls, lines: list[str]):
        return cls(
            lines,
            {
                Tsid(m.group(1))
                for m in itertools.chain.from_iterable(re.finditer(cls.tsid_heuristic, l) for l in lines)
            },
        )

    @classmethod
    def from_text(cls, text: str):
        return cls.from_lines(text.splitlines())
