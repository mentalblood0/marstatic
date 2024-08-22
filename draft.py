import pyparsing as pp

fundamental_root = pp.Combine(pp.Char(pp.alphas.upper())[1, ...]).add_parse_action(lambda x: ("root", x[0]))
root = pp.Combine(pp.Char(pp.alphas.lower())[1, ...]).add_parse_action(lambda x: ("root", x[0]))
number = pp.Combine(pp.Char(pp.nums)[1, ...]).add_parse_action(lambda x: ("number", x[0]))
fundamental_atom = (fundamental_root + pp.Opt(number)).add_parse_action(
    lambda x: ("fundamental_atom", dict(x.as_list()))
)
atom = (root + pp.Opt(number)).add_parse_action(lambda x: ("atom", dict(x.as_list())))

clarification_delimiter = pp.Char(".").suppress()
clarification = (
    (atom | fundamental_atom) + clarification_delimiter + pp.DelimitedList(atom | number, clarification_delimiter)
).set_parse_action(lambda x: ("clarification", x.as_list()))

version_delimiter = pp.Char("-").suppress()
version = (
    (clarification | atom | fundamental_atom) + version_delimiter + pp.DelimitedList(atom | number, version_delimiter)
).set_parse_action(lambda x: ("version", x.as_list()))

answer_delimiter = pp.Char("/").suppress()
answer_element = version | clarification | atom | fundamental_atom
answer = pp.DelimitedList(answer_element, answer_delimiter).set_parse_action(lambda x: ("answer", x.as_list()))

thesis = (answer | version | clarification | fundamental_atom).set_parse_action(lambda x: ("thesis", x.as_list()))


def test_basic():
    atom.parse_string("abc1234").pprint()
    fundamental_atom.parse_string("ABC1234").pprint()
    clarification.parse_string("A2.b").pprint()
    clarification.parse_string("A2.b.c").pprint()
    version.parse_string("A2.b-c").pprint()
    answer.parse_string("A2.b-c/D").pprint()
