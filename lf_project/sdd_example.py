"""Our grammar and SDD for Item 3: alternating digit sum.

Grammar (convention of Section 2.2):
    S -> L
    L -> DN
    N -> L e
    D -> 0 1 2 ... 9
A string is a non-empty sequence of digits. The SDD computes the alternating
sum of the digits (+d1 -d2 +d3 ...) and the number of digits.

Attributes:
    D.val  synthesized  numeric value of the digit
    L.s    inherited    sign (+1 or -1) of the first digit of this L
    L.v    synthesized  alternating sum of the digits of this L
    L.len  synthesized  number of digits of this L
    N.s, N.v, N.len     same meaning as for L (N derives a possibly empty L)
    S.v, S.len          final results
"""
from sdd import SDD, Rule

GRAMMAR_LINES = [
    "S -> L",
    "L -> DN",
    "N -> L e",
    "D -> 0 1 2 3 4 5 6 7 8 9",
]

ATTRIBUTES = {
    'S': {'v': 'syn', 'len': 'syn'},
    'L': {'s': 'inh', 'v': 'syn', 'len': 'syn'},
    'N': {'s': 'inh', 'v': 'syn', 'len': 'syn'},
    'D': {'val': 'syn'},
}


def make_rules(circular=False):
    rules = {
        "S -> L": [
            Rule((1, 's'), [], lambda: 1),                       # L.s = 1
            Rule((0, 'v'), [(1, 'v')], lambda v: v),             # S.v = L.v
            Rule((0, 'len'), [(1, 'len')], lambda n: n),         # S.len = L.len
        ],
        "L -> DN": [
            Rule((2, 's'), [(0, 's')], lambda s: -s),            # N.s = -L.s
            Rule((0, 'v'), [(0, 's'), (1, 'val'), (2, 'v')],
                 lambda s, d, v: s * d + v),                     # L.v = L.s*D.val + N.v
            Rule((0, 'len'), [(2, 'len')], lambda n: 1 + n),     # L.len = 1 + N.len
        ],
        "N -> L": [
            Rule((1, 's'), [(0, 's')], lambda s: s),             # L.s = N.s
            Rule((0, 'v'), [(1, 'v')], lambda v: v),             # N.v = L.v
            Rule((0, 'len'), [(1, 'len')], lambda n: n),         # N.len = L.len
        ],
        "N -> e": [
            Rule((0, 'v'), [], lambda: 0),                       # N.v = 0
            Rule((0, 'len'), [], lambda: 0),                     # N.len = 0
        ],
    }
    for d in "0123456789":
        rules[f"D -> {d}"] = [Rule((0, 'val'), [(1, 'lexval')], lambda c: int(c))]
    if circular:
        # temporary change for Step 6: N.s now depends on N.v, which creates a cycle
        rules["L -> DN"][0] = Rule((2, 's'), [(2, 'v')], lambda v: v)
    return rules


def make_sdd(circular=False):
    return SDD(ATTRIBUTES, make_rules(circular), 'v')
