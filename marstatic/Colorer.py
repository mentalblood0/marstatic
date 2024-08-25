import colorsys
import dataclasses
import functools
import itertools
import re
import typing

from marstatic.TsidParser import T, TsidParser

tsid_parser = TsidParser()


@dataclasses.dataclass(frozen=True, kw_only=False)
class Color:
    h: float
    s: float
    v: float
    alpha: float = 1

    def saturated(self, c: float):
        return dataclasses.replace(self, s=self.s * c)

    def transpared(self, alpha: float):
        return dataclasses.replace(self, alpha=alpha)

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
        return f"rgba({self.r}, {self.g}, {self.b}, {self.alpha})"

    @classmethod
    def from_shift(cls, shift: float):
        return cls(shift, 0.35, 0.78)

    @classmethod
    def transparent(cls):
        return cls(0, 0, 0, 0)


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
    padding: int = 1

    def __len__(self):
        return len(self.text_to_render)

    @functools.cached_property
    def text_to_render(self):
        return " " * self.padding + self.text.strip("()"[0]).replace("(", " ").replace(")", " ") + " " * self.padding

    @functools.cached_property
    def shift(self):
        return self.padding - self.text.find(self.text_to_render[self.padding])

    def sshift(self, segment_point: float | int):
        return f"{round((segment_point + self.shift) / len(self) * 100, 2)}%"

    def css(self, i: int | None = None):
        if i is None:
            if len(self.segments) == 1:
                return (
                    f"linear-gradient(90deg, "
                    f"{self.segments[0].color.css} {self.sshift(self.padding - self.shift)}, "
                    f"{self.segments[0].color.css} {self.sshift(len(self) - self.padding-self.shift)}"
                    ")"
                )
            return f"linear-gradient(90deg, " + ", ".join(self.css(i) for i in range(len(self.segments))) + ")"
        if isinstance(i, int):
            s = self.segments[i]
            result = ""
            # if i != 0:
            #     p = self.segments[i - 1]
            #     result += f"{Color.transparent().css} {self.sshift((p.end + s.start) / 2)}, "
            result += f"{s.color.css} {self.sshift(s.start)}, {s.color.css} {self.sshift(s.end)}"
            # if i != len(self.segments) - 1:
            #     n = self.segments[i + 1]
            #     result += f", {Color.transparent().css} {self.sshift((s.end + n.start) / 2)}"
            return result

    def html(self, c: str):
        return f"<span class='link {c}'>{self.text_to_render.replace(' ', '&nbsp;')}</span>"


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

    @functools.cached_property
    def number_by_tsid(self):
        return {r.value: i for i, r in enumerate(sorted(self.tsids))}

    def replace(self, m: re.Match):
        e = m.group(1)
        return self.colored(e).html(f"i{self.number_by_tsid[e]}") + (":" if m.group(0)[-1] == ":" else "")

    @functools.cached_property
    def css(self):
        return [
            {"class": f"i{self.number_by_tsid[t.value]}", "background": self.colored(t.value).css()} for t in self.tsids
        ]

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
            result = self.colored(o.first) + [(o.other[-1].loc, self.colorspace(o.first).color(o))]
        elif isinstance(o, T.C):
            first = self.colored(o.first)
            result = first + [(c.loc, first[-1][1].saturated(0.57 ** (i + 1))) for i, c in enumerate(o.other)]
        elif isinstance(o, T.Ans):
            result = [self.colored(o.first)]
            for a in o.other:
                result += self.colored(a)
        return self.flatten(result)

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
