"""Generic SDD evaluator (Sections 5.1 and 5.2 of the book).

The evaluator knows nothing about a particular SDD: the SDD is plain data
(class SDD below). Evaluation follows Section 5.2.1 (dependency graph) and
Section 5.2.2 (topological order).
"""
from collections import deque

from tree import preorder


class Rule:
    """One semantic rule.  A reference is a pair (position, attribute):
    position 0 is the head of the production, position i >= 1 is the i-th
    symbol of the body.  Terminals only have the attribute 'lexval'."""

    def __init__(self, target, deps, func):
        self.target = target      # attribute defined by the rule
        self.deps = deps          # attributes the rule uses
        self.func = func          # function of the values of deps, in order


class SDD:
    def __init__(self, attributes, rules, main_attr):
        self.attributes = attributes   # symbol -> {attribute: 'syn' or 'inh'}
        self.rules = rules             # "A -> body" -> [Rule, ...]
        self.main_attr = main_attr     # attribute of S that is printed at the end


def prod_key(head, body):
    return f"{head} -> {''.join(body) if body else 'e'}"


def check_sdd(g, sdd):
    """Checks the conditions of Section 5.1.1. Returns a list of error messages."""
    errors = []
    for a, kind in sdd.attributes.get(g.start, {}).items():
        if kind == 'inh':
            errors.append(f"start symbol has inherited attribute {a}")
    for head, body in g.prods:
        key = prod_key(head, body)
        rules = sdd.rules.get(key, [])
        symbols = (head,) + tuple(body)
        required = set()
        for a, kind in sdd.attributes.get(head, {}).items():
            if kind == 'syn':
                required.add((0, a))
        for i, x in enumerate(body, start=1):
            for a, kind in sdd.attributes.get(x, {}).items():
                if kind == 'inh':
                    required.add((i, a))
        targets = [r.target for r in rules]
        for t in set(targets):
            if targets.count(t) > 1:
                errors.append(f"{key}: attribute {t} defined more than once")
        for t in required - set(targets):
            errors.append(f"{key}: attribute {t} is never defined")
        for t in set(targets) - required:
            errors.append(f"{key}: rule defines {t}, which it may not define")
        for r in rules:
            for pos, a in r.deps:
                if pos > len(body):
                    errors.append(f"{key}: dependency {(pos, a)} out of range")
                    continue
                x = symbols[pos]
                if g.is_nonterminal(x):
                    kind = sdd.attributes.get(x, {}).get(a)
                    if kind is None:
                        errors.append(f"{key}: {x} has no attribute {a}")
                    elif pos == 0 and kind != 'inh':
                        errors.append(f"{key}: rule uses synthesized attribute of the head")
                elif a != 'lexval':
                    errors.append(f"{key}: terminal {x} only has lexval")
    return errors


class Result:
    pass


def label(node, attr):
    return f"{node.symbol}_{node.id}.{attr}"


def evaluate(root, g, sdd):
    """Builds the dependency graph of the tree, orders it topologically and
    evaluates it. Returns a Result with fields: circular, order, edges, nodes."""
    nodes = list(preorder(root))
    for i, node in enumerate(nodes):
        node.id = i
        node.attrs = {}

    # one vertex per attribute of each node (leaves: lexval, already known)
    verts = []
    for node in nodes:
        if g.is_nonterminal(node.symbol):
            for a in sdd.attributes.get(node.symbol, {}):
                verts.append((node, a))
        else:
            verts.append((node, 'lexval'))
    vid = {(n.id, a): k for k, (n, a) in enumerate(verts)}

    def vertex(node, pos, attr):
        target = node if pos == 0 else node.children[pos - 1]
        return vid[(target.id, attr)]

    rule_of = {}          # vertex number -> (rule, vertices it uses)
    edges = []            # (used vertex, defined vertex)
    for node in nodes:
        if not g.is_nonterminal(node.symbol):
            continue
        head, body = g.prods[node.prod]
        for r in sdd.rules.get(prod_key(head, body), []):
            t = vertex(node, *r.target)
            used = [vertex(node, pos, a) for pos, a in r.deps]
            rule_of[t] = (r, used)
            for u in used:
                edges.append((u, t))

    succ = [[] for _ in verts]
    indeg = [0] * len(verts)
    for u, t in edges:
        succ[u].append(t)
        indeg[t] += 1

    # topological order (Kahn): repeatedly take a vertex with no pending inputs
    queue = deque(k for k in range(len(verts)) if indeg[k] == 0)
    order = []
    while queue:
        k = queue.popleft()
        order.append(k)
        for t in succ[k]:
            indeg[t] -= 1
            if indeg[t] == 0:
                queue.append(t)

    res = Result()
    res.nodes = nodes
    res.verts = verts
    res.edges = edges
    res.circular = len(order) < len(verts)
    if res.circular:
        res.stuck = [label(*verts[k]) for k in range(len(verts)) if indeg[k] > 0]
        res.order = []
        return res

    values = {}
    for k, (node, a) in enumerate(verts):
        if a == 'lexval':
            values[k] = node.symbol          # the lexval of a terminal is the character
            node.attrs['lexval'] = node.symbol
    evaluated = []
    for k in order:
        if k in rule_of:
            r, used = rule_of[k]
            values[k] = r.func(*[values[u] for u in used])
            node, a = verts[k]
            node.attrs[a] = values[k]
            evaluated.append(k)
    for node in nodes:     # show attributes in the order they were declared
        if g.is_nonterminal(node.symbol):
            node.attrs = {a: node.attrs[a] for a in sdd.attributes[node.symbol]}
    res.order = [(label(*verts[k]), values[k]) for k in evaluated]
    res.edge_labels = [(label(*verts[u]), label(*verts[t])) for u, t in edges]
    res.main_value = root.attrs[sdd.main_attr]
    return res
