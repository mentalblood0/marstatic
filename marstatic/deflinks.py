import colorsys
import functools
import itertools
import re
from dataclasses import dataclass

from .TsidParser import TsidParser

tsid_parser = TsidParser()


@dataclass(frozen=True, kw_only=True)
class Def:
    id: int
    name: str
    shift: float

    @functools.cached_property
    def parsed(self):
        return tsid_parser.parse(self.name)

    @functools.cached_property
    def atoms(self):
        pass

    @functools.cached_property
    def color(self):
        return "#%02x%02x%02x" % tuple(int(255 * i) for i in colorsys.hsv_to_rgb(self.shift, 0.35, 0.78))

    @functools.cached_property
    def css_class(self):
        return f"d{self.id}"

    @functools.cached_property
    def css(self):
        return {"class": self.css_class, "color": self.color}


@dataclass(frozen=True, kw_only=False)
class Defs:
    regex = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:?")

    lines: list[str]

    @functools.cached_property
    def names(self):
        return sorted(
            set(m.group(1) for m in itertools.chain.from_iterable(re.finditer(self.regex, l) for l in self.lines))
        )

    @functools.cached_property
    def by_name(self):
        return {d: self[i] for i, d in enumerate(self.names)}

    @functools.cached_property
    def colors_classes(self):
        return [d.css for d in self.by_name.values()]

    def __len__(self):
        return len(self.names)

    def __getitem__(self, key: int):
        return Def(id=key, name=self.names[key], shift=key / len(self))

    def __iter__(self):
        for i in range(len(self.names)):
            return self[i]


@dataclass(frozen=False, kw_only=False)
class Replacer:
    lines: list[str]

    def __post_init__(self):
        self.defs = Defs(self.lines)

    def replace(self, m: re.Match):
        d = self.defs.by_name[m.group(1)]
        if m.group(0).endswith(":"):
            return f'<span class="def {d.css_class}">&nbsp;**{d.name}**&nbsp;</span><a name="{d.id}"></a>:'
        else:
            return f'<span class="link {d.css_class}">&nbsp;**[{d.name}](#{d.id})**&nbsp;</span>'

    @property
    def result(self):
        return "\n".join(re.sub(self.defs.regex, self.replace, l) for l in self.lines)

    @classmethod
    def from_input(cls, input: str):
        return cls(input.splitlines())
