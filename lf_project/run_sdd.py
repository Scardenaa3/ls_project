"""Item 3: evaluate the SDD of sdd_example.py on the parse tree of each string.

Usage:  python3 run_sdd.py [--parser ll1|slr1] [--graph] [--circular]
Strings are read from standard input, one per line, until an empty line.
"""
import sys

from grammar import parse_grammar
from ll1 import LL1
from slr import SLR1
from sdd import check_sdd, evaluate
from sdd_example import GRAMMAR_LINES, make_sdd
from tree import tree_lines


def main():
    args = sys.argv[1:]
    g = parse_grammar(GRAMMAR_LINES)
    sdd = make_sdd(circular='--circular' in args)
    errors = check_sdd(g, sdd)
    if errors:
        print("The SDD is not well formed:")
        for e in errors:
            print("  " + e)
        return

    ll1, slr = LL1(g), SLR1(g)
    if '--parser' in args:
        use_ll1 = args[args.index('--parser') + 1] == 'll1'
    else:
        use_ll1 = ll1.is_ll1
    parser = ll1 if use_ll1 else slr

    while True:
        line = sys.stdin.readline().strip()
        if not line:
            break
        ok, root, _ = parser.parse(line)
        if not ok:
            print('no')
            continue
        res = evaluate(root, g, sdd)
        if res.circular:
            print("The SDD is circular: these attributes cannot be ordered:")
            print('  ' + ', '.join(res.stuck))
            continue
        print("Annotated parse tree:")
        print('\n'.join(tree_lines(root, g)))
        if '--graph' in args:
            print("Dependency graph (used -> defined):")
            for u, t in res.edge_labels:
                print(f"  {u} -> {t}")
        print("Evaluation order:")
        for i, (name, value) in enumerate(res.order, start=1):
            print(f"  {i}. {name} = {value}")
        print(f"S.{sdd.main_attr} = {res.main_value}")
        print()


if __name__ == '__main__':
    main()
