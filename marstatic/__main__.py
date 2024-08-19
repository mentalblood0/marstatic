import argparse
import pathlib

import markdown
import ruiner

from .Deflinks import Deflinks

parser = argparse.ArgumentParser(prog="marstatic", description="Convert markdown to HTML")
parser.add_argument("-i", "--input", type=pathlib.Path, required=True)
parser.add_argument("-o", "--output", type=pathlib.Path, required=True)
parser.add_argument("-H", "--header", type=str, required=True)

args = parser.parse_args()

args.output.write_text(
    ruiner.Template((pathlib.Path(__file__).parent / "template.html").read_text()).rendered(
        {
            "header": args.header,
            "body": markdown.markdown(args.input.read_text(encoding="utf8"), extensions=[Deflinks()]),
        }
    ),
    encoding="utf8",
)
