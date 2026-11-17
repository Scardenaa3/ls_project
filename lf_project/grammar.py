"""Grammar representation, FIRST and FOLLOW (Section 4.4.2 of the book)."""

EPS = 'e'
END = '$'


class Grammar:
    def __init__(self, rules):
        """rules: list of (head, [alternative strings]) in input order."""
        self.start = 'S'
        self.nonterminals = sorted(head for head, _ in rules)
        self.nt_set = set(self.nonterminals)
        # prods[i] = (head, body) where body is a tuple of symbols.
        # An epsilon production has the empty tuple as its body.
        self.prods = []
        for head, alts in rules:
            for alt in alts:
                body = tuple(c for c in alt if c != EPS)
                self.prods.append((head, body))
        used = {c for _, body in self.prods for c in body}
        self.terminals = sorted(c for c in used if c not in self.nt_set)
        self.first = self.compute_first()
        self.follow = self.compute_follow()

    def is_nonterminal(self, x):
        return x in self.nt_set

    def prod_str(self, i):
        head, body = self.prods[i]
        return f"{head} -> {''.join(body) if body else EPS}"

    # ---------- FIRST ----------
    def first_of(self, symbols, first=None):
        """FIRST of a string X1 X2 ... Xn (a sequence of symbols)."""
        if first is None:
            first = self.first
        result = set()
        for x in symbols:
            fx = first[x] if x in self.nt_set else {x}
            result |= fx - {EPS}
            if EPS not in fx:
                return result
        result.add(EPS)          # every symbol can derive epsilon
        return result

    def compute_first(self):
        first = {a: set() for a in self.nonterminals}
        changed = True
        while changed:           # repeat until no set grows
            changed = False
            for head, body in self.prods:
                f = self.first_of(body, first)
                if not f <= first[head]:
                    first[head] |= f
                    changed = True
        return first

    # ---------- FOLLOW ----------
    def compute_follow(self):
        follow = {a: set() for a in self.nonterminals}
        follow[self.start].add(END)
        changed = True
        while changed:
            changed = False
            for head, body in self.prods:
                for i, b in enumerate(body):
                    if b not in self.nt_set:
                        continue
                    f = self.first_of(body[i + 1:])
                    new = f - {EPS}
                    if EPS in f:
                        new |= follow[head]
                    if not new <= follow[b]:
                        follow[b] |= new
                        changed = True
        return follow


def parse_grammar(lines):
    """lines: the n production lines, e.g. 'B -> bBc e'."""
    rules = []
    for line in lines:
        line = line.strip()
        head = line[0]
        rest = line[line.index('->') + 2:]
        rules.append((head, rest.split()))
    return Grammar(rules)


def format_set(s):
    """Terminals in ASCII order, then e, then $ (as the assignment asks)."""
    items = sorted(x for x in s if x not in (EPS, END))
    if EPS in s:
        items.append(EPS)
    if END in s:
        items.append(END)
    return '{' + ', '.join(items) + '}'


def print_sets(g):
    for a in g.nonterminals:
        print(f"First({a}) = {format_set(g.first[a])}")
    for a in g.nonterminals:
        print(f"Follow({a}) = {format_set(g.follow[a])}")


def tokenize(string):
    """Input symbols plus the end marker. The line 'e' is the empty string."""
    if string == EPS:
        return [END]
    if END in string or any(c.isspace() for c in string):
        return None
    return list(string) + [END]
