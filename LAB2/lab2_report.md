# Lab 2 – Determinism in Finite Automata. Conversion from NDFA to DFA. Chomsky Hierarchy.

**Course:** Formal Languages & Finite Automata

**Author:** Mutu Adrian

---

## Theory

A finite automaton is a mathematical model of computation that processes strings over an alphabet by moving through a finite set of states. It has a designated start state and one or more accepting (final) states. When every (state, symbol) pair leads to at most one next state, the automaton is called **deterministic (DFA)**; when a pair can lead to multiple states simultaneously, it is **non-deterministic (NDFA)**. Despite this difference in structure, every NDFA has an equivalent DFA, constructible via the **subset (powerset) construction** — each DFA state represents a set of NDFA states that could be active simultaneously.

The **Chomsky hierarchy** classifies formal grammars into four types based on the shape of their production rules:

**Type 3 – Regular:** productions of the form `A → aB` or `A → a` (right-linear), recognized by finite automata.
**Type 2 – Context-Free:** productions of the form `A → α`, recognized by pushdown automata.
**Type 1 – Context-Sensitive:** productions where `|LHS| ≤ |RHS|`, recognized by linear-bounded automata.
**Type 0 – Unrestricted:** no restrictions, recognized by Turing machines.

---

## Objectives

1. Understand what a finite automaton is and what it can be used for.
2. Provide a function in the `Grammar` class that classifies the grammar based on the Chomsky hierarchy.
3. Implement conversion of a finite automaton to a regular grammar.
4. Determine whether the FA (Variant 16) is deterministic or non-deterministic.
5. Implement conversion from NDFA to DFA using the subset construction algorithm.
6. (Bonus) Represent the finite automaton graphically using the `graphviz` library.

---

## Implementation Description

### Grammar class (`grammar.py`)

The `Grammar` class stores non-terminals, terminals, productions and the start symbol. Its main method `classify_chomsky()` tests the most restrictive type first and returns the first type whose conditions are satisfied.

```python
def classify_chomsky(self) -> str:
    if self._is_regular():
        return "Type 3 – Regular Grammar"
    if self._is_context_free():
        return "Type 2 – Context-Free Grammar"
    if self._is_context_sensitive():
        return "Type 1 – Context-Sensitive Grammar"
    return "Type 0 – Unrestricted Grammar (Recursively Enumerable)"
```

The `_is_regular()` helper checks that every LHS is a single non-terminal and every RHS matches either the right-linear pattern (`terminals* NT?`) or the left-linear pattern (`NT? terminals*`), using a greedy longest-match scan that correctly handles multi-character symbols like `q0`, `q1`.

```python
def _is_regular(self) -> bool:
    right_linear = True
    left_linear  = True
    for lhs, rhs_list in self.productions.items():
        if lhs not in self.non_terminals:
            return False
        for rhs in rhs_list:
            if rhs in ('ε', ''):
                continue
            if not self._matches_right_linear(rhs):
                right_linear = False
            if not self._matches_left_linear(rhs):
                left_linear = False
    return right_linear or left_linear
```

---

### FiniteAutomaton class (`finite_automaton.py`)

Transitions are stored as `dict[(state, symbol) → set(states)]`, which naturally represents non-determinism without any special casing — a deterministic transition is simply a set of size one.

#### FA → Regular Grammar

Each transition `δ(q, a) ∋ p` becomes production `q → a p`. Each accepting state gets `q → ε` to mark the end of a valid word.

```python
def to_regular_grammar(self) -> Grammar:
    productions = defaultdict(list)
    for (state, symbol), next_states in self.transitions.items():
        for nxt in next_states:
            productions[state].append(f"{symbol}{nxt}")
    for state in self.accept_states:
        productions[state].append('ε')
    return Grammar(self.states, self.alphabet, dict(productions), self.start_state)
```

#### Determinism Check

The automaton is deterministic if and only if every `(state, symbol)` pair maps to at most one state.

```python
def is_deterministic(self) -> bool:
    for (state, symbol), next_states in self.transitions.items():
        if len(next_states) > 1:
            return False
    return True
```

#### NDFA → DFA (Subset Construction)

Starting from `{q0}`, the algorithm computes for each DFA state (a frozenset of NDFA states) and each symbol the union of all reachable NDFA states. New subsets are added to a worklist until no new states appear. The empty frozenset `∅` acts as the sink/dead state.

```python
def to_dfa(self) -> "FiniteAutomaton":
    DEAD = frozenset()
    start_dfa = frozenset([self.start_state])
    worklist, visited, dfa_trans = [start_dfa], set(), {}

    while worklist:
        current = worklist.pop()
        if current in visited:
            continue
        visited.add(current)
        for sym in self.alphabet:
            reached = frozenset(
                nxt
                for state in current
                for nxt in self.transitions.get((state, sym), set())
            )
            dfa_trans[(current, sym)] = reached
            if reached not in visited:
                worklist.append(reached)
    # ... state naming and FiniteAutomaton construction
```

#### Graphical Representation (Bonus)

The `render_graph()` method uses the `graphviz` Python package to produce a PNG diagram. Accepting states are drawn with a double circle; parallel edges between the same pair of states are merged into a single labelled arrow.

```python
def render_graph(self, filename: str = "automaton", view: bool = False):
    import graphviz
    dot = graphviz.Digraph(name=filename, format="png")
    dot.attr(rankdir="LR")
    for state in self.states:
        shape = "doublecircle" if state in self.accept_states else "circle"
        dot.node(state, shape=shape)
    # ... edges grouped by (src, tgt) with combined labels
    dot.render(filename=filename, cleanup=True, view=view)
```

---

## Conclusions / Screenshots / Results

Running `main.py` for **Variant 16** produces the following output:

```
=== Variant 16 – Original NDFA ===
  States        : ['q0', 'q1', 'q2', 'q3']
  Alphabet      : ['a', 'b']
  Start state   : q0
  Accept states : ['q3']
  Transitions:
    δ(q0, a) = ['q1']
    δ(q0, b) = ['q0']
    δ(q1, b) = ['q1', 'q2']   ← non-deterministic
    δ(q2, a) = ['q2']
    δ(q2, b) = ['q3']

--- Determinism Check ---
The automaton is NON-DETERMINISTIC (NDFA).
Offending transitions:
  δ(q1, b) = {'q2', 'q1'}  ← multiple targets

--- FA → Regular Grammar ---
  Productions:
    q0 → aq1 | bq0
    q1 → bq1 | bq2
    q2 → aq2 | bq3
    q3 → ε
  Chomsky class : Type 3 – Regular Grammar

--- NDFA → DFA (Subset Construction) ---
  States: {q0}, {q1}, {q2}, {q3}, {q1,q2}, {q1,q2,q3}, ∅
  Accept states: {q3}, {q1,q2,q3}

  δ({q0},       a) = {q1}
  δ({q0},       b) = {q0}
  δ({q1},       b) = {q1,q2}
  δ({q1,q2},    a) = {q2}
  δ({q1,q2},    b) = {q1,q2,q3}
  δ({q1,q2,q3}, a) = {q2}
  δ({q1,q2,q3}, b) = {q1,q2,q3}
  δ({q2},       a) = {q2}
  δ({q2},       b) = {q3}
  δ({q3},       a) = ∅
  δ({q3},       b) = ∅
  δ(∅,          a) = ∅
  δ(∅,          b) = ∅

  DFA determinism check: PASS ✓
```



**Key conclusions:**

1. Variant 16's FA is **non-deterministic** because `δ(q1, b)` leads to two states (`q1` and `q2`) simultaneously.
2. The derived grammar is **Type 3 – Regular**, as all productions are right-linear (`A → aB` or `A → ε`).
3. The subset construction expands the original **4-state NDFA** into a **7-state DFA** (including the sink state `∅` and the compound accepting state `{q1,q2,q3}`).
4. The resulting DFA is verified deterministic — every `(state, symbol)` pair has exactly one target.

---

## References

- Cojuhari I., Drumea V. *Formal Languages and Finite Automata – Guide for practical lessons.* Technical University of Moldova, 2022.
- Hopcroft J.E., Motwani R., Ullman J.D. *Introduction to Automata Theory, Languages, and Computation.* 3rd ed. Pearson, 2006.
- Python `graphviz` package documentation: https://graphviz.readthedocs.io