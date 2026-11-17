"""Parse tree node shared by both parsers and the SDD evaluator."""


class Node:
    def __init__(self, symbol, prod=None):
        self.symbol = symbol      # grammar symbol
        self.prod = prod          # index of the production used (nonterminals)
        self.children = []        # an epsilon production has no children
        self.attrs = {}           # attribute name -> value
        self.id = None


def preorder(node):
    yield node
    for child in node.children:
        yield from preorder(child)


def tree_lines(root, g, show_attrs=True):
    """One node per line, indented by depth."""
    lines = []

    def visit(node, depth):
        text = '  ' * depth + (f"{node.symbol}_{node.id}" if node.id is not None else node.symbol)
        if node.prod is not None:
            text += f"   [{g.prod_str(node.prod)}]"
        if show_attrs and node.attrs:
            attrs = ', '.join(f"{k}={v!r}" if k == 'lexval' else f"{k}={v}"
                              for k, v in node.attrs.items())
            text += f"   {{{attrs}}}"
        lines.append(text)
        for c in node.children:
            visit(c, depth + 1)

    visit(root, 0)
    return lines
