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

    def replace(self, m: re.Match):
        g = m.group(1)
        if m.group(0).endswith(":"):
            return f'**{g}**<a name="{g}"></a>:'
        else:
            return f"**[{g}](#{g})**"

    def run(self, lines: list[str]):
        return [re.sub(self.deflink_regex, self.replace, l) for l in lines]
