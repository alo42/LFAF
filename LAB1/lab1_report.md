# 1_RegularGrammars

**Course:** Formal Languages & Finite Automata  
**Author:** Adrian Mutu  

---

## Theory

A formal language is a set of strings formed from a finite alphabet according to specific production rules.  
In this laboratory work, a regular grammar was implemented and converted into a finite automaton.

---

## Objectives

1. Understand what a formal grammar is.
2. Implement a grammar in Python.
3. Generate valid strings from the grammar.
4. Convert the grammar into a finite automaton.
5. Check whether a string belongs to the language.

---

## Implementation description

### Grammar Class

The `Grammar` class stores non-terminals, terminals, production rules and the start symbol.  
It contains methods for generating valid strings and converting the grammar into a finite automaton.

```python
class Grammar:
    def __init__(self):
        self.non_terminals = {"S", "A", "B"}
        self.terminals = {"a", "b", "c", "d"}
        self.start_symbol = "S" '''
```
---

### Finite Automaton Class

The `FiniteAutomaton` class represents the equivalent automaton of the grammar.  
It stores the set of states, alphabet, transition function, start state, and final states.  
The method `string_belong_to_language()` simulates the automaton by reading the input string symbol by symbol and following valid transitions. The string is accepted only if the final state reached is an accepting state.

```python
class FiniteAutomaton:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = final_states

    def string_belong_to_language(self, input_string):
        current_state = self.start_state

        for symbol in input_string:
            if (current_state, symbol) not in self.transitions:
                return False
            current_state = self.transitions[(current_state, symbol)]

        return current_state in self.final_states
```
---

### Main Program Class

The main.py file represents the entry point of the application.
It creates an instance of the Grammar class, generates sample strings, converts the grammar into a finite automaton, and verifies whether certain strings belong to the language.
The program demonstrates the interaction between the grammar and its equivalent finite automaton.

```python
from grammar import Grammar
from finite_automaton import FiniteAutomaton


def main():
    # Create grammar instance
    grammar = Grammar()

    # Generate example string
    generated_string = grammar.generate_string()
    print("Generated string:", generated_string)

    # Convert grammar to finite automaton
    automaton = grammar.to_finite_automaton()

    # Test strings
    test_strings = ["ab", "acd", "ba", "abc"]

    for string in test_strings:
        result = automaton.string_belong_to_language(string)
        print(f"String '{string}' accepted:", result)


if __name__ == "__main__":
    main()
```
### Conclusions
Overall, this project strengthened both conceptual understanding and programming skills. It clarified how abstract mathematical definitions can be translated into working code and showed how formal language theory forms the foundation for many areas in computer science, including compilers, lexical analysis, and pattern recognition.




