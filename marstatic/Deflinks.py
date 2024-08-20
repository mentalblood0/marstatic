import colorsys
import functools
import itertools
import re
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Def:
    id: int
    name: str
    shift: float
    depth: float

    @functools.cached_property
    def color(self):
        return "#%02x%02x%02x" % tuple(
            int(255 * i) for i in colorsys.hsv_to_rgb(self.shift, max(0.15, 0.8 - self.depth), max(0.78, self.depth))
        )

    @functools.cached_property
    def css_class(self):
        return f"d{self.id}"

    @functools.cached_property
    def css(self):
        return {"class": self.css_class, "color": self.color}


@dataclass(frozen=True, kw_only=False)
class Defs:
    regex = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:*")

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

    @functools.cached_property
    def depth(self):
        return max(self.depth_of(n) for n in self.names)

    def depth_of(self, name: str):
        return name.count("/") + name.count(".")

    def __len__(self):
        return len(self.names)

    def __getitem__(self, key: int):
        name = self.names[key]
        return Def(id=key, name=name, shift=key / len(self), depth=self.depth_of(name) / self.depth)

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
