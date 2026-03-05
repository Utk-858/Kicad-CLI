import re

class Node:
    def __init__(self, name: str = "", values=None, children=None):
        self.name = name
        self.values = values if values is not None else []
        self.children = children if children is not None else []

    def __repr__(self):
        return f"Node({self.name!r}, {self.values!r}, {self.children!r})"

def tokenize(text):
    """
    Split the input into tokens, handling parentheses and quoted strings.
    """
    # Regex to match one of: '(' or ')' or quoted string, or atom
    token_re = re.compile(
        r'''"([^"\\]*(?:\\.[^"\\]*)*)"   # match quoted string
        |(\()                           # match open paren
        |(\))                           # match close paren
        |([^\s()"]+)                    # match atom
        ''',
        re.VERBOSE
    )

    for match in token_re.finditer(text):
        quoted, l_paren, r_paren, atom = match.groups()
        if quoted is not None:
            # Unescape any escaped quotes within the string
            yield quoted.replace('\\"', '"').replace('\\\\', '\\')
        elif l_paren is not None:
            yield '('
        elif r_paren is not None:
            yield ')'
        elif atom is not None:
            yield atom

def parse_tokens(tokens):
    """
    Given a token generator or list, build the Node tree.
    """
    stack = []
    current = None

    def finish_node():
        node = stack.pop()
        if stack:
            stack[-1].children.append(node)
        return node

    for token in tokens:
        if token == '(':
            # Start new node context
            stack.append(Node())
        elif token == ')':
            node = finish_node()
            if not stack:
                # Finished parsing; node is root
                return node
        else:
            # Token is either a node name or value
            if not stack:
                # Malformed
                continue
            cur_node = stack[-1]
            if cur_node.name == "":
                cur_node.name = token
            else:
                cur_node.values.append(token)
    if stack:
        # Return the first node if unbalanced but some structure built
        return stack[0]
    return None

def parse_sexp(file_path):
    """
    Given a file path, parse S-expression and return the root Node.
    """
    # Read file efficiently (whole file for S-expr is typically ok)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Tokenize
    tokens = tokenize(content)
    # Parse
    root = parse_tokens(tokens)
    return root
