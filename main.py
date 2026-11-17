"""Items 1 and 2: FIRST/FOLLOW, LL(1) parser and SLR(1) parser.

Usage:  python3 main.py [--sets] [--tables] [--trace] < grammar_and_strings.txt

When the input comes from a file or a pipe (as the statement requires) the
program behaves exactly as described in Section 2.2. Only when it is started
from a terminal, with nothing redirected, it first shows a menu to choose an
example or to type a grammar.
"""
import os
import sys

from grammar import parse_grammar, print_sets
from ll1 import LL1
from slr import SLR1


def read_line():
    line = sys.stdin.readline()
    return None if line == '' else line.strip()


def run_strings(parser, trace):
    """Reads strings until an empty line (or end of input)."""
    while True:
        line = read_line()
        if not line:
            break
        ok, _, rows = parser.parse(line, trace)
        if trace:
            print(f"{'STACK':<30}{'INPUT':<20}ACTION")
            for stack, rest, action in rows:
                print(f"{stack:<30}{rest:<20}{action}")
        print('yes' if ok else 'no')
        sys.stdout.flush()


def run(args):
    trace = '--trace' in args
    n = int(read_line())
    g = parse_grammar([read_line() for _ in range(n)])
    if '--sets' in args:
        print_sets(g)
    ll1, slr = LL1(g), SLR1(g)
    if '--tables' in args:
        print(ll1.describe())
        print()
        print(slr.describe())
        print()

    if ll1.is_ll1 and slr.is_slr1:
        while True:
            print("Select a parser (T: for LL(1), B: for SLR(1), Q: quit):")
            sys.stdout.flush()
            choice = read_line()
            if choice is None or choice.upper() == 'Q':
                break
            if choice.upper() == 'T':
                run_strings(ll1, trace)
            elif choice.upper() == 'B':
                run_strings(slr, trace)
    elif ll1.is_ll1:
        print("Grammar is LL(1).")
        run_strings(ll1, trace)
    elif slr.is_slr1:
        print("Grammar is SLR(1).")
        run_strings(slr, trace)
    else:
        print("Grammar is neither LL(1) nor SLR(1).")


EXAMPLES = [
    ('ex1.txt', 'Statement example 1 (SLR(1))'),
    ('ex2.txt', 'Statement example 2 (LL(1) and SLR(1))'),
    ('ex3.txt', 'Statement example 3 (neither)'),
    ('mine.txt', 'Our own grammar (nested lists)'),
]


def menu(args):
    """Shown only when stdin is a terminal: choose an example or type input."""
    here = os.path.dirname(os.path.abspath(__file__))
    keyboard = sys.stdin
    while True:
        print()
        print("What do you want to run?")
        for i, (name, text) in enumerate(EXAMPLES, start=1):
            print(f"  {i}) {text}  [examples/{name}]")
        print(f"  {len(EXAMPLES) + 1}) Type my own grammar and strings")
        print(f"  {len(EXAMPLES) + 2}) Quit")
        choice = input("> ").strip()
        if not choice.isdigit() or not 1 <= int(choice) <= len(EXAMPLES) + 2:
            print(f"Please type a number from 1 to {len(EXAMPLES) + 2}.")
            continue
        k = int(choice)
        if k == len(EXAMPLES) + 2:
            return
        try:
            if k <= len(EXAMPLES):
                name = EXAMPLES[k - 1][0]
                path = os.path.join(here, 'examples', name)
                with open(path, encoding='utf-8') as f:
                    text = f.read()
                print(f"--- input (examples/{name}) ---")
                print(text.rstrip('\n'))
                print("--- output ---")
                sys.stdin = open(path, encoding='utf-8')
                try:
                    run(args)
                finally:
                    sys.stdin.close()
                    sys.stdin = keyboard
            else:
                print("Type the number of nonterminals, then one production per line")
                print("(S is the start symbol, e is the empty string, alternatives are")
                print("separated by blank spaces, for example: B -> bBc e).")
                print("Then type the strings to parse, one per line, and finish with an")
                print("empty line.")
                run(args)
        except (ValueError, TypeError, IndexError):
            print("The grammar was not written in the expected format.")


def main():
    args = sys.argv[1:]
    if sys.stdin.isatty():
        try:
            menu(args)
        except (EOFError, KeyboardInterrupt):
            print()
    else:
        run(args)


if __name__ == '__main__':
    main()
