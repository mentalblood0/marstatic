import colorsys
import re

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class Deflinks(Extension):
    def extendMarkdown(self, md: Markdown):
        md.registerExtension(self)
        md.preprocessors.register(DeflinksPreprocessor(), "deflinks", 100)


class DeflinksPreprocessor(Preprocessor):
    deflink_regex = re.compile(r"\*\*(?P<link>(?:\w|\.|\/)+?)\*\*:*")

    @staticmethod
    def replace(m: re.Match):
        g = m.group(1)
        if m.group(0).endswith(":"):
            return f'**{g}**<a name="{g}"></a>:'
        else:
            return f"**[{g}](#{g})**"

    @staticmethod
    def color(target: int, overall: int):
        return "#%02x%02x%02x" % colorsys.hsv_to_rgb(target * 1 / overall, 0.5, 0.5)

    def run(self, lines: list[str]):
        return [re.sub(self.deflink_regex, self.replace, l) for l in lines]
