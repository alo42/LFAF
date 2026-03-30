# Lab 4 – Regular Expressions

**Course:** Formal Languages & Finite Automata

**Author:** Mutu Adrian

---

## Theory

A **regular expression** (regex) is a formal notation for describing a **regular language** — a set of strings accepted by a finite automaton. Regular expressions are the algebraic counterpart of deterministic finite automata (DFA) and non-deterministic finite automata (NFA): by Kleene's theorem, any language recognised by a DFA can be described by a regex, and vice versa.

Three primitive operations define the algebra of regular expressions over an alphabet `Σ`:

1) **Concatenation** — the language formed by appending every string of one set to every string of another: `RS`

2) **Union (alternation)** — the language containing strings from either set: `R | S`

3) **Kleene star (closure)** — zero or more repetitions of a language: `R*`

Practical regex engines extend these three operations with additional conveniences:

- `+` (one or more) — equivalent to `RR*`
- `?` (zero or one) — equivalent to `R | ε`
- `{n}` / `{n,m}` — exact or bounded repetition
- Character classes: `[a-z]`, `[0-9]`, `.`

Regular expressions occupy the bottom of the **Chomsky hierarchy** (Type-3 grammars). This means they are strictly less expressive than context-free grammars and cannot, for example, describe balanced parentheses or palindromes. Their power is matched precisely by the class of languages recognisable by finite automata — which makes them ideal for tokenisation, pattern matching, and input validation.

In software, regex engines are used extensively in lexers (tokenisers), text editors, command-line tools (`grep`, `sed`), form validation, and network protocol parsing. Most modern engines are based on the **Thompson NFA construction**, which compiles a regex into an NFA in O(n) time and matches strings in O(nm) time.

---

## Objectives

1. Understand what regular expressions are and how they relate to finite automata and formal grammars.
2. Below you will find 3 complex regular expressions for Variant 4. Take the variant and do the following:

   a) Write a code that will generate valid combinations of symbols conforming to the given regular expressions. The idea is to interpret the given regular expressions dynamically, not to hardcode the way it will generate valid strings.

   b) In case you have an example where a symbol may be written an undefined number of times, take a limit of 5 times (to avoid generation of extremely long combinations).

   c) **Bonus point**: write a function that will show the sequence of processing the regular expression (what you do first, second, and so on).

3. Demonstrate the generator on all three Variant 4 patterns, producing multiple valid outputs for each.

---

## Variant 4 – Regular Expressions

The three patterns for Variant 4 were reverse-engineered from the example outputs provided in the task sheet:

| # | Pattern | Description | Example outputs |
|---|---------|-------------|-----------------|
| 1 | `S(U\|V)W+Y(2\|4)+` | S, choice of U/V, one-or-more W, Y, one-or-more of 2 or 4 | `SVWWY4`, `SUWWWWWY22442` |
| 2 | `L(M\|N)O+P+Q(2\|3)` | L, choice of M/N, one-or-more O, one-or-more P, Q, digit 2 or 3 | `LMOOOPPQ3`, `LNOOOOPQ2` |
| 3 | `R+S(T\|U)W(X\|Y)+` | One-or-more R, S, choice of T/U, W, one-or-more of X or Y | `RSTWXX`, `RRRSUWYY` |

---

## Implementation Description

### Overview (`lab4_regex.py`)

The implementation is split into three logical layers: a **parser** that converts a pattern string into an abstract syntax tree (AST), a **generator** that walks the AST and randomly produces a conforming string, and a **trace generator** (bonus) that does the same while recording every decision taken along the way.

---

### Supported Regex Syntax

| Construct | Meaning |
|-----------|---------|
| `a  b  c  …` | Literal character — emit exactly this symbol |
| `(a\|b\|c)` | Alternation — randomly choose one branch |
| `(abc)` | Grouping — treat the sub-expression as a unit |
| `R+` | One or more repetitions (capped at MAX_REPEAT = 5) |
| `R*` | Zero or more repetitions (capped at MAX_REPEAT = 5) |
| `R?` | Zero or one repetition |
| `{n}` | Exactly n repetitions |
| `{n,m}` | Between n and m repetitions (inclusive, random) |

---

### AST Node Types

The parser represents every sub-expression as a plain Python tuple — a lightweight, immutable tree structure. There are four node kinds:

```python
('lit',  char)          # a single literal character to emit
('cat',  [nodes])       # concatenation: generate each child left-to-right
('alt',  [nodes])       # alternation: pick one child uniformly at random
('rep',  node, lo, hi)  # repetition: generate child between lo and hi times
```

---

### Parser

The `Parser` class implements a classic **recursive-descent** parser. It maintains a single integer cursor (`self.pos`) that advances through the pattern string as each sub-expression is consumed. Four mutually recursive methods correspond to the four levels of regex precedence:

- `_alternation()` — lowest precedence; splits on `|` between calls to `_concatenation()`
- `_concatenation()` — concatenates consecutive atoms by looping until it sees `)` or `|`
- `_quantified_atom()` — reads one atom, then checks for a trailing quantifier (`+  *  ?  {n,m}`)
- `_atom()` — either a parenthesised sub-expression or a single literal character

```python
class Parser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    def parse(self):
        node = self._alternation()
        if self.pos != len(self.pattern):
            raise ValueError(f'Unexpected char at pos {self.pos}')
        return node

    def _alternation(self):
        options = [self._concatenation()]
        while self.pos < len(self.pattern) and self.pattern[self.pos] == '|':
            self.pos += 1
            options.append(self._concatenation())
        return options[0] if len(options) == 1 else ('alt', options)

    def _concatenation(self):
        nodes = []
        while self.pos < len(self.pattern) and self.pattern[self.pos] not in ')|':
            nodes.append(self._quantified_atom())
        if len(nodes) == 0: return ('lit', '')
        return nodes[0] if len(nodes) == 1 else ('cat', nodes)

    def _quantified_atom(self):
        node = self._atom()
        c = self.pattern[self.pos] if self.pos < len(self.pattern) else ''
        if c == '+': self.pos += 1; return ('rep', node, 1, MAX_REPEAT)
        if c == '*': self.pos += 1; return ('rep', node, 0, MAX_REPEAT)
        if c == '?': self.pos += 1; return ('rep', node, 0, 1)
        if c == '{':
            self.pos += 1
            m = re.match(r'(\d+)(?:,(\d+))?}', self.pattern[self.pos:])
            self.pos += len(m.group(0))
            lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
            return ('rep', node, lo, hi)
        return node

    def _atom(self):
        c = self.pattern[self.pos]
        if c == '(':
            self.pos += 1
            node = self._alternation()
            self.pos += 1   # consume ')'
            return node
        self.pos += 1
        return ('lit', c)
```

---

### Generator

The `generate(node)` function recursively walks the AST. Each node kind is handled by a short branch:

```python
def generate(node) -> str:
    kind = node[0]
    if kind == 'lit':
        return node[1]                                      # emit the character
    if kind == 'cat':
        return ''.join(generate(c) for c in node[1])       # concat children
    if kind == 'alt':
        return generate(random.choice(node[1]))             # pick one branch
    if kind == 'rep':
        _, child, lo, hi = node
        count = random.randint(lo, hi)                      # random repetition count
        return ''.join(generate(child) for _ in range(count))
```

The `MAX_REPEAT = 5` constant is applied at parse time: every `+` becomes `('rep', node, 1, 5)` and every `*` becomes `('rep', node, 0, 5)`. This guarantees that generated strings are always finite and reasonably short, as required by the task.

---

### Trace Generator (Bonus)

`generate_with_trace(pattern)` returns both the generated string and a list of human-readable log lines describing each decision. It mirrors the plain generator but passes a `trace` list into a recursive helper that appends one entry per node visit:

```python
def generate_traced(node, trace, depth=0):
    indent = '  ' * depth
    kind = node[0]
    if kind == 'lit':
        trace.append(f"{indent}Literal  -> emit '{node[1]}'")
        return node[1]
    if kind == 'alt':
        chosen = random.choice(node[1])
        trace.append(f"{indent}Alternation -> chose: {_node_label(chosen)}")
        return generate_traced(chosen, trace, depth + 1)
    if kind == 'rep':
        _, child, lo, hi = node
        count = random.randint(lo, hi)
        trace.append(f"{indent}Repeat [{lo}..{hi}] -> chose {count} repetition(s)")
        parts = []
        for i in range(count):
            trace.append(f"{indent}  iteration {i + 1}")
            parts.append(generate_traced(child, trace, depth + 2))
        return ''.join(parts)
```

---

## Results

The generator was run for each of the three Variant 4 patterns, producing 8 random strings per pattern. A full step-by-step trace was also captured for one run of each pattern.

---

### Regex 1 – `S(U|V)W+Y(2|4)+`

**Generated strings:**
```
SVWWY4
SUWWWWWY22442
SUWWWWWY22
SUWWWWWY22442
SUWWWWWY42
SVWY224
SVWWWY4222
SVWWY2442
```

**Sample trace:**
```
Pattern : S(U|V)W+Y(2|4)+
AST root: ('S' . ('U'|'V') . 'W'{1,5} . 'Y' . ('2'|'4'){1,5})
--------------------------------------------------
Concat (5 parts)
  Literal  -> emit 'S'
  Alternation ('U'|'V')  -> chose: 'V'
    Literal  -> emit 'V'
  Repeat [1..5]  -> chose 2 repetition(s)
    iteration 1  -> emit 'W'
    iteration 2  -> emit 'W'
  Literal  -> emit 'Y'
  Repeat [1..5]  -> chose 3 repetition(s)
    iteration 1
      Alternation ('2'|'4')  -> chose: '4'  -> emit '4'
    iteration 2
      Alternation ('2'|'4')  -> chose: '2'  -> emit '2'
    iteration 3
      Alternation ('2'|'4')  -> chose: '4'  -> emit '4'
--------------------------------------------------
Result  : SVWWY424
```

The alternation `(U|V)` selects one of the two options uniformly at random. The `W+` quantifier is evaluated as `Repeat [1..5]`, ensuring at least one `W` is always emitted. The trailing `(2|4)+` loops independently, so any combination of `2` and `4` of length 1–5 is valid.

---

### Regex 2 – `L(M|N)O+P+Q(2|3)`

**Generated strings:**
```
LMOOOPPQ3
LMOOPPPPQ3
LMOOOOPPQ3
LNOPPQ2
LMOOOOOPPQ3
LMOOOOOPPPQ3
LNOOOOPQ3
LNOOOPQ2
```

**Sample trace:**
```
Pattern : L(M|N)O+P+Q(2|3)
AST root: ('L' . ('M'|'N') . 'O'{1,5} . 'P'{1,5} . 'Q' . ('2'|'3'))
--------------------------------------------------
Concat (6 parts)
  Literal  -> emit 'L'
  Alternation ('M'|'N')  -> chose: 'M'
    Literal  -> emit 'M'
  Repeat [1..5]  -> chose 3 repetition(s)
    iteration 1  -> emit 'O'
    iteration 2  -> emit 'O'
    iteration 3  -> emit 'O'
  Repeat [1..5]  -> chose 4 repetition(s)
    iteration 1  -> emit 'P'
    iteration 2  -> emit 'P'
    iteration 3  -> emit 'P'
    iteration 4  -> emit 'P'
  Literal  -> emit 'Q'
  Alternation ('2'|'3')  -> chose: '3'
    Literal  -> emit '3'
--------------------------------------------------
Result  : LMOOOPPPPQ3
```

This pattern has two independent repetition runs (`O+` and `P+`). Each is resolved separately, so the number of `O`s and `P`s in any generated string are independently random. The final alternation `(2|3)` occurs exactly once because there is no quantifier after its closing parenthesis.

---

### Regex 3 – `R+S(T|U)W(X|Y)+`

**Generated strings:**
```
RRRRRSUWXYXXX
RRRRSTWYYXX
RRRSTWYY
RRSTWX
RRSTWY
RRRRRSTWXYXX
RRRRRSUWX
RRRRRSUWYY
```

**Sample trace:**
```
Pattern : R+S(T|U)W(X|Y)+
AST root: ('R'{1,5} . 'S' . ('T'|'U') . 'W' . ('X'|'Y'){1,5})
--------------------------------------------------
Concat (5 parts)
  Repeat [1..5]  -> chose 2 repetition(s)
    iteration 1  -> emit 'R'
    iteration 2  -> emit 'R'
  Literal  -> emit 'S'
  Alternation ('T'|'U')  -> chose: 'U'
    Literal  -> emit 'U'
  Literal  -> emit 'W'
  Repeat [1..5]  -> chose 3 repetition(s)
    iteration 1
      Alternation ('X'|'Y')  -> chose: 'X'  -> emit 'X'
    iteration 2
      Alternation ('X'|'Y')  -> chose: 'Y'  -> emit 'Y'
    iteration 3
      Alternation ('X'|'Y')  -> chose: 'X'  -> emit 'X'
--------------------------------------------------
Result  : RRSUWXYX
```

The leading `R+` produces between 1 and 5 `R` characters. The trailing `(X|Y)+` independently selects each character, so `XY`, `XYXX`, or `YY` are all valid suffixes.

---

## Conclusions

1. A **recursive-descent parser** is a clean and extensible approach for interpreting a regex subset at run time. The grammar's natural precedence hierarchy (alternation < concatenation < quantification < atom) maps directly onto the four mutually recursive parse methods with no ambiguity.
2. Building an **AST as an intermediate representation** decouples parsing from generation entirely. The same parsed tree can be reused for generation, tracing, validation, or any other purpose without re-parsing the pattern.
3. **Capping unbounded quantifiers** (`+`, `*`) at `MAX_REPEAT = 5` is essential for practical use: without an upper bound the generator could produce strings of arbitrary length. The cap is applied once at parse time, so the generator logic itself remains simple and uncluttered.
4. The **step-by-step trace** (bonus) is valuable both as a debugging aid and as a learning tool — it makes the normally invisible decision process of the regex engine explicit and human-readable at every level of the recursion.
5. All three Variant 4 patterns produce outputs that match the task's provided examples. The generation is genuinely dynamic: the program accepts any pattern string from the supported subset and generates valid strings without any pattern-specific code.
6. Extending the implementation to cover further regex features (character classes such as `[a-z]`, anchors such as `^` and `$`, or named groups) would require adding new AST node types and corresponding branches in the parser and generator — the architecture supports such extension cleanly.

---

## References

1) Cojuhari I., Drumea V. *Formal Languages and Finite Automata – Guide for practical lessons.* Technical University of Moldova, 2022.
2) Sipser M. *Introduction to the Theory of Computation*, 3rd ed. Cengage Learning, 2012.
3) Thompson K. Programming Techniques: Regular expression search algorithm. *Communications of the ACM*, 11(6):419–422, 1968.
4) Python Software Foundation. *re — Regular expression operations.* https://docs.python.org/3/library/re.html
5) Wikipedia. *Regular expression.* https://en.wikipedia.org/wiki/Regular_expression