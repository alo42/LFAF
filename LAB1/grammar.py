import random

class Grammar:
    def __init__(self):
        # VN, VT, P, S
        self.non_terminals = {"S", "A", "B"}
        self.terminals = {"a", "b", "c", "d"}
        self.start_symbol = "S"

        self.productions = {
            "S": ["bS", "dA"],
            "A": ["aA", "dB", "b"],
            "B": ["cB", "a"]
        }

    def generate_string(self):
        """
        Generates one valid string from the grammar.
        """
        current = self.start_symbol

        while any(symbol in self.non_terminals for symbol in current):
            new_string = ""
            for symbol in current:
                if symbol in self.non_terminals:
                    new_string += random.choice(self.productions[symbol])
                else:
                    new_string += symbol
            current = new_string

        return current

    def to_finite_automaton(self):
        """
        Converts this grammar to an equivalent finite automaton.
        """
        states = {"S", "A", "B", "F"}
        alphabet = self.terminals
        start_state = "S"
        final_states = {"F"}

        transitions = {
            ("S", "b"): "S",
            ("S", "d"): "A",

            ("A", "a"): "A",
            ("A", "d"): "B",
            ("A", "b"): "F",

            ("B", "c"): "B",
            ("B", "a"): "F"
        }

        return FiniteAutomaton(
            states,
            alphabet,
            transitions,
            start_state,
            final_states
        )
