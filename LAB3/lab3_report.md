# Lab 3 – Lexer / Scanner

**Course:** Formal Languages & Finite Automata

**Author:** Mutu Adrian

---

## Theory

The term **lexer** comes from *lexical analysis* — the process of transforming a raw character stream into a sequence of structured units called **tokens**. Alternative names for the same mechanism are *tokeniser* and *scanner*. Lexical analysis is the very first stage of a compiler or interpreter: it sits between the source text and the parser.

A **lexeme** is the raw substring extracted from the source (e.g. the characters `3.14`). A **token** is the categorised, typed representation of that lexeme (e.g. `FLOAT("3.14")`). The distinction matters: the parser consumes tokens — abstract types with optional metadata — not raw characters.

Token categories found in most languages include:

1)**Literals** — integers, floats, strings, booleans.

2)**Identifiers** — user-defined names (variables, functions).

3)**Keywords** — reserved words with special meaning (`if`, `while`, `return`, `sin`, …).

4)**Operators** — arithmetic, relational, logical, assignment.

5)**Delimiters** — parentheses, braces, commas, semicolons.

6)**Comments / whitespace** — typically discarded before a token is emitted.

A lexer operates with a single left-to-right pass, applying the **maximal-munch** principle: always consume the longest possible match before emitting a token. One character of look-ahead is sufficient to disambiguate most multi-character operators (`==` vs `=`, `!=` vs `!`, `<=` vs `<`, etc.).

---

## Objectives

1. Understand what lexical analysis is and where it fits in a compiler pipeline.
2. Get familiar with the inner workings of a lexer / scanner / tokeniser.
3. Implement a sample lexer for a simple scripting language that supports:
   a)Integer and floating-point literals (including scientific notation).
   b)String literals with escape sequences.
   c)Trigonometric keywords (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`).
   d)Control-flow keywords (`let`, `if`, `else`, `while`, `return`, `true`, `false`).
   e)Arithmetic, relational, logical, and assignment operators.
   f)Single-line (`//`) and block (`/* … */`) comments.
4. Demonstrate the lexer on five representative input programs.

---

## Implementation Description

### Token Types (`lexer.py`)

All 30+ token categories are defined as members of a Python `Enum`. This makes the code self-documenting and eliminates magic-string bugs.

```python
class TokenType(Enum):
    # Literals
    INTEGER, FLOAT, STRING = auto(), auto(), auto()
    # Identifiers & keywords
    IDENTIFIER, KEYWORD = auto(), auto()
    # Arithmetic operators
    PLUS, MINUS, MULTIPLY, DIVIDE, MODULO, POWER = auto(), auto(), auto(), auto(), auto(), auto()
    # Relational / assignment
    ASSIGN, EQ, NEQ, LT, GT, LEQ, GEQ = auto(), auto(), auto(), auto(), auto(), auto(), auto()
    # Logical
    AND, OR, NOT = auto(), auto(), auto()
    # Delimiters
    LPAREN, RPAREN, LBRACE, RBRACE, COMMA, SEMICOLON = auto(), auto(), auto(), auto(), auto(), auto()
    # Special
    NEWLINE, EOF, UNKNOWN = auto(), auto(), auto()
```

The reserved keyword set covers trigonometric identifiers and common control-flow words:

```python
KEYWORDS = {
    "sin", "cos", "tan", "asin", "acos", "atan",
    "let", "if", "else", "while", "return",
    "true", "false", "and", "or", "not"
}
```

---

### Token Dataclass

Each token stores its type, raw value, and source position (line + column) to support meaningful error messages in downstream phases:

```python
@dataclass
class Token:
    type:   TokenType
    value:  str
    line:   int
    column: int
```

---

### Lexer Class

The `Lexer` class owns the source string and a cursor position. Two properties give clean read-only access to the current and look-ahead characters without index arithmetic scattered across the class:

```python
@property
def current(self) -> Optional[str]:
    return self.source[self.pos] if self.pos < len(self.source) else None

@property
def peek(self) -> Optional[str]:
    nxt = self.pos + 1
    return self.source[nxt] if nxt < len(self.source) else None
```

#### Whitespace and Comment Skipping

Before reading every token the lexer discards spaces, tabs, carriage returns, `//` line comments, and `/* … */` block comments in a single helper, keeping the main loop clean:

```python
def skip_whitespace_and_comments(self):
    while self.current is not None:
        ch = self.current
        if ch in (' ', '\t', '\r'):
            self.advance()
        elif ch == '/' and self.peek == '/':      # line comment
            while self.current not in (None, '\n'):
                self.advance()
        elif ch == '/' and self.peek == '*':      # block comment
            self.advance(); self.advance()         # consume /*
            while self.current is not None:
                if self.current == '*' and self.peek == '/':
                    self.advance(); self.advance() # consume */
                    break
                self.advance()
        else:
            break
```

#### Number Recognition

The number reader follows the maximal-munch rule, greedily consuming digit and dot characters, then an optional exponent suffix (`e`/`E`). The presence of a dot or exponent determines whether the token type is `INTEGER` or `FLOAT`:

```python
def read_number(self) -> Token:
    buf = ''
    is_float = False
    while self.current and (self.current.isdigit() or self.current == '.'):
        if self.current == '.':
            if is_float: break   # second dot – stop
            is_float = True
        buf += self.advance()
    # optional exponent  1.5e10 / 2E-3
    if self.current in ('e', 'E'):
        is_float = True
        buf += self.advance()
        if self.current in ('+', '-'):
            buf += self.advance()
        while self.current and self.current.isdigit():
            buf += self.advance()
    ttype = TokenType.FLOAT if is_float else TokenType.INTEGER
    return self.make_token(ttype, buf, ...)
```

#### Identifier and Keyword Recognition

Identifiers start with a letter or underscore. After reading the full word, the value is checked against `KEYWORDS`; if it matches, the type is `KEYWORD`, otherwise `IDENTIFIER`:

```python
def read_identifier_or_keyword(self) -> Token:
    buf = ''
    while self.current and (self.current.isalnum() or self.current == '_'):
        buf += self.advance()
    ttype = TokenType.KEYWORD if buf in KEYWORDS else TokenType.IDENTIFIER
    return self.make_token(ttype, buf, ...)
```

#### String Literal Recognition

String literals may be enclosed in single or double quotes. Basic escape sequences (`\n`, `\t`, `\\`) are handled:

```python
def read_string(self) -> Token:
    quote = self.advance()     # opening ' or "
    buf = ''
    while self.current and self.current != quote:
        if self.current == '\\':
            self.advance()
            esc = self.advance()
            buf += {'n': '\n', 't': '\t', '\\': '\\'}.get(esc, esc)
        else:
            buf += self.advance()
    if self.current == quote:
        self.advance()         # closing quote
    return self.make_token(TokenType.STRING, buf, ...)
```

#### Multi-character Operator Dispatch

The main `tokenize()` loop first checks for two-character operators using `peek`, then falls through to a single-character dispatch dictionary:

```python
# Two-character operators checked first
elif ch == '=' and self.peek == '=': ...  # EQ   ==
elif ch == '!' and self.peek == '=': ...  # NEQ  !=
elif ch == '<' and self.peek == '=': ...  # LEQ  <=
elif ch == '>' and self.peek == '=': ...  # GEQ  >=
elif ch == '&' and self.peek == '&': ...  # AND  &&
elif ch == '|' and self.peek == '|': ...  # OR   ||

# Single-character dispatch table
SINGLE = {
    '+': PLUS,  '-': MINUS,  '*': MULTIPLY, '/': DIVIDE,
    '%': MODULO, '^': POWER, '=': ASSIGN,  '<': LT,
    '>': GT,    '!': NOT,   '(': LPAREN,  ')': RPAREN,
    '{': LBRACE,'}': RBRACE,',': COMMA,   ';': SEMICOLON,
}
```

---

## Results

Five representative programs were fed to the lexer. Newline tokens are omitted for brevity.

### Sample 1 – Arithmetic Expression

**Input:**
```
3 + 4.5 * (2 - 1) / 0.5
```

**Output:**
```
Token(INTEGER      | '3'    | line 1, col 1)
Token(PLUS         | '+'    | line 1, col 3)
Token(FLOAT        | '4.5'  | line 1, col 5)
Token(MULTIPLY     | '*'    | line 1, col 9)
Token(LPAREN       | '('    | line 1, col 11)
Token(INTEGER      | '2'    | line 1, col 12)
Token(MINUS        | '-'    | line 1, col 14)
Token(INTEGER      | '1'    | line 1, col 16)
Token(RPAREN       | ')'    | line 1, col 17)
Token(DIVIDE       | '/'    | line 1, col 19)
Token(FLOAT        | '0.5'  | line 1, col 21)
Token(EOF          | ''     | line 1, col 24)
```

---

### Sample 2 – Trigonometric Expression

**Input:**
```
let angle = 1.5708;
let result = sin(angle) + cos(0.0) * tan(angle / 2);
```

**Output:**
```
Token(KEYWORD      | 'let'    | line 1, col 1)
Token(IDENTIFIER   | 'angle'  | line 1, col 5)
Token(ASSIGN       | '='      | line 1, col 11)
Token(FLOAT        | '1.5708' | line 1, col 13)
Token(SEMICOLON    | ';'      | line 1, col 19)
Token(KEYWORD      | 'let'    | line 2, col 1)
Token(IDENTIFIER   | 'result' | line 2, col 5)
Token(ASSIGN       | '='      | line 2, col 12)
Token(KEYWORD      | 'sin'    | line 2, col 14)
Token(LPAREN       | '('      | line 2, col 17)
Token(IDENTIFIER   | 'angle'  | line 2, col 18)
Token(RPAREN       | ')'      | line 2, col 23)
Token(PLUS         | '+'      | line 2, col 25)
Token(KEYWORD      | 'cos'    | line 2, col 27)
Token(LPAREN       | '('      | line 2, col 30)
Token(FLOAT        | '0.0'    | line 2, col 31)
Token(RPAREN       | ')'      | line 2, col 34)
Token(MULTIPLY     | '*'      | line 2, col 36)
Token(KEYWORD      | 'tan'    | line 2, col 38)
Token(LPAREN       | '('      | line 2, col 41)
Token(IDENTIFIER   | 'angle'  | line 2, col 42)
Token(DIVIDE       | '/'      | line 2, col 48)
Token(INTEGER      | '2'      | line 2, col 50)
Token(RPAREN       | ')'      | line 2, col 51)
Token(SEMICOLON    | ';'      | line 2, col 52)
Token(EOF          | ''       | line 2, col 53)
```

`sin`, `cos`, and `tan` are correctly classified as `KEYWORD` tokens (not `IDENTIFIER`), because they exist in the reserved-words set.

---

### Sample 3 – Control Flow with Logical Operators

**Input:**
```
// check if number is in range
let x = 42;
if (x >= 0 && x <= 100) {
    return true;
} else {
    return false;
}
```

**Output:**
```
Token(KEYWORD      | 'let'    | line 2, col 1)
Token(IDENTIFIER   | 'x'      | line 2, col 5)
Token(ASSIGN       | '='      | line 2, col 7)
Token(INTEGER      | '42'     | line 2, col 9)
Token(SEMICOLON    | ';'      | line 2, col 11)
Token(KEYWORD      | 'if'     | line 3, col 1)
Token(LPAREN       | '('      | line 3, col 4)
Token(IDENTIFIER   | 'x'      | line 3, col 5)
Token(GEQ          | '>='     | line 3, col 7)
Token(INTEGER      | '0'      | line 3, col 10)
Token(AND          | '&&'     | line 3, col 12)
Token(IDENTIFIER   | 'x'      | line 3, col 15)
Token(LEQ          | '<='     | line 3, col 17)
Token(INTEGER      | '100'    | line 3, col 20)
Token(RPAREN       | ')'      | line 3, col 23)
Token(LBRACE       | '{'      | line 3, col 25)
Token(KEYWORD      | 'return' | line 4, col 5)
Token(KEYWORD      | 'true'   | line 4, col 12)
Token(SEMICOLON    | ';'      | line 4, col 16)
Token(RBRACE       | '}'      | line 5, col 1)
Token(KEYWORD      | 'else'   | line 5, col 3)
Token(LBRACE       | '{'      | line 5, col 8)
Token(KEYWORD      | 'return' | line 6, col 5)
Token(KEYWORD      | 'false'  | line 6, col 12)
Token(SEMICOLON    | ';'      | line 6, col 17)
Token(RBRACE       | '}'      | line 7, col 1)
Token(EOF          | ''       | line 7, col 2)
```

The `//` comment on line 1 was entirely stripped. Two-character tokens `>=`, `&&`, and `<=` are emitted as single `GEQ`, `AND`, `LEQ` tokens, proving that the peek-ahead mechanism works correctly.

---

### Sample 4 – String Literal and Float with Exponent

**Input:**
```
let greeting = "Hello, World!";
let pi = 3.14159e0;
let tau = pi * 2;
```

**Output:**
```
Token(KEYWORD      | 'let'           | line 1, col 1)
Token(IDENTIFIER   | 'greeting'      | line 1, col 5)
Token(ASSIGN       | '='             | line 1, col 14)
Token(STRING       | 'Hello, World!' | line 1, col 16)
Token(SEMICOLON    | ';'             | line 1, col 31)
Token(KEYWORD      | 'let'           | line 2, col 1)
Token(IDENTIFIER   | 'pi'            | line 2, col 5)
Token(ASSIGN       | '='             | line 2, col 8)
Token(FLOAT        | '3.14159e0'     | line 2, col 10)
Token(SEMICOLON    | ';'             | line 2, col 19)
Token(KEYWORD      | 'let'           | line 3, col 1)
Token(IDENTIFIER   | 'tau'           | line 3, col 5)
Token(ASSIGN       | '='             | line 3, col 9)
Token(IDENTIFIER   | 'pi'            | line 3, col 11)
Token(MULTIPLY     | '*'             | line 3, col 14)
Token(INTEGER      | '2'             | line 3, col 16)
Token(EOF          | ''              | line 3, col 18)
```

The string value stored in the token excludes the surrounding quote characters. The exponent notation `3.14159e0` is correctly classified as `FLOAT`, not `INTEGER`.

---

### Sample 5 – Pythagorean Identity with Power Operator

**Input:**
```
// Pythagorean identity: sin^2 + cos^2 == 1
let a = sin(0.7854);
let b = cos(0.7854);
let identity = a^2 + b^2;
if (identity != 1.0) { return false; }
```

**Output:**
```
Token(KEYWORD      | 'let'      | line 2, col 1)
Token(IDENTIFIER   | 'a'        | line 2, col 5)
Token(ASSIGN       | '='        | line 2, col 7)
Token(KEYWORD      | 'sin'      | line 2, col 9)
Token(LPAREN       | '('        | line 2, col 12)
Token(FLOAT        | '0.7854'   | line 2, col 13)
Token(RPAREN       | ')'        | line 2, col 19)
Token(SEMICOLON    | ';'        | line 2, col 20)
Token(KEYWORD      | 'let'      | line 3, col 1)
Token(IDENTIFIER   | 'b'        | line 3, col 5)
Token(ASSIGN       | '='        | line 3, col 7)
Token(KEYWORD      | 'cos'      | line 3, col 9)
Token(LPAREN       | '('        | line 3, col 12)
Token(FLOAT        | '0.7854'   | line 3, col 13)
Token(RPAREN       | ')'        | line 3, col 19)
Token(SEMICOLON    | ';'        | line 3, col 20)
Token(KEYWORD      | 'let'      | line 4, col 1)
Token(IDENTIFIER   | 'identity' | line 4, col 5)
Token(ASSIGN       | '='        | line 4, col 14)
Token(IDENTIFIER   | 'a'        | line 4, col 16)
Token(POWER        | '^'        | line 4, col 17)
Token(INTEGER      | '2'        | line 4, col 18)
Token(PLUS         | '+'        | line 4, col 20)
Token(IDENTIFIER   | 'b'        | line 4, col 22)
Token(POWER        | '^'        | line 4, col 23)
Token(INTEGER      | '2'        | line 4, col 24)
Token(SEMICOLON    | ';'        | line 4, col 25)
Token(KEYWORD      | 'if'       | line 5, col 1)
Token(LPAREN       | '('        | line 5, col 4)
Token(IDENTIFIER   | 'identity' | line 5, col 5)
Token(NEQ          | '!='       | line 5, col 14)
Token(FLOAT        | '1.0'      | line 5, col 17)
Token(RPAREN       | ')'        | line 5, col 20)
Token(LBRACE       | '{'        | line 5, col 22)
Token(KEYWORD      | 'return'   | line 5, col 24)
Token(KEYWORD      | 'false'    | line 5, col 31)
Token(SEMICOLON    | ';'        | line 5, col 36)
Token(RBRACE       | '}'        | line 5, col 38)
Token(EOF          | ''         | line 5, col 39)
```

---

## Conclusions

1. The lexer correctly processes all five sample programs, producing well-typed token streams with accurate source positions.
2. A single look-ahead character (`peek`) is sufficient to disambiguate all multi-character operators (`==`, `!=`, `<=`, `>=`, `&&`, `||`) from their single-character prefixes — no backtracking is ever required.
3. The maximal-munch rule (always consume the longest possible match) is straightforward to implement greedily and avoids ambiguity in all tested cases, including numbers with scientific notation (`3.14159e0`).
4. Distinguishing keywords from identifiers *post-recognition* — reading the full word first, then checking against a set — is simpler and more maintainable than encoding keywords as separate DFA paths.
5. Tracking line and column numbers for every token is low-cost during scanning, yet provides invaluable context for error messages in subsequent compiler phases.
6. The implementation handles both `//` line comments and `/* … */` block comments, correctly stripping them before any token is emitted.

---

## References

1) Cojuhari I., Drumea V. *Formal Languages and Finite Automata – Guide for practical lessons.* Technical University of Moldova, 2022.
2) LLVM Project. *My First Language Frontend with LLVM Tutorial.* https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl01.html
3) Wikipedia. *Lexical analysis.* https://en.wikipedia.org/wiki/Lexical_analysis
4) Aho A.V., Lam M.S., Sethi R., Ullman J.D. *Compilers: Principles, Techniques, and Tools.* 2nd ed. Pearson, 2006.