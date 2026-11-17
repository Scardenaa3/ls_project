"""Interactive mode (menu driven) for Items 1, 2 and 3.

Usage:  python3 interactive.py

This is an extra front end. It reuses grammar.py, ll1.py, slr.py, tree.py,
sdd.py and sdd_example.py without changing them. The input/output required
by the statement (Section 2.2) is still produced by main.py and run_sdd.py.
"""
import sys

from grammar import parse_grammar, print_sets
from ll1 import LL1
from slr import SLR1
from sdd import check_sdd, evaluate
from sdd_example import GRAMMAR_LINES, make_sdd
from tree import tree_lines


def ask(prompt):
    return input(prompt).strip()


def on_off(flag):
    return 'on' if flag else 'off'


def choose(title, options):
    """Prints a numbered menu and returns the chosen number (1..len)."""
    print()
    print(title)
    for i, text in enumerate(options, start=1):
        print(f"  {i}) {text}")
    while True:
        s = ask("> ")
        if s.isdigit() and 1 <= int(s) <= len(options):
            return int(s)
        print(f"Please type a number from 1 to {len(options)}.")


# ----------------------------------------------------------------------
# Items 1 and 2
# ----------------------------------------------------------------------
def check_line(line, heads):
    """Returns (normalized line, None) or (None, error message)."""
    if '->' not in line:
        return None, "The line must look like:  A -> alt1 alt2 ...  (e is epsilon)"
    head = line[:line.index('->')].strip()
    alts = line[line.index('->') + 2:].split()
    if len(head) != 1 or not head.isupper():
        return None, "The left side must be one capital letter."
    if head in heads:
        return None, f"{head} already has a line (one line per nonterminal)."
    if not alts:
        return None, "Write at least one alternative (e is the empty string)."
    if any('$' in a for a in alts):
        return None, "The symbol $ is reserved as the end marker."
    return f"{head} -> {' '.join(alts)}", None


def read_grammar():
    """Reads a grammar from the keyboard. Returns None to go back."""
    print()
    print("Type the grammar as in the statement: capital letters are nonterminals,")
    print("S is the start symbol, e is the empty string, alternatives are separated")
    print("by blank spaces.  Example:  B -> bBc e")
    while True:
        s = ask("Number of nonterminals (empty line to go back): ")
        if s == '':
            return None
        if s.isdigit() and int(s) > 0:
            n = int(s)
            break
        print("Please type a positive integer.")
    lines, heads = [], set()
    while len(lines) < n:
        raw = ask(f"Production {len(lines) + 1}/{n}: ")
        line, err = check_line(raw, heads)
        if err:
            print(err)
            continue
        heads.add(line[0])
        lines.append(line)
    if 'S' not in heads:
        print("The grammar needs a line for the start symbol S. Try again.")
        return read_grammar()
    for line in lines:
        for c in line[line.index('->') + 2:]:
            if c.isupper() and c not in heads:
                print(f"The nonterminal {c} has no line. Try again.")
                return read_grammar()
    return parse_grammar(lines)


def show_trace(rows):
    print(f"{'STACK':<30}{'INPUT':<20}ACTION")
    for stack, rest, action in rows:
        print(f"{stack:<30}{rest:<20}{action}")


def parse_session(name, parser, trace):
    print()
    print(f"Parsing with {name}. Type a string and press Enter "
          "(e = empty string). Empty line to stop.")
    while True:
        s = ask("string> ")
        if s == '':
            return
        ok, _, rows = parser.parse(s, trace)
        if trace:
            show_trace(rows)
        print('yes' if ok else 'no')


def grammar_mode():
    g = read_grammar()
    if g is None:
        return
    ll1, slr = LL1(g), SLR1(g)
    print()
    print_sets(g)
    print()
    if ll1.is_ll1 and slr.is_slr1:
        print("The grammar is both LL(1) and SLR(1).")
    elif ll1.is_ll1:
        print("Grammar is LL(1).")
    elif slr.is_slr1:
        print("Grammar is SLR(1).")
    else:
        print("Grammar is neither LL(1) nor SLR(1).")

    parsers = []
    if ll1.is_ll1:
        parsers.append(('LL(1)', ll1))
    if slr.is_slr1:
        parsers.append(('SLR(1)', slr))
    current = 0
    trace = False

    while True:
        options = ["Parse strings",
                   "Show the LL(1) table and the conflicts",
                   "Show the LR(0) automaton, the SLR(1) table and the conflicts",
                   "Show FIRST and FOLLOW again",
                   f"Step-by-step trace of each parse (now {on_off(trace)})",
                   "Enter another grammar",
                   "Back to the main menu"]
        if len(parsers) > 1:
            options.insert(1, f"Switch parser (now {parsers[current][0]})")
        elif parsers:
            options[0] = f"Parse strings (with {parsers[0][0]})"
        k = choose("Grammar menu", options)
        text = options[k - 1]
        if text.startswith("Parse strings"):
            if not parsers:
                print("There is no parser to use: the grammar is neither LL(1) nor SLR(1).")
            else:
                name, parser = parsers[current]
                parse_session(name, parser, trace)
        elif text.startswith("Switch parser"):
            current = (current + 1) % len(parsers)
            print(f"Now using {parsers[current][0]}.")
        elif text.startswith("Show the LL(1)"):
            print(ll1.describe())
        elif text.startswith("Show the LR(0)"):
            print(slr.describe())
        elif text.startswith("Show FIRST"):
            print_sets(g)
        elif text.startswith("Step-by-step"):
            trace = not trace
            print(f"Trace is now {on_off(trace)}.")
        elif text.startswith("Enter another"):
            return grammar_mode()
        else:
            return


# ----------------------------------------------------------------------
# Item 3
# ----------------------------------------------------------------------
def run_sdd_string(g, sdd, parser, s, show_graph, stepwise):
    ok, root, _ = parser.parse(s)
    if not ok:
        print('no')
        return
    res = evaluate(root, g, sdd)
    if res.circular:
        print("The SDD is circular: these attributes cannot be ordered:")
        print('  ' + ', '.join(res.stuck))
        return
    print("Parse tree (nodes are numbered in preorder):")
    print('\n'.join(tree_lines(root, g, show_attrs=False)))
    if show_graph:
        print("Dependency graph (used -> defined):")
        for u, t in res.edge_labels:
            print(f"  {u} -> {t}")
    print("Evaluation order:")
    total = len(res.order)
    for i, (name, value) in enumerate(res.order, start=1):
        print(f"  {i}/{total}. {name} = {value}")
        if stepwise and i < total:
            c = ask("     [Enter] next   [a] show all   [q] stop > ").lower()
            if c == 'a':
                stepwise = False
            elif c == 'q':
                print("Stopped.")
                return
    print("Annotated parse tree:")
    print('\n'.join(tree_lines(root, g)))
    print(f"S.{sdd.main_attr} = {res.main_value}")


def sdd_mode():
    g = parse_grammar(GRAMMAR_LINES)
    ll1, slr = LL1(g), SLR1(g)
    use_ll1 = ll1.is_ll1
    circular = False
    show_graph = False
    stepwise = True

    print()
    print("Grammar of the SDD (sdd_example.py):")
    for line in GRAMMAR_LINES:
        print("  " + line)

    while True:
        options = ["Evaluate strings",
                   f"Pause after each attribute (now {on_off(stepwise)})",
                   f"Show the dependency graph (now {on_off(show_graph)})",
                   f"Circular variant of the SDD (now {on_off(circular)}; try the string 12)",
                   f"Switch parser (now {'LL(1)' if use_ll1 else 'SLR(1)'})",
                   "Back to the main menu"]
        k = choose("SDD menu", options)
        if k == 1:
            sdd = make_sdd(circular=circular)
            errors = check_sdd(g, sdd)
            if errors:
                print("The SDD is not well formed:")
                for e in errors:
                    print("  " + e)
                continue
            parser = ll1 if use_ll1 else slr
            print("Type a string of digits (for example 1234). Empty line to stop.")
            while True:
                s = ask("string> ")
                if s == '':
                    break
                run_sdd_string(g, sdd, parser, s, show_graph, stepwise)
                print()
        elif k == 2:
            stepwise = not stepwise
        elif k == 3:
            show_graph = not show_graph
        elif k == 4:
            circular = not circular
        elif k == 5:
            use_ll1 = not use_ll1
        else:
            return


def main():
    print("Formal Languages and Compilers - interactive mode")
    try:
        while True:
            k = choose("Main menu",
                       ["Grammar analysis and parsing (FIRST/FOLLOW, LL(1), SLR(1))",
                        "Syntax-directed definition (SDD)",
                        "Quit"])
            if k == 1:
                grammar_mode()
            elif k == 2:
                sdd_mode()
            else:
                break
    except (EOFError, KeyboardInterrupt):
        print()
    print("Bye.")


if __name__ == '__main__':
    main()
