import colorsys
import functools
import itertools
import pathlib
import re
from dataclasses import dataclass

from marstatic.TsidParser import (
    Answer,
    Atom,
    Clarification,
    FundamentalAtom,
    FundamentalRoot,
    Number,
    Thesis,
    TsidParser,
    Version,
)

tsid_parser = TsidParser()


def color(n: int, N: int):
    return tuple(int(255 * i) for i in colorsys.hsv_to_rgb(n / N, 0.35, 0.78))


def fundamental_roots(o: Thesis | Answer | Version | Clarification | Atom | FundamentalAtom | Number):
    if isinstance(o, Thesis):
        return fundamental_roots(o.value)
    if isinstance(o, Answer | Version | Clarification):
        return {r for pattern in o.value for r in fundamental_roots(pattern)}
    if isinstance(o, FundamentalAtom):
        return {o.root}
    return set()


def versions(o: Thesis | Answer | Version | Clarification | Atom | FundamentalAtom | Number):
    if isinstance(o, Thesis):
        return versions(o.value)
    if isinstance(o, Answer):
        return {r for pattern in o.value for r in versions(pattern)}
    if isinstance(o, Version):
        return {o}
    return set()


@dataclass(frozen=True, kw_only=False)
class Tsid:
    value: str

    @functools.cached_property
    def parsed(self):
        result = tsid_parser.parse(self.value)
        if not isinstance(result, Thesis):
            raise ValueError
        return result

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


@dataclass(frozen=True, kw_only=False)
class Colorspace:
    members: set[FundamentalRoot]

    def __len__(self):
        return len(self.members)

    @functools.cached_property
    def number_by_value(self):
        return {r.value: i for i, r in enumerate(sorted(self.members, key=lambda r: r.value))}

    def color(self, root_value: str):
        return color(self.number_by_value[root_value], len(self))


@dataclass(frozen=True, kw_only=False)
class Colorer:
    tsid_heuristic = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:?")

    tsids: set[Tsid]

    @functools.cached_property
    def fundamental_roots(self):
        return {r for t in self.tsids for r in t.fundamental_roots}

    @functools.cached_property
    def versions(self):
        return {r for t in self.tsids for r in t.versions}

    @functools.cached_property
    def colorspace(self):
        return Colorspace(self.fundamental_roots)

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
print(c.fundamental_roots)
# print(c.versions)
# print(c.colorspace.color("A"))
