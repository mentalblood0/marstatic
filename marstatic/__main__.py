import argparse
import pathlib
import sys

import markdown
import ruiner

from .Colorer import Color, Colorer

parser = argparse.ArgumentParser(prog="marstatic", description="Convert markdown to HTML")

parser.add_argument("-t", "--title", type=str, required=False, default="notes")
parser.add_argument("-s", "--salt", type=str, required=False, default="w")
parser.add_argument("-si", "--saturation_min", type=float, required=False, default=0.25)
parser.add_argument("-sa", "--saturation_max", type=float, required=False, default=0.7)
parser.add_argument("-vi", "--value_min", type=float, required=False, default=0.60)
parser.add_argument("-va", "--value_max", type=float, required=False, default=0.95)

args = parser.parse_args()

Color.salt = args.salt.encode()
Color.s_limits = (args.saturation_min, args.saturation_max)
Color.v_limits = (args.value_min, args.value_max)

text = sys.stdin.read()
c = Colorer(text)
body = markdown.markdown(c.colored())

templates = {p.stem: ruiner.Template(p.read_text()) for p in (pathlib.Path(__file__).parent / "templates").iterdir()}
parameters = {"title": str(args.title), "body": body, "Color": c.css}

result = templates["Page"].rendered(parameters, templates)
sys.stdout.write(result)
