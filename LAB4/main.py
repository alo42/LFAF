"""
Laboratory Work 4 – Regular Expressions  (Variant 4)
Course: Formal Languages & Finite Automata

Variant 4 regular expressions (derived from the provided examples):
  Regex 1 : S(U|V)W+Y(2|4)+
  Regex 2 : L(M|N)O+P+Q(2|3)
  Regex 3 : R+S(T|U)W(X|Y)+

The generator dynamically interprets any pattern from the supported
subset and randomly produces a valid string for it.

Supported regex syntax
──────────────────────
  Literals        : any single character (A-Z, 0-9, …)
  Grouping        : (abc)
  Alternation     : (a|b|c)
  Quantifiers     : +  one-or-more  (capped at MAX_REPEAT)
                    *  zero-or-more (capped at MAX_REPEAT)
                    ?  zero-or-one
                    {n}   exactly n
                    {n,m} between n and m (inclusive)

Bonus: generate_with_trace() shows the step-by-step processing log.
"""

import random
import re as stdlib_re  # only used for the {n,m} sub-match

MAX_REPEAT = 5          # upper bound for + and *


# ─────────────────────────────────────────────────────────────────────────────
# 1.  AST NODES  (plain tuples for simplicity)
# ─────────────────────────────────────────────────────────────────────────────
#   ('lit',    char)
#   ('cat',    [node, ...])
#   ('alt',    [node, ...])
#   ('rep',    node, lo, hi)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  PARSER
# ─────────────────────────────────────────────────────────────────────────────

class Parser:
    """Recursive-descent parser for the regex subset described above."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    # entry point
    def parse(self):
        node = self._alternation()
        if self.pos != len(self.pattern):
            raise ValueError(
                f"Unexpected character '{self.pattern[self.pos]}' at position {self.pos}"
            )
        return node

    # alternation  :=  concatenation ( '|' concatenation )*
    def _alternation(self):
        options = [self._concatenation()]
        while self.pos < len(self.pattern) and self.pattern[self.pos] == '|':
            self.pos += 1
            options.append(self._concatenation())
        return options[0] if len(options) == 1 else ('alt', options)

    # concatenation :=  quantified_atom *
    def _concatenation(self):
        nodes = []
        while self.pos < len(self.pattern) and self.pattern[self.pos] not in ')|':
            nodes.append(self._quantified_atom())
        if len(nodes) == 0:
            return ('lit', '')          # empty alternative
        return nodes[0] if len(nodes) == 1 else ('cat', nodes)

    # quantified_atom := atom ( '+' | '*' | '?' | '{n}' | '{n,m}' )?
    def _quantified_atom(self):
        node = self._atom()
        if self.pos >= len(self.pattern):
            return node
        c = self.pattern[self.pos]
        if c == '+':
            self.pos += 1
            return ('rep', node, 1, MAX_REPEAT)
        if c == '*':
            self.pos += 1
            return ('rep', node, 0, MAX_REPEAT)
        if c == '?':
            self.pos += 1
            return ('rep', node, 0, 1)
        if c == '{':
            self.pos += 1
            m = stdlib_re.match(r'(\d+)(?:,(\d+))?}', self.pattern[self.pos:])
            if not m:
                raise ValueError(f"Malformed quantifier at position {self.pos}")
            self.pos += len(m.group(0))
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) else lo
            return ('rep', node, lo, hi)
        return node

    # atom := literal | '(' alternation ')'
    def _atom(self):
        c = self.pattern[self.pos]
        if c == '(':
            self.pos += 1          # consume '('
            node = self._alternation()
            if self.pos >= len(self.pattern) or self.pattern[self.pos] != ')':
                raise ValueError("Missing closing ')'")
            self.pos += 1          # consume ')'
            return node
        # ordinary literal character
        self.pos += 1
        return ('lit', c)


def parse_regex(pattern: str):
    return Parser(pattern).parse()


# ─────────────────────────────────────────────────────────────────────────────
# 3.  GENERATOR  (plain)
# ─────────────────────────────────────────────────────────────────────────────

def generate(node) -> str:
    kind = node[0]
    if kind == 'lit':
        return node[1]
    if kind == 'cat':
        return ''.join(generate(child) for child in node[1])
    if kind == 'alt':
        return generate(random.choice(node[1]))
    if kind == 'rep':
        _, child, lo, hi = node
        count = random.randint(lo, hi)
        return ''.join(generate(child) for _ in range(count))
    raise ValueError(f"Unknown AST node kind: {kind}")


def generate_string(pattern: str) -> str:
    """Generate one valid random string for the given regex pattern."""
    return generate(parse_regex(pattern))


# ─────────────────────────────────────────────────────────────────────────────
# 4.  GENERATOR WITH TRACE  (bonus)
# ─────────────────────────────────────────────────────────────────────────────

def generate_traced(node, trace: list, depth: int = 0) -> str:
    """Generate a string and record every decision taken."""
    indent = "  " * depth
    kind = node[0]

    if kind == 'lit':
        trace.append(f"{indent}Literal  → emit '{node[1]}'")
        return node[1]

    if kind == 'cat':
        trace.append(f"{indent}Concat ({len(node[1])} parts)")
        return ''.join(generate_traced(child, trace, depth + 1) for child in node[1])

    if kind == 'alt':
        chosen = random.choice(node[1])
        labels = _node_label(node)
        trace.append(f"{indent}Alternation {labels}  → chose: {_node_label(chosen)}")
        return generate_traced(chosen, trace, depth + 1)

    if kind == 'rep':
        _, child, lo, hi = node
        count = random.randint(lo, hi)
        trace.append(
            f"{indent}Repeat [{lo}..{hi}]  → chose {count} repetition(s)"
        )
        parts = []
        for i in range(count):
            trace.append(f"{indent}  iteration {i + 1}")
            parts.append(generate_traced(child, trace, depth + 2))
        return ''.join(parts)

    raise ValueError(f"Unknown AST node kind: {kind}")


def _node_label(node) -> str:
    """Human-readable summary of an AST node."""
    kind = node[0]
    if kind == 'lit':
        return f"'{node[1]}'"
    if kind == 'cat':
        return f"({' · '.join(_node_label(c) for c in node[1])})"
    if kind == 'alt':
        return f"({'|'.join(_node_label(c) for c in node[1])})"
    if kind == 'rep':
        return f"{_node_label(node[1])}{{{node[2]},{node[3]}}}"
    return '?'


def generate_with_trace(pattern: str):
    """
    Returns (generated_string, trace_lines).
    trace_lines is a list of strings describing the generation steps.
    """
    ast = parse_regex(pattern)
    trace = [f"Pattern : {pattern}",
             f"AST root: {_node_label(ast)}",
             "─" * 50]
    result = generate_traced(ast, trace)
    trace.append("─" * 50)
    trace.append(f"Result  : {result}")
    return result, trace


# ─────────────────────────────────────────────────────────────────────────────
# 5.  VARIANT 4 DEFINITIONS & DEMO
# ─────────────────────────────────────────────────────────────────────────────

VARIANT_4_PATTERNS = [
    "S(U|V)W+Y(2|4)+",
    "L(M|N)O+P+Q(2|3)",
    "R+S(T|U)W(X|Y)+",
]

SAMPLES_PER_PATTERN = 8


def demo():
    separator = "═" * 60

    print(separator)
    print("  Lab 4 – Regular Expressions  |  Variant 4")
    print(separator)

    for idx, pattern in enumerate(VARIANT_4_PATTERNS, start=1):
        print(f"\n{'─'*60}")
        print(f"  Regex {idx} : {pattern}")
        print(f"{'─'*60}")

        print(f"\n  {SAMPLES_PER_PATTERN} generated strings:")
        for _ in range(SAMPLES_PER_PATTERN):
            print(f"    {generate_string(pattern)}")

        # ── Bonus: one detailed trace ──────────────────────────────────────
        print(f"\n  [Bonus] Step-by-step trace of one generation:")
        _, trace = generate_with_trace(pattern)
        for line in trace:
            print(f"    {line}")

    print(f"\n{separator}")
    print("  Custom pattern demo (you can change these):")
    print(separator)
    custom = [
        ("AB(C|D){2,3}E", 5),
        ("(X|Y|Z)+", 5),
        ("A?B*C+", 5),
    ]
    for pat, n in custom:
        samples = [generate_string(pat) for _ in range(n)]
        print(f"  {pat:20s}  →  {samples}")

    print()


if __name__ == "__main__":
    random.seed()   # real randomness each run
    demo()