"""
Laboratory Work 5 – Chomsky Normal Form
Course: Formal Languages & Finite Automata
Author: Mutu Adrian
Variant 16

Grammar G = (VN, VT, P, S)
  VN = {S, A, B, C, D}
  VT = {a, b}
  P:
    1.  S → abAB
    2.  A → aSab
    3.  A → BS
    4.  A → aA
    5.  A → b
    6.  B → BA
    7.  B → ababB
    8.  B → b
    9.  B → ε
    10. C → AS
"""

from itertools import combinations
from copy import deepcopy


class Grammar:
    """
    Context-free grammar representation with step-by-step CNF conversion.
    Accepts any grammar — not just Variant 16 (bonus requirement).
    """

    def __init__(self, VN, VT, productions, start):
        self.VN = set(VN)
        self.VT = set(VT)
        # productions: dict  NT -> list of lists (each list is one RHS)
        # empty list [] represents ε
        self.P = {nt: [list(rhs) for rhs in prods]
                  for nt, prods in productions.items()}
        self.S = start
        self._counter = 0

    # ── helpers ──────────────────────────────────────────────────────────────

    def _fresh(self, hint='X'):
        """Return a new non-terminal name not yet in VN."""
        self._counter += 1
        name = f"{hint}{self._counter}"
        while name in self.VN or name in self.VT:
            self._counter += 1
            name = f"{hint}{self._counter}"
        return name

    def _dedup(self, lst):
        seen = []
        for x in lst:
            if x not in seen:
                seen.append(x)
        return seen

    def show(self, title=""):
        sep = "─" * 58
        if title:
            print(f"\n{'═'*58}")
            print(f"  {title}")
            print(f"{'═'*58}")
        print(f"  VN = {{ {', '.join(sorted(self.VN))} }}")
        print(f"  VT = {{ {', '.join(sorted(self.VT))} }}")
        print(f"  S  = {self.S}")
        print(f"  {sep}")
        print("  Productions:")
        for nt in sorted(self.P.keys()):
            for rhs in self.P[nt]:
                arrow = "ε" if rhs == [] else "".join(rhs)
                print(f"    {nt} → {arrow}")

    # ── Step 1: Eliminate ε-productions ──────────────────────────────────────

    def step1_eliminate_epsilon(self):
        print("\n" + "─"*58)
        print("  STEP 1 – Eliminate ε-productions")
        print("─"*58)

        # Compute nullable set
        nullable = set()
        changed = True
        while changed:
            changed = False
            for nt, prods in self.P.items():
                if nt in nullable:
                    continue
                for rhs in prods:
                    if rhs == [] or all(s in nullable for s in rhs):
                        nullable.add(nt)
                        changed = True
                        break
        print(f"  Nullable symbols: {nullable if nullable else '∅'}")

        new_P = {nt: [] for nt in self.P}
        for nt, prods in self.P.items():
            for rhs in prods:
                if rhs == []:          # drop ε directly
                    continue
                nullable_pos = [i for i, s in enumerate(rhs) if s in nullable]
                # generate all subsets of nullable positions to omit
                for r in range(len(nullable_pos) + 1):
                    for omit in combinations(nullable_pos, r):
                        new_rhs = [s for i, s in enumerate(rhs) if i not in omit]
                        if new_rhs:    # don't re-add ε
                            new_P[nt].append(new_rhs)
            new_P[nt] = self._dedup(new_P[nt])
        self.P = new_P
        print("  ε-productions removed.\n")

    # ── Step 2: Eliminate unit productions ───────────────────────────────────

    def step2_eliminate_unit(self):
        print("─"*58)
        print("  STEP 2 – Eliminate unit productions (renaming)")
        print("─"*58)

        changed = True
        while changed:
            changed = False
            for nt in list(self.P.keys()):
                for rhs in list(self.P[nt]):
                    if len(rhs) == 1 and rhs[0] in self.VN:
                        target = rhs[0]
                        self.P[nt].remove(rhs)
                        print(f"  Resolved {nt} → {target}: "
                              f"adding {target}'s productions to {nt}")
                        for tr in self.P.get(target, []):
                            if tr not in self.P[nt]:
                                self.P[nt].append(tr)
                        changed = True
                        break   # restart because list changed

        print("  Unit productions removed.\n")

    # ── Step 3: Eliminate inaccessible symbols ────────────────────────────────

    def step3_eliminate_inaccessible(self):
        print("─"*58)
        print("  STEP 3 – Eliminate inaccessible symbols")
        print("─"*58)

        reachable = {self.S}
        changed = True
        while changed:
            changed = False
            for nt in list(reachable):
                for rhs in self.P.get(nt, []):
                    for sym in rhs:
                        if sym in self.VN and sym not in reachable:
                            reachable.add(sym)
                            changed = True

        inaccessible = self.VN - reachable
        print(f"  Reachable    : {sorted(reachable)}")
        print(f"  Inaccessible : {sorted(inaccessible)} → removed")
        self.VN = reachable
        for sym in inaccessible:
            self.P.pop(sym, None)
        print("  Inaccessible symbols removed.\n")

    # ── Step 4: Eliminate non-productive symbols ──────────────────────────────

    def step4_eliminate_nonproductive(self):
        print("─"*58)
        print("  STEP 4 – Eliminate non-productive symbols")
        print("─"*58)

        productive = set(self.VT)
        changed = True
        while changed:
            changed = False
            for nt, prods in self.P.items():
                if nt in productive:
                    continue
                for rhs in prods:
                    if all(s in productive for s in rhs):
                        productive.add(nt)
                        changed = True
                        break

        nonproductive = self.VN - productive
        print(f"  Productive      : {sorted(productive & self.VN)}")
        print(f"  Non-productive  : {sorted(nonproductive)} → removed")
        self.VN -= nonproductive
        for nt in nonproductive:
            self.P.pop(nt, None)
        # also drop any production that references a non-productive symbol
        for nt in list(self.P.keys()):
            self.P[nt] = [
                rhs for rhs in self.P[nt]
                if all(s in productive for s in rhs)
            ]
        print("  Non-productive symbols removed.\n")

    # ── Step 5: Convert to Chomsky Normal Form ────────────────────────────────

    def step5_to_cnf(self):
        print("─"*58)
        print("  STEP 5 – Convert to Chomsky Normal Form")
        print("─"*58)

        # 5a. Introduce terminal nonterminals for terminals inside long rules
        terminal_nt = {}   # terminal char -> NT

        def get_Tt(t):
            if t not in terminal_nt:
                nt = self._fresh(f'T{t}')
                terminal_nt[t] = nt
                self.VN.add(nt)
                self.P[nt] = [[t]]
                print(f"  New terminal NT: {nt} → {t}")
            return terminal_nt[t]

        for nt in list(self.P.keys()):
            new_prods = []
            for rhs in self.P[nt]:
                if len(rhs) >= 2:
                    new_rhs = [get_Tt(s) if s in self.VT else s for s in rhs]
                    new_prods.append(new_rhs)
                else:
                    new_prods.append(rhs)
            self.P[nt] = new_prods

        # 5b. Binarize productions with > 2 symbols
        # Cache: tuple of symbols -> NT that produces them
        pair_cache = {}

        def get_pair_nt(pair):
            key = tuple(pair)
            if key in pair_cache:
                return pair_cache[key]
            # check existing rules first (avoid duplicates)
            for xnt, prods in self.P.items():
                if prods == [list(pair)]:
                    pair_cache[key] = xnt
                    return xnt
            # create a new one
            new_nt = self._fresh('Y')
            self.VN.add(new_nt)
            self.P[new_nt] = [list(pair)]
            pair_cache[key] = new_nt
            print(f"  New binary NT : {new_nt} → {''.join(pair)}")
            return new_nt

        for nt in list(self.P.keys()):
            new_prods = []
            for rhs in self.P[nt]:
                # fold right: replace last two with a new NT, repeat
                while len(rhs) > 2:
                    right_pair = rhs[-2:]
                    helper = get_pair_nt(right_pair)
                    rhs = rhs[:-2] + [helper]
                new_prods.append(rhs)
            self.P[nt] = self._dedup(new_prods)

        print("\n  Grammar is now in Chomsky Normal Form.")

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def to_cnf(self, verbose=True):
        if verbose:
            self.show("Original Grammar")
        self.step1_eliminate_epsilon()
        if verbose:
            self.show("After Step 1 – ε-elimination")
        self.step2_eliminate_unit()
        if verbose:
            self.show("After Step 2 – unit-production elimination")
        self.step3_eliminate_inaccessible()
        if verbose:
            self.show("After Step 3 – inaccessible-symbol elimination")
        self.step4_eliminate_nonproductive()
        if verbose:
            self.show("After Step 4 – non-productive-symbol elimination")
        self.step5_to_cnf()
        if verbose:
            self.show("Final CNF Grammar")
        return self


# ── Variant 16 ────────────────────────────────────────────────────────────────

VARIANT_16 = {
    'VN': ['S', 'A', 'B', 'C', 'D'],
    'VT': ['a', 'b'],
    'S' : 'S',
    'P' : {
        'S': [['a','b','A','B']],
        'A': [['a','S','a','b'], ['B','S'], ['a','A'], ['b']],
        'B': [['B','A'], ['a','b','a','b','B'], ['b'], []],
        'C': [['A','S']],
        'D': [],          # D has no productions at all
    }
}


if __name__ == '__main__':
    g = Grammar(
        VN=VARIANT_16['VN'],
        VT=VARIANT_16['VT'],
        productions=VARIANT_16['P'],
        start=VARIANT_16['S'],
    )
    g.to_cnf(verbose=True)