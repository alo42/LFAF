"""
Lab 2 – Variant 16
===================
Q  = {q0, q1, q2, q3}
Σ  = {a, b}
F  = {q3}
δ(q0, a) = q1
δ(q1, b) = q1   ←┐ NDFA: same (state, symbol) → two different states
δ(q1, b) = q2   ←┘
δ(q2, a) = q2
δ(q2, b) = q3
δ(q0, b) = q0
"""

from finite_automaton import FiniteAutomaton


def main():
    states       = {'q0', 'q1', 'q2', 'q3'}
    alphabet     = {'a', 'b'}
    start_state  = 'q0'
    accept_states = {'q3'}

    # Note: δ(q1, b) = q1  AND  δ(q1, b) = q2  →  represented as a SET
    transitions = {
        ('q0', 'a'): {'q1'},
        ('q0', 'b'): {'q0'},
        ('q1', 'b'): {'q1', 'q2'},   # non-deterministic branch
        ('q2', 'a'): {'q2'},
        ('q2', 'b'): {'q3'},
    }

    ndfa = FiniteAutomaton(states, alphabet, transitions, start_state, accept_states)
    ndfa.display("Variant 16 – Original NDFA")

    print("\n--- Determinism Check ---")
    print(ndfa.determinism_report())

    print("\n--- FA → Regular Grammar ---")
    grammar = ndfa.to_regular_grammar()
    grammar.display()


    print("\n--- NDFA → DFA (Subset Construction) ---")
    dfa = ndfa.to_dfa()
    dfa.display("Equivalent DFA")

    print("\n  DFA determinism check:", "PASS ✓" if dfa.is_deterministic() else "FAIL ✗")



if __name__ == "__main__":
    main()