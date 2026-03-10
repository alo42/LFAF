from collections import defaultdict
from grammar import Grammar


class FiniteAutomaton:
    """
    Represents a (possibly non-deterministic) finite automaton and provides:
      - Conversion to a regular grammar
      - Determinism check
      - NDFA → DFA conversion via subset construction
      - Graphical representation via Graphviz (optional)
    """

    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        """
        :param states:        set of state names,       e.g. {'q0','q1','q2','q3'}
        :param alphabet:      set of input symbols,     e.g. {'a','b'}
        :param transitions:   dict (state, symbol) -> set(states)
                              e.g. {('q1','b'): {'q1','q2'}}
        :param start_state:   str,                      e.g. 'q0'
        :param accept_states: set of accepting states,  e.g. {'q3'}
        """
        self.states        = set(states)
        self.alphabet      = set(alphabet)
        self.transitions   = transitions        # {(state, sym): set(states)}
        self.start_state   = start_state
        self.accept_states = set(accept_states)

    # ------------------------------------------------------------------
    # 1.  FA → Regular Grammar
    # ------------------------------------------------------------------

    def to_regular_grammar(self) -> Grammar:
        """
        Converts this FA to a right-linear regular grammar.

        Rules:
          For every δ(q, a) ∋ p  →  production  q → a p
          For every accepting state q              →  production  q → ε
        """
        non_terminals = self.states
        terminals     = self.alphabet
        productions   = defaultdict(list)

        for (state, symbol), next_states in self.transitions.items():
            for nxt in next_states:
                productions[state].append(f"{symbol}{nxt}")

        # ε-productions for accepting states (marks end of a word)
        for state in self.accept_states:
            productions[state].append('ε')

        return Grammar(
            non_terminals=non_terminals,
            terminals=terminals,
            productions=dict(productions),
            start_symbol=self.start_state,
        )

    # ------------------------------------------------------------------
    # 2.  Determinism Check
    # ------------------------------------------------------------------

    def is_deterministic(self) -> bool:
        """
        An FA is deterministic (DFA) iff every (state, symbol) pair has
        at most one next state.
        """
        for (state, symbol), next_states in self.transitions.items():
            if len(next_states) > 1:
                return False
        return True

    def determinism_report(self) -> str:
        """Human-readable explanation of why the FA is (non-)deterministic."""
        violations = []
        for (state, symbol), next_states in self.transitions.items():
            if len(next_states) > 1:
                violations.append(
                    f"  δ({state}, {symbol}) = {set(next_states)}  ← multiple targets"
                )
        if violations:
            lines = ["The automaton is NON-DETERMINISTIC (NDFA)."]
            lines.append("Offending transitions:")
            lines.extend(violations)
            return "\n".join(lines)
        return "The automaton is DETERMINISTIC (DFA)."

    # ------------------------------------------------------------------
    # 3.  NDFA → DFA  (Subset / Powerset Construction)
    # ------------------------------------------------------------------

    def to_dfa(self) -> "FiniteAutomaton":
        """
        Converts the NDFA to an equivalent DFA using the subset construction.

        DFA states are frozensets of NDFA states.
        Transitions that lead nowhere are simply omitted — no dead/sink state.
        """
        start_dfa  = frozenset([self.start_state])
        worklist   = [start_dfa]
        visited    = set()
        dfa_trans  = {}      # {(frozenset, sym): frozenset} — only non-empty targets

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
                # Skip transitions that lead nowhere — no dead state needed
                if not reached:
                    continue
                dfa_trans[(current, sym)] = reached
                if reached not in visited:
                    worklist.append(reached)

        # Build human-readable state names
        def name(fs: frozenset) -> str:
            return "{" + ",".join(sorted(fs)) + "}"

        dfa_states       = {name(s) for s in visited}
        dfa_start        = name(start_dfa)
        dfa_accept       = {name(s) for s in visited
                            if s & self.accept_states}
        dfa_transitions  = {}
        for (fs, sym), target in dfa_trans.items():
            src = name(fs)
            tgt = name(target)
            dfa_transitions.setdefault((src, sym), set()).add(tgt)

        return FiniteAutomaton(
            states        = dfa_states,
            alphabet      = self.alphabet,
            transitions   = dfa_transitions,
            start_state   = dfa_start,
            accept_states = dfa_accept,
        )

    # ------------------------------------------------------------------
    # 4.  Graphical Representation  (requires graphviz Python package)
    # ------------------------------------------------------------------

    def render_graph(self, filename: str = "automaton", view: bool = False):
        """
        Renders the automaton as a PNG/PDF via the graphviz package.
        Falls back gracefully if graphviz is not installed.
        """
        try:
            import graphviz  # type: ignore
        except ImportError:
            print("[render_graph] graphviz package not found. "
                  "Install with:  pip install graphviz")
            return

        dot = graphviz.Digraph(name=filename, format="png")
        dot.attr(rankdir="LR")

        # Invisible start arrow
        dot.node("__start__", shape="none", label="")
        dot.edge("__start__", self.start_state)

        # States
        for state in self.states:
            shape = "doublecircle" if state in self.accept_states else "circle"
            dot.node(state, shape=shape)

        # Transitions – group parallel edges with combined labels
        edge_labels: dict[tuple, list] = defaultdict(list)
        for (state, sym), next_states in self.transitions.items():
            for nxt in next_states:
                edge_labels[(state, nxt)].append(sym)

        for (src, tgt), syms in edge_labels.items():
            dot.edge(src, tgt, label=", ".join(sorted(syms)))

        path = dot.render(filename=filename, cleanup=True, view=view)
        print(f"[render_graph] Saved to {path}")

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def display(self, title: str = "Finite Automaton"):
        print(f"\n=== {title} ===")
        print(f"  States        : {sorted(self.states)}")
        print(f"  Alphabet      : {sorted(self.alphabet)}")
        print(f"  Start state   : {self.start_state}")
        print(f"  Accept states : {sorted(self.accept_states)}")
        print("  Transitions:")
        for (state, sym), nexts in sorted(self.transitions.items()):
            print(f"    δ({state}, {sym}) = {sorted(nexts)}")