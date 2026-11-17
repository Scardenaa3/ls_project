"""SLR(1): LR(0) items, CLOSURE and GOTO (Section 4.6.2), ACTION/GOTO tables
(Algorithm 4.46, Section 4.6.4) and the LR parsing algorithm (Algorithm 4.44,
Section 4.6.3)."""

from grammar import END, EPS, tokenize
from tree import Node

AUG = "S'"


class SLR1:
    def __init__(self, g):
        self.g = g
        # augmented grammar: the new production S' -> S is the last one
        self.prods = g.prods + [(AUG, (g.start,))]
        self.aug = len(g.prods)
        self.symbols = g.nonterminals + g.terminals
        self.states = []       # each state is a frozenset of items (prod, dot)
        self.trans = {}        # (state, symbol) -> state
        self.action = {}       # (state, terminal or $) -> ('s', j) | ('r', p) | ('acc',)
        self.goto = {}         # (state, nonterminal) -> state
        self.conflicts = []    # (state, symbol, old action, new action)
        self.build_automaton()
        self.build_table()
        self.is_slr1 = not self.conflicts

    # ---------- canonical collection of LR(0) items ----------
    def closure(self, items):
        result = set(items)
        work = list(items)
        while work:
            p, dot = work.pop()
            body = self.prods[p][1]
            if dot < len(body) and self.g.is_nonterminal(body[dot]):
                for q, (head, _) in enumerate(self.prods):
                    if head == body[dot] and (q, 0) not in result:
                        result.add((q, 0))
                        work.append((q, 0))
        return frozenset(result)

    def goto_set(self, items, x):
        moved = {(p, dot + 1) for p, dot in items
                 if dot < len(self.prods[p][1]) and self.prods[p][1][dot] == x}
        return self.closure(moved) if moved else None

    def build_automaton(self):
        start = self.closure({(self.aug, 0)})
        self.states = [start]
        index = {start: 0}
        i = 0
        while i < len(self.states):
            for x in self.symbols:
                j_set = self.goto_set(self.states[i], x)
                if j_set is None:
                    continue
                if j_set not in index:
                    index[j_set] = len(self.states)
                    self.states.append(j_set)
                self.trans[(i, x)] = index[j_set]
            i += 1

    # ---------- ACTION and GOTO ----------
    def set_action(self, i, a, act):
        old = self.action.get((i, a))
        if old is None:
            self.action[(i, a)] = act
        elif old != act:
            self.conflicts.append((i, a, old, act))

    def build_table(self):
        g = self.g
        for i, items in enumerate(self.states):
            for p, dot in sorted(items):
                head, body = self.prods[p]
                if dot < len(body):
                    a = body[dot]
                    if not g.is_nonterminal(a):
                        self.set_action(i, a, ('s', self.trans[(i, a)]))
                elif p == self.aug:
                    self.set_action(i, END, ('acc',))
                else:
                    for a in sorted(g.follow[head]):
                        self.set_action(i, a, ('r', p))
            for A in g.nonterminals:
                if (i, A) in self.trans:
                    self.goto[(i, A)] = self.trans[(i, A)]

    # ---------- parsing (Algorithm 4.44) ----------
    def act_str(self, act):
        if act is None:
            return 'error'
        if act[0] == 's':
            return f"shift {act[1]}"
        if act[0] == 'r':
            return f"reduce {self.prod_str(act[1])}"
        return 'accept'

    def prod_str(self, p):
        head, body = self.prods[p]
        return f"{head} -> {''.join(body) if body else EPS}"

    def parse(self, string, trace=False):
        """Returns (accepted, parse tree or None, trace rows)."""
        tokens = tokenize(string)
        rows = []
        if tokens is None:
            return False, None, rows
        stack = [(0, None)]                # pairs (state, tree node)
        ip = 0
        while True:
            s = stack[-1][0]
            a = tokens[ip]
            act = self.action.get((s, a))
            if trace:
                text = ' '.join([str(stack[0][0])] +
                                [f"{n.symbol} {st}" for st, n in stack[1:]])
                rows.append((text, ''.join(tokens[ip:]), self.act_str(act)))
            if act is None:
                return False, None, rows
            if act[0] == 's':
                node = Node(a)
                node.attrs['lexval'] = a
                stack.append((act[1], node))
                ip += 1
            elif act[0] == 'r':
                p = act[1]
                head, body = self.prods[p]
                n = len(body)
                node = Node(head, p)
                node.children = [x[1] for x in stack[len(stack) - n:]]
                del stack[len(stack) - n:]
                stack.append((self.goto[(stack[-1][0], head)], node))
            else:
                return True, stack[-1][1], rows

    # ---------- printing ----------
    def item_str(self, p, dot):
        head, body = self.prods[p]
        return f"{head} -> {''.join(body[:dot])}.{''.join(body[dot:])}"

    def describe(self):
        g = self.g
        out = ["LR(0) automaton (canonical collection):"]
        for i, items in enumerate(self.states):
            out.append(f"I{i}:")
            for p, dot in sorted(items):
                out.append(f"    {self.item_str(p, dot)}")
            for x in self.symbols:
                if (i, x) in self.trans:
                    out.append(f"    --{x}--> I{self.trans[(i, x)]}")
        out.append("")
        out.append("SLR(1) table:")
        cols = g.terminals + [END]
        out.append('state  ' + ''.join(c.ljust(7) for c in cols) + '| ' +
                   ''.join(A.ljust(5) for A in g.nonterminals))
        for i in range(len(self.states)):
            cells = []
            for c in cols:
                act = self.action.get((i, c))
                cells.append(('' if act is None else
                              'acc' if act[0] == 'acc' else f"{act[0]}{act[1]}").ljust(7))
            gotos = [str(self.goto.get((i, A), '')).ljust(5) for A in g.nonterminals]
            out.append(str(i).ljust(7) + ''.join(cells) + '| ' + ''.join(gotos))
        for i, a, old, new in self.conflicts:
            out.append(f"CONFLICT in state {i} on {a}: {self.act_str(old)}  vs  {self.act_str(new)}")
        return '\n'.join(out)
