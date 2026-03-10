class Grammar:
    """
    Represents a formal grammar with productions and classifies it
    according to the Chomsky hierarchy (Type 0–3).
    """

    def __init__(self, non_terminals, terminals, productions, start_symbol):
        """
        :param non_terminals: set of non-terminal symbols, e.g. {'S', 'A', 'B'}
        :param terminals:     set of terminal symbols,     e.g. {'a', 'b'}
        :param productions:   dict  NT -> list[str],       e.g. {'S': ['aA', 'b'], 'A': ['bS']}
        :param start_symbol:  str,                         e.g. 'S'
        """
        self.non_terminals = set(non_terminals)
        self.terminals = set(terminals)
        self.productions = productions          # { lhs_str : [rhs_str, ...] }
        self.start_symbol = start_symbol

    # ------------------------------------------------------------------
    # Chomsky Hierarchy Classification
    # ------------------------------------------------------------------

    def classify_chomsky(self) -> str:
        """
        Returns the most restrictive Chomsky type that describes this grammar.

        Type 3  – Regular grammar
        Type 2  – Context-free grammar
        Type 1  – Context-sensitive grammar
        Type 0  – Recursively enumerable (unrestricted)
        """
        if self._is_regular():
            return "Type 3 – Regular Grammar"
        if self._is_context_free():
            return "Type 2 – Context-Free Grammar"
        if self._is_context_sensitive():
            return "Type 1 – Context-Sensitive Grammar"
        return "Type 0 – Unrestricted Grammar (Recursively Enumerable)"

    # ---------- helper predicates ----------

    def _is_regular(self) -> bool:
        """
        Right-linear: every production is  A → aB  or  A → a  or  A → ε
        (we also accept left-linear, but a single grammar must be consistent).
        """
        right_linear = True
        left_linear  = True

        for lhs, rhs_list in self.productions.items():
            # LHS must be a single non-terminal (possibly multi-char, e.g. "q0")
            if lhs not in self.non_terminals:
                return False

            for rhs in rhs_list:
                if rhs == 'ε' or rhs == '':
                    continue  # epsilon is fine

                if not self._matches_right_linear(rhs):
                    right_linear = False
                if not self._matches_left_linear(rhs):
                    left_linear = False

        return right_linear or left_linear

    def _matches_right_linear(self, rhs: str) -> bool:
        """A → w  or  A → wB  where w ∈ Σ* and B ∈ N.
        Works with multi-character non-terminal/terminal symbols.
        """
        # Try stripping a trailing non-terminal (longest match first)
        tail = rhs
        for nt in sorted(self.non_terminals, key=len, reverse=True):
            if rhs.endswith(nt):
                tail = rhs[: len(rhs) - len(nt)]
                break
        # The rest must consist only of terminals (each terminal may be multi-char)
        return self._is_all_terminals(tail)

    def _matches_left_linear(self, rhs: str) -> bool:
        """A → w  or  A → Bw  where w ∈ Σ* and B ∈ N."""
        head = rhs
        for nt in sorted(self.non_terminals, key=len, reverse=True):
            if rhs.startswith(nt):
                head = rhs[len(nt):]
                break
        return self._is_all_terminals(head)

    def _is_all_terminals(self, s: str) -> bool:
        """Return True iff s can be fully decomposed into terminal symbols."""
        if s == '':
            return True
        # Greedy longest-match scan
        i = 0
        while i < len(s):
            matched = False
            for t in sorted(self.terminals, key=len, reverse=True):
                if s[i:].startswith(t):
                    i += len(t)
                    matched = True
                    break
            if not matched:
                return False
        return True

    def _is_context_free(self) -> bool:
        """LHS is exactly one non-terminal; RHS is any non-empty string."""
        for lhs, rhs_list in self.productions.items():
            if lhs not in self.non_terminals:
                return False
            for rhs in rhs_list:
                if rhs == '' or rhs is None:
                    return False
        return True

    def _is_context_sensitive(self) -> bool:
        """
        |LHS| <= |RHS| for all productions except possibly S → ε
        when S doesn't appear in any RHS.
        """
        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                if rhs == 'ε' or rhs == '':
                    # Only allowed if lhs is start and start not in any RHS
                    if lhs != self.start_symbol:
                        return False
                    if self._start_appears_in_rhs():
                        return False
                elif len(lhs) > len(rhs):
                    return False
        return True

    def _start_appears_in_rhs(self) -> bool:
        for rhs_list in self.productions.values():
            for rhs in rhs_list:
                if self.start_symbol in rhs:
                    return True
        return False


    def display(self):
        print("=== Grammar ===")
        print(f"  Non-terminals : {self.non_terminals}")
        print(f"  Terminals     : {self.terminals}")
        print(f"  Start symbol  : {self.start_symbol}")
        print("  Productions:")
        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                print(f"    {lhs} → {rhs}")
        print(f"  Chomsky class : {self.classify_chomsky()}")