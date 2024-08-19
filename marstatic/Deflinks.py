import colorsys
import functools
import re
from dataclasses import dataclass

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class Deflinks(Extension):
    def extendMarkdown(self, md: Markdown):
        md.registerExtension(self)
        md.preprocessors.register(DeflinksPreprocessor(), "deflinks", 100)


@dataclass(frozen=True, kw_only=False)
class Replacer:
    deflink_regex = re.compile(r"\*\*([^А-Яа-я]+?)\*\*:*")

    lines: list[str]

    def color(self, target: int, overall: int):
        return "#%02x%02x%02x" % tuple(int(255 * i) for i in colorsys.hsv_to_rgb(target * 1 / overall, 0.34, 0.78))

    @functools.cached_property
    def defs(self):
        return set(m.group(1) for m in re.finditer(self.deflink_regex, "\n".join(self.lines)))

    @functools.cached_property
    def defs_colors(self):
        return {d: self.color(i, len(self.defs)) for i, d in enumerate(sorted(self.defs))}

    def replace(self, m: re.Match):
        g = m.group(1)
        if m.group(0).endswith(":"):
            return f'<span class="def" style="background-color:{self.defs_colors[g]}">&nbsp;**{g}**&nbsp;</span><a name="{g}"></a>:'
        else:
            return (
                f'<span class="link" style="background-color:{self.defs_colors[g]}">&nbsp;**[{g}](#{g})**&nbsp;</span>'
            )

    @property
    def result(self):
        return [re.sub(self.deflink_regex, self.replace, l) for l in self.lines]


class DeflinksPreprocessor(Preprocessor):
    def run(self, lines: list[str]):
        return Replacer(lines).result
