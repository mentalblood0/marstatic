import argparse
import pathlib

import markdown

from .Deflinks import Deflinks

parser = argparse.ArgumentParser(prog="marstatic", description="Convert markdown to HTML")
parser.add_argument("-i", "--input", type=pathlib.Path, required=True)
parser.add_argument("-o", "--output", type=pathlib.Path, required=True)

args = parser.parse_args()

args.output.write_text(
    markdown.markdown(args.input.read_text(encoding="utf8"), extensions=[Deflinks()]), encoding="utf8"
)
