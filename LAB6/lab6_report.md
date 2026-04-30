# Lab 6 – Parser & Building an Abstract Syntax Tree

**Course:** Formal Languages & Finite Automata

**Author:** Mutu Adrian

---

## Theory

**Parsing** (syntactic analysis) is the second stage of a compiler or interpreter pipeline, placed immediately after lexical analysis. Whereas the lexer converts a raw character stream into a flat sequence of tokens, the parser imposes hierarchical structure on that sequence by checking that it conforms to a formal grammar and simultaneously constructing a tree that captures the grammatical relationships between tokens.

The result of parsing is typically one of two tree structures:

1) **Concrete Syntax Tree (CST) / Parse Tree** — a full derivation tree where every grammar rule application is explicit, including punctuation tokens, parentheses, and other syntactically necessary but semantically irrelevant symbols.

2) **Abstract Syntax Tree (AST)** — a more compact tree that retains only the semantically meaningful structure. Redundant tokens (parentheses whose purpose is captured by the tree shape, semicolons that merely terminate statements, etc.) are dropped. This is the representation used in practice by compilers, interpreters, and static analysis tools.

The most common manual parsing technique is **recursive-descent parsing**: each grammar rule is implemented as a function that calls other rule-functions for its sub-expressions. Operator precedence is encoded naturally by the call hierarchy — lower-precedence rules call higher-precedence ones, so higher-precedence operators bind more tightly in the resulting tree.

Key concepts in parsing:

- **Grammar** — a formal specification of the syntactic structure of a language (here written in EBNF form).
- **Precedence** — determines which operators bind their operands more tightly. In the grammar below, `^` (power) binds tighter than `*`/`/`, which bind tighter than `+`/`-`, and so on.
- **Associativity** — determines grouping when the same operator appears consecutively. Addition is left-associative (`a + b + c = (a + b) + c`); power is right-associative (`a ^ b ^ c = a ^ (b ^ c)`).
- **Lookahead** — the number of unconsumed tokens the parser may inspect before deciding which rule to apply. The grammar here is LL(1) for all rules except assignment, which uses one extra token of lookahead to distinguish `IDENT '='` (assignment) from a plain identifier in an expression.

---

## Objectives

1. Get familiar with parsing, what it is and how it can be programmed.
2. Get familiar with the concept of AST.
3. Extending the lexer from Lab 3:

   a) Implement a `TokenType` enum and use **regular expressions** to identify each token type (replacing the character-by-character approach of Lab 3).

   b) Implement the necessary AST node data structures for the scripting language processed in Lab 3.

   c) Implement a recursive-descent parser that extracts the syntactic information from the token stream and produces a well-formed AST.

---

## Language Grammar

The scripting language is defined by the following grammar (EBNF notation):

```
program     → statement*
statement   → let_stmt | if_stmt | while_stmt | return_stmt | expr_stmt
let_stmt    → 'let' IDENT '=' expr ';'
if_stmt     → 'if' '(' expr ')' block ( 'else' block )?
while_stmt  → 'while' '(' expr ')' block
return_stmt → 'return' expr ';'
expr_stmt   → expr ';'
block       → '{' statement* '}'

expr        → assignment
assignment  → IDENT '=' assignment | logical_or
logical_or  → logical_and  ( '||' logical_and  )*
logical_and → equality     ( '&&' equality     )*
equality    → comparison   ( ('=='|'!=') comparison )*
comparison  → addition     ( ('<'|'>'|'<='|'>=') addition )*
addition    → multiply     ( ('+'|'-') multiply     )*
multiply    → unary        ( ('*'|'/'|'%') unary     )*
unary       → ('-'|'!') unary | power
power       → call         ( '^' unary             )*
call        → primary      ( '(' args? ')'          )*
primary     → NUMBER | STRING | BOOL | IDENT | '(' expr ')'
args        → expr (',' expr)*
```

---

## Implementation Description

### 1. Token Types & Regex-based Lexer (`lab6_parser.py`)

Lab 6 requires that token types be identified using **regular expressions**. The lexer is rebuilt around an ordered list of `(regex_pattern, TokenType)` pairs that are compiled once at module load and applied via `re.match` at each position in the source string:

```python
TOKEN_REGEX = [
    (r'\n',                                        TokenType.NEWLINE),
    (r'[ \t\r]+',                                  None),          # skip whitespace
    (r'//[^\n]*',                                  None),          # skip line comment
    (r'/\*[\s\S]*?\*/',                            None),          # skip block comment
    (r'\d+\.\d*(?:[eE][+-]?\d+)?'
     r'|\d*\.\d+(?:[eE][+-]?\d+)?'
     r'|\d+[eE][+-]?\d+',                         TokenType.FLOAT),
    (r'\d+',                                       TokenType.INTEGER),
    (r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'',   TokenType.STRING),
    (r'[A-Za-z_]\w*',                              TokenType.KEYWORD),  # refined below
    (r'==',  TokenType.EQ),    (r'!=', TokenType.NEQ),
    (r'<=',  TokenType.LEQ),   (r'>=', TokenType.GEQ),
    (r'&&',  TokenType.AND),   (r'\|\|', TokenType.OR),
    # ... single-character tokens ...
]
_COMPILED = [(re.compile(pat), tt) for pat, tt in TOKEN_REGEX]
```

The patterns are tried in order; the first match wins (maximal-munch is achieved automatically because Python's `re.match` is anchored at the current position). Words matching `[A-Za-z_]\w*` are initially typed as `KEYWORD`; after matching, the value is checked against the `KEYWORDS` set and reclassified as `IDENTIFIER` if not found.

---

### 2. AST Node Hierarchy

Each syntactic construct in the language is represented by a dedicated Python `@dataclass`. The hierarchy is:

**Expression nodes:**

```python
@dataclass
class NumberLiteral(ASTNode): value: Any;    raw: str
@dataclass
class StringLiteral(ASTNode): value: str
@dataclass
class BoolLiteral(ASTNode):   value: bool
@dataclass
class Identifier(ASTNode):    name: str
@dataclass
class BinaryOp(ASTNode):      op: str;  left: ASTNode;  right: ASTNode
@dataclass
class UnaryOp(ASTNode):       op: str;  operand: ASTNode
@dataclass
class Assignment(ASTNode):    name: str; value: ASTNode
@dataclass
class FunctionCall(ASTNode):  callee: str; args: List[ASTNode]
```

**Statement nodes:**

```python
@dataclass
class LetStatement(ASTNode):    name: str;      value: ASTNode
@dataclass
class ReturnStatement(ASTNode): value: ASTNode
@dataclass
class ExprStatement(ASTNode):   expr: ASTNode
@dataclass
class Block(ASTNode):           statements: List[ASTNode]
@dataclass
class IfStatement(ASTNode):     condition: ASTNode
                                then_branch: Block
                                else_branch: Optional[Block]
@dataclass
class WhileStatement(ASTNode):  condition: ASTNode; body: Block
@dataclass
class Program(ASTNode):         statements: List[ASTNode]
```

The `ASTNode` base class is empty; it serves only as a common type for type-checking and pretty-printing dispatch.

---

### 3. Parser

The `Parser` class holds the token list and a cursor integer `self.pos`. Three cursor helpers keep the code clean:

```python
def _peek(self)  -> Token:  return self.tokens[self.pos]
def _match(self, *tt) -> bool:  # consume and return True if current type in tt
def _expect(self, tt, msg):     # consume or raise ParseError with message
```

#### Statement parsing

The top-level `_statement()` dispatcher inspects the current keyword to route to the appropriate handler:

```python
def _statement(self):
    tok = self._peek()
    if tok.type == TokenType.KEYWORD:
        if tok.value == 'let':    return self._let_stmt()
        if tok.value == 'if':     return self._if_stmt()
        if tok.value == 'while':  return self._while_stmt()
        if tok.value == 'return': return self._return_stmt()
    return self._expr_stmt()
```

Each statement parser consumes exactly the tokens it owns and delegates expression sub-trees to `_expression()`.

#### Expression parsing & precedence

Operator precedence is encoded through the call hierarchy. Each level calls the next-higher level and then loops while it sees its own operator(s):

```python
def _addition(self):
    node = self._multiply()                     # higher precedence first
    while self._match(TokenType.PLUS, TokenType.MINUS):
        op   = self._prev().value               # '+' or '-'
        node = BinaryOp(op, node, self._multiply())
    return node                                 # left-associative by construction
```

Assignment uses one extra token of lookahead to distinguish `x = expr` from a bare identifier:

```python
def _assignment(self):
    if (self._check(TokenType.IDENTIFIER) and
            self.tokens[self.pos + 1].type == TokenType.ASSIGN):
        name = self._peek().value
        self.pos += 2           # consume IDENT and '='
        value = self._assignment()              # right-associative
        return Assignment(name, value)
    return self._logical_or()
```

#### Function calls

`_call()` wraps `_primary()` and checks for a following `(`. If found, it consumes arguments until `)`. Because `_call()` loops, it would support chained calls (`f(x)(y)`), though the language does not use them:

```python
def _call(self):
    node = self._primary()
    while self._match(TokenType.LPAREN):
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        self._expect(TokenType.RPAREN, "Expected ')'")
        node = FunctionCall(node.name, args)
    return node
```

---

### 4. AST Pretty-Printer

`print_ast(node, indent)` recursively walks the AST and prints each node type with its key attributes, using indentation to convey the tree depth. It dispatches on `isinstance` checks, one branch per node class.

---

## Results

Five representative programs were tokenised and parsed. For each, the full token list (excluding NEWLINE/EOF) and the resulting AST are shown.

---

### Sample 1 – Arithmetic Expression

**Input:**
```
3 + 4.5 * (2 - 1) / 0.5;
```

**Tokens:**
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
Token(SEMICOLON    | ';'    | line 1, col 24)
```

**AST:**
```
Program
  ExprStatement
    BinaryOp  op='+'
      NumberLiteral  value=3
      BinaryOp  op='/'
        BinaryOp  op='*'
          NumberLiteral  value=4.5
          BinaryOp  op='-'
            NumberLiteral  value=2
            NumberLiteral  value=1
        NumberLiteral  value=0.5
```

The tree reflects standard operator precedence: `*` and `/` bind tighter than `+`, and the parenthesised sub-expression `(2 - 1)` is correctly nested as a child of `*`.

---

### Sample 2 – Let Statements & Trigonometric Calls

**Input:**
```
let angle = 1.5708;
let result = sin(angle) + cos(0.0) * tan(angle / 2);
```

**Tokens:**
```
Token(KEYWORD      | 'let'    | line 2, col 1)
Token(IDENTIFIER   | 'angle'  | line 2, col 5)
Token(ASSIGN       | '='      | line 2, col 11)
Token(FLOAT        | '1.5708' | line 2, col 13)
Token(SEMICOLON    | ';'      | line 2, col 19)
Token(KEYWORD      | 'let'    | line 3, col 1)
Token(IDENTIFIER   | 'result' | line 3, col 5)
Token(ASSIGN       | '='      | line 3, col 12)
Token(KEYWORD      | 'sin'    | line 3, col 14)
Token(LPAREN       | '('      | line 3, col 17)
Token(IDENTIFIER   | 'angle'  | line 3, col 18)
Token(RPAREN       | ')'      | line 3, col 23)
Token(PLUS         | '+'      | line 3, col 25)
Token(KEYWORD      | 'cos'    | line 3, col 27)
Token(LPAREN       | '('      | line 3, col 30)
Token(FLOAT        | '0.0'    | line 3, col 31)
Token(RPAREN       | ')'      | line 3, col 34)
Token(MULTIPLY     | '*'      | line 3, col 36)
Token(KEYWORD      | 'tan'    | line 3, col 38)
Token(LPAREN       | '('      | line 3, col 41)
Token(IDENTIFIER   | 'angle'  | line 3, col 42)
Token(DIVIDE       | '/'      | line 3, col 48)
Token(INTEGER      | '2'      | line 3, col 50)
Token(RPAREN       | ')'      | line 3, col 51)
Token(SEMICOLON    | ';'      | line 3, col 52)
```

**AST:**
```
Program
  LetStatement  name='angle'
    NumberLiteral  value=1.5708
  LetStatement  name='result'
    BinaryOp  op='+'
      FunctionCall  callee='sin'
        Identifier  name='angle'
      BinaryOp  op='*'
        FunctionCall  callee='cos'
          NumberLiteral  value=0.0
        FunctionCall  callee='tan'
          BinaryOp  op='/'
            Identifier  name='angle'
            NumberLiteral  value=2
```

`sin`, `cos`, and `tan` are correctly parsed as `FunctionCall` nodes. The multiplication `cos(...) * tan(...)` sits below the addition, reflecting left-to-right operator precedence.

---

### Sample 3 – If / Else with Logical Operators

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

**Tokens:**
```
Token(KEYWORD      | 'let'   | line 3, col 1)
Token(IDENTIFIER   | 'x'     | line 3, col 5)
Token(ASSIGN       | '='     | line 3, col 7)
Token(INTEGER      | '42'    | line 3, col 9)
Token(SEMICOLON    | ';'     | line 3, col 11)
Token(KEYWORD      | 'if'    | line 4, col 1)
Token(LPAREN       | '('     | line 4, col 4)
Token(IDENTIFIER   | 'x'     | line 4, col 5)
Token(GEQ          | '>='    | line 4, col 7)
Token(INTEGER      | '0'     | line 4, col 10)
Token(AND          | '&&'    | line 4, col 12)
Token(IDENTIFIER   | 'x'     | line 4, col 15)
Token(LEQ          | '<='    | line 4, col 17)
Token(INTEGER      | '100'   | line 4, col 20)
Token(RPAREN       | ')'     | line 4, col 23)
Token(LBRACE       | '{'     | line 4, col 25)
Token(KEYWORD      | 'return'| line 5, col 5)
Token(KEYWORD      | 'true'  | line 5, col 12)
Token(SEMICOLON    | ';'     | line 5, col 16)
Token(RBRACE       | '}'     | line 6, col 1)
Token(KEYWORD      | 'else'  | line 6, col 3)
Token(LBRACE       | '{'     | line 6, col 8)
Token(KEYWORD      | 'return'| line 7, col 5)
Token(KEYWORD      | 'false' | line 7, col 12)
Token(SEMICOLON    | ';'     | line 7, col 17)
Token(RBRACE       | '}'     | line 8, col 1)
```

**AST:**
```
Program
  LetStatement  name='x'
    NumberLiteral  value=42
  IfStatement
    condition:
      BinaryOp  op='&&'
        BinaryOp  op='>='
          Identifier  name='x'
          NumberLiteral  value=0
        BinaryOp  op='<='
          Identifier  name='x'
          NumberLiteral  value=100
    then:
      Block
        ReturnStatement
          BoolLiteral  value=True
    else:
      Block
        ReturnStatement
          BoolLiteral  value=False
```

The `//` comment is silently stripped by the lexer. The `&&` sits above `>=` and `<=` in the tree, correctly expressing that the comparisons are evaluated first. The `IfStatement` node carries distinct `then_branch` and `else_branch` children.

---

### Sample 4 – String Literal & Power Operator

**Input:**
```
let greeting = "Hello, World!";
let pi = 3.14159e0;
let tau = pi * 2;
let identity = pi^2 + tau^2;
```

**Tokens:**
```
Token(KEYWORD      | 'let'           | line 2, col 1)
Token(IDENTIFIER   | 'greeting'      | line 2, col 5)
Token(ASSIGN       | '='             | line 2, col 14)
Token(STRING       | 'Hello, World!' | line 2, col 16)
Token(SEMICOLON    | ';'             | line 2, col 31)
Token(KEYWORD      | 'let'           | line 3, col 1)
Token(IDENTIFIER   | 'pi'            | line 3, col 5)
Token(ASSIGN       | '='             | line 3, col 8)
Token(FLOAT        | '3.14159e0'     | line 3, col 10)
Token(SEMICOLON    | ';'             | line 3, col 19)
Token(KEYWORD      | 'let'           | line 4, col 1)
Token(IDENTIFIER   | 'tau'           | line 4, col 5)
Token(ASSIGN       | '='             | line 4, col 9)
Token(IDENTIFIER   | 'pi'            | line 4, col 11)
Token(MULTIPLY     | '*'             | line 4, col 14)
Token(INTEGER      | '2'             | line 4, col 16)
Token(SEMICOLON    | ';'             | line 4, col 17)
Token(KEYWORD      | 'let'           | line 5, col 1)
Token(IDENTIFIER   | 'identity'      | line 5, col 5)
Token(ASSIGN       | '='             | line 5, col 14)
Token(IDENTIFIER   | 'pi'            | line 5, col 16)
Token(POWER        | '^'             | line 5, col 18)
Token(INTEGER      | '2'             | line 5, col 19)
Token(PLUS         | '+'             | line 5, col 21)
Token(IDENTIFIER   | 'tau'           | line 5, col 23)
Token(POWER        | '^'             | line 5, col 26)
Token(INTEGER      | '2'             | line 5, col 27)
Token(SEMICOLON    | ';'             | line 5, col 28)
```

**AST:**
```
Program
  LetStatement  name='greeting'
    StringLiteral  value='Hello, World!'
  LetStatement  name='pi'
    NumberLiteral  value=3.14159
  LetStatement  name='tau'
    BinaryOp  op='*'
      Identifier  name='pi'
      NumberLiteral  value=2
  LetStatement  name='identity'
    BinaryOp  op='+'
      BinaryOp  op='^'
        Identifier  name='pi'
        NumberLiteral  value=2
      BinaryOp  op='^'
        Identifier  name='tau'
        NumberLiteral  value=2
```

String quotes are stripped by the lexer so the `StringLiteral` node holds only the content. The power operator `^` binds tighter than `+`, so `pi^2` and `tau^2` are both children of the `+` node.

---

### Sample 5 – While Loop & In-place Assignment

**Input:**
```
let i = 0;
let total = 0;
while (i <= 10) {
    total = total + i;
    i = i + 1;
}
return total;
```

**Tokens:**
```
Token(KEYWORD      | 'let'   | line 2, col 1)
Token(IDENTIFIER   | 'i'     | line 2, col 5)
Token(ASSIGN       | '='     | line 2, col 7)
Token(INTEGER      | '0'     | line 2, col 9)
Token(SEMICOLON    | ';'     | line 2, col 10)
Token(KEYWORD      | 'let'   | line 3, col 1)
Token(IDENTIFIER   | 'total' | line 3, col 5)
Token(ASSIGN       | '='     | line 3, col 11)
Token(INTEGER      | '0'     | line 3, col 13)
Token(SEMICOLON    | ';'     | line 3, col 14)
Token(KEYWORD      | 'while' | line 4, col 1)
Token(LPAREN       | '('     | line 4, col 7)
Token(IDENTIFIER   | 'i'     | line 4, col 8)
Token(LEQ          | '<='    | line 4, col 10)
Token(INTEGER      | '10'    | line 4, col 13)
Token(RPAREN       | ')'     | line 4, col 15)
Token(LBRACE       | '{'     | line 4, col 17)
Token(IDENTIFIER   | 'total' | line 5, col 5)
Token(ASSIGN       | '='     | line 5, col 11)
Token(IDENTIFIER   | 'total' | line 5, col 13)
Token(PLUS         | '+'     | line 5, col 19)
Token(IDENTIFIER   | 'i'     | line 5, col 21)
Token(SEMICOLON    | ';'     | line 5, col 22)
Token(IDENTIFIER   | 'i'     | line 6, col 5)
Token(ASSIGN       | '='     | line 6, col 7)
Token(IDENTIFIER   | 'i'     | line 6, col 9)
Token(PLUS         | '+'     | line 6, col 11)
Token(INTEGER      | '1'     | line 6, col 13)
Token(SEMICOLON    | ';'     | line 6, col 14)
Token(RBRACE       | '}'     | line 7, col 1)
Token(KEYWORD      | 'return'| line 8, col 1)
Token(IDENTIFIER   | 'total' | line 8, col 8)
Token(SEMICOLON    | ';'     | line 8, col 13)
```

**AST:**
```
Program
  LetStatement  name='i'
    NumberLiteral  value=0
  LetStatement  name='total'
    NumberLiteral  value=0
  WhileStatement
    condition:
      BinaryOp  op='<='
        Identifier  name='i'
        NumberLiteral  value=10
    body:
      Block
        ExprStatement
          Assignment  name='total'
            BinaryOp  op='+'
              Identifier  name='total'
              Identifier  name='i'
        ExprStatement
          Assignment  name='i'
            BinaryOp  op='+'
              Identifier  name='i'
              NumberLiteral  value=1
  ReturnStatement
    Identifier  name='total'
```

In-loop assignments (`total = total + i`) are parsed as `Assignment` nodes rather than `LetStatement`, correctly distinguishing declaration from re-assignment. The `WhileStatement` node holds a `condition` sub-tree and a `Block` body.

---

## Conclusions

1. Replacing the character-by-character lexer from Lab 3 with a **regex-driven lexer** substantially simplifies the implementation. Each token type is described by a self-contained regular expression; the lexer simply tries patterns in priority order at every position, which naturally implements maximal-munch without explicit state machines.
2. The **AST node hierarchy** maps one-to-one onto the grammar rules of the language. Using Python `@dataclass` for each node type makes the structure explicit, avoids boilerplate, and lets the pretty-printer dispatch cleanly on `isinstance` checks.
3. **Recursive-descent parsing** encodes operator precedence through the function call hierarchy in a way that is easy to read, modify, and extend. Adding a new precedence level requires adding one new method at the correct position in the chain — no precedence tables or parser generators are needed.
4. **Left-associativity** is achieved automatically by the `while self._match(...)` loop in each precedence level: the left operand accumulates as the loop iterates. **Right-associativity** (used for assignment and power) is achieved by having the rule call itself recursively on the right operand instead of looping.
5. The single-token lookahead in `_assignment()` (checking whether `tokens[pos+1]` is `=`) is sufficient to avoid ambiguity between an assignment target and an identifier in an expression. The rest of the grammar is strictly LL(1) — one unconsumed token is always enough to decide which rule to apply.
6. The clean separation of **Lexer → Token stream → Parser → AST** layers means each component can be tested and extended independently — for example, the lexer from Lab 3 could be swapped in without changing the parser, or the parser could be retargeted to a different grammar without touching the lexer.

---

## References

1) Cojuhari I., Drumea V. *Formal Languages and Finite Automata – Guide for practical lessons.* Technical University of Moldova, 2022.
2) Crafting Interpreters – Robert Nystrom. https://craftinginterpreters.com
3) Wikipedia. *Parsing.* https://en.wikipedia.org/wiki/Parsing
4) Wikipedia. *Abstract Syntax Tree.* https://en.wikipedia.org/wiki/Abstract_syntax_tree
5) Aho A.V., Lam M.S., Sethi R., Ullman J.D. *Compilers: Principles, Techniques, and Tools.* 2nd ed. Pearson, 2006.