class FiniteAutomaton:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        # Q, Σ, δ, q0, F
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = final_states

    def string_belong_to_language(self, input_string):
        """
        Checks if the input string is accepted by the automaton.
        """
        current_state = self.start_state

        for symbol in input_string:
            if (current_state, symbol) not in self.transitions:
                return False
            current_state = self.transitions[(current_state, symbol)]

        return current_state in self.final_states
