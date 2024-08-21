import pyparsing as pp

fundamental_root = pp.Combine(pp.Char(pp.alphas.upper()) * ...)("fundamental_root")
root = pp.Combine(pp.Char(pp.alphas.lower()) * ...)("root")
number = pp.Combine(pp.Char(pp.nums) * ...)("number")
fundamental_atom = (fundamental_root + number)("fundamental_atom")
atom = (root + number)("atom")

clarification_delimiter = pp.Char(".")
clarification = (atom | fundamental_atom) + pp.Opt(
    clarification_delimiter + pp.DelimitedList(atom | number, clarification_delimiter)
)("clarification")

version_delimiter = pp.Char("-")
version = (clarification | atom | fundamental_atom) + pp.Opt(
    version_delimiter + pp.DelimitedList(atom | number, version_delimiter)
)("version")

answer_delimiter = pp.Char("/")
answer_element = version | clarification | atom | fundamental_atom
answer = pp.DelimitedList(answer_element)("answer")

thesis = (answer | version | clarification | fundamental_atom)("thesis")


def test_basic():
    # print(atom.parse_string("abc1234").asDict())
    print(clarification.parse_string("A2.b").asDict())
    # print(thesis.parse_string("A2.b-c/D").asDict())
