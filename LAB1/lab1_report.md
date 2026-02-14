# The title of the work

**Course:** Formal Languages & Finite Automata  
**Author:** Adrian Mutu  

---

## Theory

A formal language is a set of strings formed from a finite alphabet according to specific production rules.  
In this laboratory work, a regular grammar was implemented and converted into a finite automaton.

---

## Objectives

- Understand what a formal grammar is.
- Implement a grammar in Python.
- Generate valid strings from the grammar.
- Convert the grammar into a finite automaton.
- Check whether a string belongs to the language.

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
        self.start_symbol = "S"
        
        
