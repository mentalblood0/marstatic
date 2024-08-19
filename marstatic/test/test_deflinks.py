import markdown

from ..Deflinks import Deflinks


def test_basic():
    text = """**DEF**: lalala

lololo **DEF** lululu"""
    result = markdown.markdown(text, extensions=[Deflinks()])
    expect = """<p><strong>DEF</strong><a name="DEF"></a>: lalala</p>
<p>lololo <strong><a href="#DEF">DEF</a></strong> lululu</p>"""
    assert result == expect
