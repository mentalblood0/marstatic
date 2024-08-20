import argparse
import pathlib

import markdown
import ruiner

from .deflinks import Replacer

parser = argparse.ArgumentParser(prog="marstatic", description="Convert markdown to HTML")

parser.add_argument("-i", "--input", type=pathlib.Path, required=True)
parser.add_argument("-o", "--output", type=pathlib.Path, required=True)
parser.add_argument("-H", "--header", type=str, required=True)

args = parser.parse_args()
input = args.input.read_text(encoding="utf8")

replacer = Replacer.from_input(input)
body = markdown.markdown(replacer.result)

templates = {p.stem: ruiner.Template(p.read_text()) for p in (pathlib.Path(__file__).parent / "templates").iterdir()}
parameters = {"header": str(args.header), "body": body, "DefColor": replacer.defs.colors_classes}

result = templates["Page"].rendered(parameters, templates=templates)
args.output.write_text(result, encoding="utf8")
