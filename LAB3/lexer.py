"""
Laboratory Work 3 - Lexer / Scanner
Course: Formal Languages & Finite Automata
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


# ─────────────────────────────────────────────
# 1. Token Types
# ─────────────────────────────────────────────
class TokenType(Enum):
    # Literals
    INTEGER     = auto()
    FLOAT       = auto()
    STRING      = auto()

    # Identifiers & keywords
    IDENTIFIER  = auto()
    KEYWORD     = auto()   # sin, cos, tan, let, if, else, while, return, true, false

    # Arithmetic operators
    PLUS        = auto()
    MINUS       = auto()
    MULTIPLY    = auto()
    DIVIDE      = auto()
    MODULO      = auto()
    POWER       = auto()

    # Assignment & comparison
    ASSIGN      = auto()   # =
    EQ          = auto()   # ==
    NEQ         = auto()   # !=
    LT          = auto()   # <
    GT          = auto()   # >
    LEQ         = auto()   # <=
    GEQ         = auto()   # >=

    # Logical
    AND         = auto()   # &&
    OR          = auto()   # ||
    NOT         = auto()   # !

    # Delimiters
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    COMMA       = auto()   # ,
    SEMICOLON   = auto()   # ;

    # Special
    NEWLINE     = auto()
    EOF         = auto()
    UNKNOWN     = auto()


KEYWORDS = {
    "sin", "cos", "tan", "asin", "acos", "atan",
    "let", "if", "else", "while", "return",
    "true", "false", "and", "or", "not"
}


# ─────────────────────────────────────────────
# 2. Token data-class
# ─────────────────────────────────────────────
@dataclass
class Token:
    type:   TokenType
    value:  str
    line:   int
    column: int

    def __repr__(self):
        return f"Token({self.type.name:<12} | {repr(self.value):<14} | line {self.line}, col {self.column})"


# ─────────────────────────────────────────────
# 3. Lexer
# ─────────────────────────────────────────────
class Lexer:
    """
    A single-pass, character-level lexer for a simple scripting language
    that supports arithmetic, trigonometric functions, variables, control
    flow keywords, and string literals.
    """

    def __init__(self, source: str):
        self.source  = source
        self.pos     = 0           # current index in source
        self.line    = 1
        self.column  = 1
        self.tokens: List[Token] = []

    # ── helpers ──────────────────────────────

    @property
    def current(self) -> Optional[str]:
        return self.source[self.pos] if self.pos < len(self.source) else None

    @property
    def peek(self) -> Optional[str]:
        nxt = self.pos + 1
        return self.source[nxt] if nxt < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos    += 1
        if ch == '\n':
            self.line  += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def make_token(self, ttype: TokenType, value: str, line: int, col: int) -> Token:
        return Token(ttype, value, line, col)

    # ── scanning helpers ─────────────────────

    def skip_whitespace_and_comments(self):
        while self.current is not None:
            ch = self.current
            if ch in (' ', '\t', '\r'):
                self.advance()
            elif ch == '/' and self.peek == '/':        # line comment
                while self.current not in (None, '\n'):
                    self.advance()
            elif ch == '/' and self.peek == '*':        # block comment
                self.advance(); self.advance()           # consume /*
                while self.current is not None:
                    if self.current == '*' and self.peek == '/':
                        self.advance(); self.advance()   # consume */
                        break
                    self.advance()
            else:
                break

    def read_number(self) -> Token:
        start_col = self.column
        start_line = self.line
        buf = ""
        is_float = False

        while self.current is not None and (self.current.isdigit() or self.current == '.'):
            if self.current == '.':
                if is_float:          # second dot → stop
                    break
                is_float = True
            buf += self.advance()

        # Optional exponent: 1.5e10 / 2E-3
        if self.current in ('e', 'E'):
            is_float = True
            buf += self.advance()
            if self.current in ('+', '-'):
                buf += self.advance()
            while self.current is not None and self.current.isdigit():
                buf += self.advance()

        ttype = TokenType.FLOAT if is_float else TokenType.INTEGER
        return self.make_token(ttype, buf, start_line, start_col)

    def read_identifier_or_keyword(self) -> Token:
        start_col  = self.column
        start_line = self.line
        buf = ""
        while self.current is not None and (self.current.isalnum() or self.current == '_'):
            buf += self.advance()
        ttype = TokenType.KEYWORD if buf in KEYWORDS else TokenType.IDENTIFIER
        return self.make_token(ttype, buf, start_line, start_col)

    def read_string(self) -> Token:
        start_col  = self.column
        start_line = self.line
        quote = self.advance()          # opening " or '
        buf = ""
        while self.current is not None and self.current != quote:
            if self.current == '\\':    # escape sequence
                self.advance()
                esc = self.advance()
                buf += {'n': '\n', 't': '\t', '\\': '\\'}.get(esc, esc)
            else:
                buf += self.advance()
        if self.current == quote:
            self.advance()              # closing quote
        return self.make_token(TokenType.STRING, buf, start_line, start_col)

    # ── main tokenise method ─────────────────

    def tokenize(self) -> List[Token]:
        while True:
            self.skip_whitespace_and_comments()
            if self.current is None:
                self.tokens.append(self.make_token(TokenType.EOF, "", self.line, self.column))
                break

            ln, col = self.line, self.column
            ch = self.current

            # Numbers
            if ch.isdigit() or (ch == '.' and self.peek and self.peek.isdigit()):
                self.tokens.append(self.read_number())

            # Identifiers / keywords
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier_or_keyword())

            # Strings
            elif ch in ('"', "'"):
                self.tokens.append(self.read_string())

            # Newlines (kept as tokens so callers can track statement endings)
            elif ch == '\n':
                self.advance()
                self.tokens.append(self.make_token(TokenType.NEWLINE, "\\n", ln, col))

            # Two-char operators first
            elif ch == '=' and self.peek == '=':
                self.advance(); self.advance()
                self.tokens.append(self.make_token(TokenType.EQ, "==", ln, col))
            elif ch == '!' and self.peek == '=':
                self.advance(); self.advance()
                self.tokens.append(self.make_token(TokenType.NEQ, "!=", ln, col))
            elif ch == '<' and self.peek == '=':
                self.advance(); self.advance()
                self.tokens.append(self.make_token(TokenType.LEQ, "<=", ln, col))
            elif ch == '>' and self.peek == '=':
                self.advance(); self.advance()
                self.tokens.append(self.make_token(TokenType.GEQ, ">=", ln, col))
            elif ch == '&' and self.peek == '&':
                self.advance(); self.advance()
                self.tokens.append(self.make_token(TokenType.AND, "&&", ln, col))
            elif ch == '|' and self.peek == '|':
                self.advance(); self.advance()
                self.tokens.append(self.make_token(TokenType.OR, "||", ln, col))

            # Single-char tokens
            else:
                SINGLE = {
                    '+': TokenType.PLUS,    '-': TokenType.MINUS,
                    '*': TokenType.MULTIPLY,'/' : TokenType.DIVIDE,
                    '%': TokenType.MODULO,  '^': TokenType.POWER,
                    '=': TokenType.ASSIGN,  '<': TokenType.LT,
                    '>': TokenType.GT,      '!': TokenType.NOT,
                    '(': TokenType.LPAREN,  ')': TokenType.RPAREN,
                    '{': TokenType.LBRACE,  '}': TokenType.RBRACE,
                    ',': TokenType.COMMA,   ';': TokenType.SEMICOLON,
                }
                ttype = SINGLE.get(ch, TokenType.UNKNOWN)
                self.advance()
                self.tokens.append(self.make_token(ttype, ch, ln, col))

        return self.tokens


# ─────────────────────────────────────────────
# 4. Demo / Test
# ─────────────────────────────────────────────
SAMPLE_PROGRAMS = {
    "arithmetic": "3 + 4.5 * (2 - 1) / 0.5",

    "trig_expression":
        "let angle = 1.5708;\n"
        "let result = sin(angle) + cos(0.0) * tan(angle / 2);",

    "control_flow":
        "// check if number is in range\n"
        "let x = 42;\n"
        "if (x >= 0 && x <= 100) {\n"
        "    return true;\n"
        "} else {\n"
        "    return false;\n"
        "}",

    "string_and_float":
        'let greeting = "Hello, World!";\n'
        "let pi = 3.14159e0;\n"
        "let tau = pi * 2;",

    "complex_trig":
        "// Pythagorean identity: sin^2 + cos^2 == 1\n"
        "let a = sin(0.7854);\n"
        "let b = cos(0.7854);\n"
        "let identity = a^2 + b^2;\n"
        "if (identity != 1.0) { return false; }",
}

if __name__ == "__main__":
    for name, source in SAMPLE_PROGRAMS.items():
        print(f"\n{'='*60}")
        print(f"  Sample: {name}")
        print(f"{'='*60}")
        print(f"  Source:\n  {source.strip()}\n")
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
        for tok in tokens:
            if tok.type != TokenType.NEWLINE:
                print(f"  {tok}")