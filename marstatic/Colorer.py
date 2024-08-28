import colorsys
import dataclasses
import functools
import hashlib
import itertools
import re
import typing

from marstatic.TsidParser import T, TsidParser

tsid_parser = TsidParser()


@dataclasses.dataclass(frozen=True, kw_only=False)
class Color:
    salt = b""
    s_limits = (0, 1)
    v_limits = (0, 1)

    h: float
    s: float
    v: float

    def saturated(self, c: float):
        return dataclasses.replace(self, s=self.s * c)

    @property
    def css(self):
        return "#%02x%02x%02x" % tuple(int(255 * i) for i in colorsys.hsv_to_rgb(self.h, self.s, self.v))

    @classmethod
    def from_value(cls, value: str):
        digest = hashlib.blake2b(value.encode(), digest_size=4, salt=cls.salt).digest()
        return cls(
            int.from_bytes(digest[:2]) / 2**16,
            cls.s_limits[0] + int.from_bytes([digest[2]]) / 2**8 * (cls.s_limits[1] - cls.s_limits[0]),
            cls.v_limits[0] + int.from_bytes([digest[3]]) / 2**8 * (cls.v_limits[1] - cls.v_limits[0]),
        )


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
        return " " * self.padding + self.text.strip("()").replace("(", " ").replace(")", " ") + " " * self.padding

    @functools.cached_property
    def shift(self):
        return self.padding - self.text.find(self.text_to_render[self.padding])

    def sshift(self, segment_point: float | int):
        return f"{round((segment_point + self.shift) / len(self) * 100, 2)}%"

    def css(self, i: int | None = None):
        if i is None:
            if len(self.segments) == 1:
                return self.segments[0].color.css
            return f"linear-gradient(90deg," + ",".join(self.css(i) for i in range(len(self.segments))) + ")"
        if isinstance(i, int):
            s = self.segments[i]
            return f"{s.color.css} {self.sshift(s.start)},{s.color.css} {self.sshift(s.end)}"

    def html(self, c: str, link: bool):
        additional = f"href='#{c}'" if link else f"href='#{c}'id='{c}'"
        return f"<a class='link {c}'{additional}>{self.text_to_render.replace(' ', '&nbsp;')}</a>"


@dataclasses.dataclass(frozen=True, kw_only=False)
class Colorer:

    default_tsid_heuristic = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:?")

    text: str
    tsid_heuristic: re.Pattern[str] = default_tsid_heuristic

    @functools.cached_property
    def lines(self):
        return self.text.splitlines()

    @functools.cached_property
    def tsids(self):
        return {
            m.group(1): f"i{i}"
            for i, m in enumerate(
                itertools.chain.from_iterable(re.finditer(self.tsid_heuristic, l) for l in self.lines)
            )
        }

    def color(self, o: T.A | T.R | T.V):
        if isinstance(o, T.R):
            value = o.value
        elif isinstance(o, T.A):
            value = o.root.value
        elif isinstance(o, T.V):
            value = str(o.value[-1].value)
        return Color.from_value(value)

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
        return self.colored(e).html(self.tsids[e], link=not m.group(0).endswith(":")) + (
            ":" if m.group(0)[-1] == ":" else ""
        )

    @functools.cached_property
    def css(self):
        return sorted(
            [{"class": i, "background": self.colored(t).css()} for t, i in self.tsids.items()], key=lambda c: c["class"]
        )

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

        if isinstance(o, T.R | T.A):
            return [(o.loc, self.color(o))]

        elif isinstance(o, T.V):
            result = self.colored(o.first)
            for i in range(len(o.other)):
                oo = o.other[i]
                if oo.loc is None:
                    raise ValueError(f"{oo} loc is {oo.loc}")
                result.append((oo.loc, self.color(T.V(o.first, *o.other[: i + 1]))))
            return result

        elif isinstance(o, T.C):
            first = self.colored(o.first)
            return first + [(c.loc, first[-1][1].saturated(0.57 ** (i + 1))) for i, c in enumerate(o.other)]

        elif isinstance(o, T.Ans):
            return self.flatten([self.colored(o.first)] + [self.colored(a) for a in o.other])
