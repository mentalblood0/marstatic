import colorsys
import functools
import itertools
import re
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Def:
    id: int
    name: str
    color: str

    @functools.cached_property
    def css_class(self):
        return f"d{self.id}"

    @functools.cached_property
    def css(self):
        return {"class": self.css_class, "color": self.color}


@dataclass(frozen=True, kw_only=False)
class Defs:
    regex = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:*")

    by_name: dict[str, Def]

    @classmethod
    def color(cls, target: int, overall: int):
        return "#%02x%02x%02x" % tuple(int(255 * i) for i in colorsys.hsv_to_rgb(target / overall, 0.34, 0.78))

    @functools.cached_property
    def colors_classes(self):
        return [d.css for d in self.by_name.values()]

    @classmethod
    def from_defs_names(cls, defs_names: set[str]):
        return cls(
            {d: Def(id=i, name=d, color=cls.color(i, len(defs_names))) for i, d in enumerate(sorted(defs_names))}
        )

    @classmethod
    def from_lines(cls, lines: list[str]):
        return cls.from_defs_names(
            set(m.group(1) for m in itertools.chain.from_iterable(re.finditer(cls.regex, l) for l in lines))
        )


@dataclass(frozen=False, kw_only=False)
class Replacer:
    lines: list[str]

    def __post_init__(self):
        self.defs = Defs.from_lines(self.lines)

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
