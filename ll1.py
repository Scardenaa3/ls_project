"""LL(1): predictive table (Algorithm 4.31) and table-driven parser
(Algorithm 4.34, Section 4.4.4)."""

from grammar import EPS, END, tokenize
from tree import Node


class LL1:
    def __init__(self, g):
        self.g = g
        self.table = {}        # (nonterminal, terminal or $) -> production index
        self.conflicts = []    # (A, a, old production, new production)
        for i, (head, body) in enumerate(g.prods):
            f = g.first_of(body)
            for a in f - {EPS}:
                self.add(head, a, i)
            if EPS in f:
                for b in g.follow[head]:
                    self.add(head, b, i)
        # The grammar is LL(1) exactly when no table entry is multiply defined.
        self.is_ll1 = not self.conflicts

    def add(self, head, a, i):
        old = self.table.get((head, a))
        if old is None:
            self.table[(head, a)] = i
        elif old != i:
            self.conflicts.append((head, a, old, i))

    def parse(self, string, trace=False):
        """Returns (accepted, parse tree or None, trace rows)."""
        g = self.g
        tokens = tokenize(string)
        rows = []
        if tokens is None:
            return False, None, rows
        root = Node(g.start)
        stack = [Node(END), root]          # top of the stack is the last element
        ip = 0
        while True:
            top = stack[-1]
            a = tokens[ip]
            if trace:
                rows.append((''.join(n.symbol for n in reversed(stack)),
                             ''.join(tokens[ip:]), None))
            if top.symbol == END:
                ok = (a == END)
                if trace:
                    rows[-1] = rows[-1][:2] + ('accept' if ok else 'error',)
                return ok, (root if ok else None), rows
            if not g.is_nonterminal(top.symbol):
                if top.symbol == a:
                    top.attrs['lexval'] = a
                    stack.pop()
                    ip += 1
                    action = f"match {a}"
                else:
                    action = 'error'
            else:
                p = self.table.get((top.symbol, a))
                if p is None:
                    action = 'error'
                else:
                    stack.pop()
                    top.prod = p
                    top.children = [Node(s) for s in g.prods[p][1]]
                    stack.extend(reversed(top.children))
                    action = g.prod_str(p)
            if trace:
                rows[-1] = rows[-1][:2] + (action,)
            if action == 'error':
                return False, None, rows

    def describe(self):
        g = self.g
        cols = g.terminals + [END]
        out = ["LL(1) predictive parsing table:"]
        width = max([len(g.prod_str(i)) for i in range(len(g.prods))] + [3]) + 2
        out.append(' ' * 3 + ''.join(c.ljust(width) for c in cols))
        for A in g.nonterminals:
            cells = []
            for c in cols:
                p = self.table.get((A, c))
                cells.append((g.prod_str(p) if p is not None else '').ljust(width))
            out.append(A.ljust(3) + ''.join(cells))
        for head, a, old, new in self.conflicts:
            out.append(f"CONFLICT in M[{head}, {a}]: {g.prod_str(old)}  vs  {g.prod_str(new)}")
        return '\n'.join(out)
