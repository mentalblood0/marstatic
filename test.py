import contextlib
import functools
import re
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=False)
class Element:
    source: str
    regex: re.Pattern[str]

    def __post_init__(self):
        if re.fullmatch(self.regex, self.source) is None:
            raise ValueError(self)

    def __eq__(self, o: object):
        if isinstance(o, str):
            return self.source == o
        if isinstance(o, Element):
            return self.source == Element.source
        return False

    @staticmethod
    def detect(s: str):
        for c in [Atom, Version, Answer]:
            with contextlib.suppress(ValueError):
                return c(s)
        raise ValueError(s)


@dataclass(frozen=True, kw_only=False)
class Atom(Element):
    fundamental_root_regex = re.compile(r"[A-Z]+")
    root_regex = re.compile(r"[A-Za-z]+")
    part_regex = re.compile(r"\d*")
    default_regex = re.compile(root_regex.pattern + part_regex.pattern)

    regex: re.Pattern[str] = default_regex

    @functools.cached_property
    def fundamental(self):
        return bool(re.search(self.fundamental_root_regex, self.source))

    @functools.cached_property
    def root(self):
        result = re.search(self.root_regex, self.source)
        if not result:
            raise ValueError(self)
        return Atom(result.group(0))

    @functools.cached_property
    def part(self):
        if result := re.search(r"\d+", self.source):
            return int(result.group(0))

    def __eq__(self, o: object):
        return super().__eq__(o)


@dataclass(frozen=True, kw_only=False)
class Version(Element):
    default_regex = re.compile(f"{Atom.default_regex.pattern}(?:\\.{Atom.default_regex.pattern})+")

    regex: re.Pattern[str] = default_regex

    @functools.cached_property
    def parsed(self):
        return [Element.detect(s) for s in self.source.split(".")]

    def __eq__(self, o: object):
        return super().__eq__(o)


@dataclass(frozen=True, kw_only=False)
class Answer(Element):
    default_regex = re.compile(
        f"(?:{Atom.default_regex.pattern})|(?:{Version.default_regex.pattern})(?:(?:-|\\.)(?:{Atom.default_regex.pattern})|(?:{Version.default_regex.pattern}))+"
    )

    regex: re.Pattern[str] = default_regex

    @functools.cached_property
    def parsed(self):
        return [Element.detect(s) for s in self.source.split("-")]

    def __eq__(self, o: object):
        return super().__eq__(o)


@dataclass(frozen=True, kw_only=False)
class Def:
    source: str

    @functools.cached_property
    def parsed(self):
        return [Element.detect(s) for s in self.source.split("/")]

    def __eq__(self, o: object):
        return super().__eq__(o)


def is_element(o: Answer | Version | Atom, t: type[Answer] | type[Version] | type[Atom], s: str):
    assert isinstance(o, t)
    assert o == s


def test_basic():
    d = Def("A2.b-c/D")

    is_element(d.parsed[0], Answer, "A2.b-c")
    is_element(d.parsed[1], Atom, "D")
    is_element(d.parsed[0].parsed[0], Version, "A2.b")
    is_element(d.parsed[0].parsed[1], Atom, "c")
    is_element(d.parsed[0].parsed[0].parsed[0], Atom, "A2")
    is_element(d.parsed[0].parsed[0].parsed[1], Atom, "b")

    a = d.parsed[0].parsed[0].parsed[0]
    is_element(a.root, Atom, "A")
    assert a.part == 2
