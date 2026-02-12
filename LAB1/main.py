from grammar import Grammar

grammar = Grammar()

print("Generated strings:")
for _ in range(5):
    print(grammar.generate_string())

fa = grammar.to_finite_automaton()

test_strings = [
    "db",
    "bdab",
    "bbdaaaab",
    "bbdaaadca",
    "d",
    "ba",
    "bbdc"
]

print("\nAutomaton checks:")
for s in test_strings:
    print(f"{s} -> {fa.string_belong_to_language(s)}")
