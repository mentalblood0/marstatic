import argparse
import pathlib

import markdown
import ruiner

from .Colorer import Colorer

parser = argparse.ArgumentParser(prog="marstatic", description="Convert markdown to HTML")

parser.add_argument("-i", "--input", type=pathlib.Path, required=True)
parser.add_argument("-o", "--output", type=pathlib.Path, required=True)
parser.add_argument(
    "-vc",
    "--versions_colorspace",
    type=Colorer.VersionsColorspaceMode,
    choices=[c for c in Colorer.VersionsColorspaceMode],
    required=True,
)
parser.add_argument("-H", "--header", type=str, required=True)

args = parser.parse_args()

text = args.input.read_text(encoding="utf8")
c = Colorer(text, args.versions_colorspace)
body = markdown.markdown(c.colored())

templates = {p.stem: ruiner.Template(p.read_text()) for p in (pathlib.Path(__file__).parent / "templates").iterdir()}
parameters = {"header": str(args.header), "body": body, "Color": c.css}

result = templates["Page"].rendered(parameters, templates)
args.output.write_text(result, encoding="utf8")
