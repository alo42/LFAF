"""
Laboratory Work 6 – Parser & AST Builder
Course: Formal Languages & Finite Automata
Author: Mutu Adrian

Extends Lab 3 (Lexer) with:
  - regex-based TokenType categorisation
  - AST node hierarchy
  - recursive-descent parser that produces an AST
  - AST pretty-printer

Language grammar (informal):
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
  logical_or  → logical_and ( '||' logical_and )*
  logical_and → equality   ( '&&' equality   )*
  equality    → comparison ( ('=='|'!=') comparison )*
  comparison  → addition   ( ('<'|'>'|'<='|'>=') addition )*
  addition    → multiply   ( ('+'|'-') multiply )*
  multiply    → unary      ( ('*'|'/'|'%') unary )*
  unary       → ('-'|'!') unary | power
  power       → call       ( '^' unary )*
  call        → primary    ( '(' args? ')' )*
  primary     → NUMBER | STRING | BOOL | IDENT | '(' expr ')'
  args        → expr (',' expr)*
"""

import re
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Any


# ══════════════════════════════════════════════════════════════════════════════
# 1.  TOKEN TYPES  (regex-based, as required by Lab 6)
# ══════════════════════════════════════════════════════════════════════════════

class TokenType(Enum):
    # Literals
    FLOAT      = auto()
    INTEGER    = auto()
    STRING     = auto()
    # Keywords & identifiers
    KEYWORD    = auto()
    IDENTIFIER = auto()
    # Arithmetic
    PLUS       = auto()
    MINUS      = auto()
    MULTIPLY   = auto()
    DIVIDE     = auto()
    MODULO     = auto()
    POWER      = auto()
    # Relational / assignment
    ASSIGN     = auto()
    EQ         = auto()
    NEQ        = auto()
    LT         = auto()
    GT         = auto()
    LEQ        = auto()
    GEQ        = auto()
    # Logical
    AND        = auto()
    OR         = auto()
    NOT        = auto()
    # Delimiters
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACE     = auto()
    RBRACE     = auto()
    COMMA      = auto()
    SEMICOLON  = auto()
    # Special
    NEWLINE    = auto()
    EOF        = auto()
    UNKNOWN    = auto()


KEYWORDS = {
    "sin", "cos", "tan", "asin", "acos", "atan",
    "let", "if", "else", "while", "return",
    "true", "false", "and", "or", "not",
}

# Ordered list of (regex_pattern, TokenType).
# The lexer tries each pattern in order and takes the first match.
TOKEN_REGEX: List[tuple] = [
    (r'\n',                                    TokenType.NEWLINE),
    (r'[ \t\r]+',                              None),             # whitespace → skip
    (r'//[^\n]*',                              None),             # line comment → skip
    (r'/\*[\s\S]*?\*/',                        None),             # block comment → skip
    (r'\d+\.\d*(?:[eE][+-]?\d+)?'
     r'|\d*\.\d+(?:[eE][+-]?\d+)?'
     r'|\d+[eE][+-]?\d+',                     TokenType.FLOAT),
    (r'\d+',                                   TokenType.INTEGER),
    (r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', TokenType.STRING),
    (r'[A-Za-z_]\w*',                          TokenType.KEYWORD),  # refined below
    (r'==',                                    TokenType.EQ),
    (r'!=',                                    TokenType.NEQ),
    (r'<=',                                    TokenType.LEQ),
    (r'>=',                                    TokenType.GEQ),
    (r'&&',                                    TokenType.AND),
    (r'\|\|',                                  TokenType.OR),
    (r'\+',                                    TokenType.PLUS),
    (r'-',                                     TokenType.MINUS),
    (r'\*',                                    TokenType.MULTIPLY),
    (r'/',                                     TokenType.DIVIDE),
    (r'%',                                     TokenType.MODULO),
    (r'\^',                                    TokenType.POWER),
    (r'=',                                     TokenType.ASSIGN),
    (r'<',                                     TokenType.LT),
    (r'>',                                     TokenType.GT),
    (r'!',                                     TokenType.NOT),
    (r'\(',                                    TokenType.LPAREN),
    (r'\)',                                    TokenType.RPAREN),
    (r'\{',                                    TokenType.LBRACE),
    (r'\}',                                    TokenType.RBRACE),
    (r',',                                     TokenType.COMMA),
    (r';',                                     TokenType.SEMICOLON),
    (r'.',                                     TokenType.UNKNOWN),
]

# Pre-compile
_COMPILED = [(re.compile(pat), tt) for pat, tt in TOKEN_REGEX]


# ══════════════════════════════════════════════════════════════════════════════
# 2.  TOKEN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Token:
    type:   TokenType
    value:  str
    line:   int
    column: int

    def __repr__(self):
        return (f"Token({self.type.name:<12} | {self.value!r:<18} "
                f"| line {self.line}, col {self.column})")


# ══════════════════════════════════════════════════════════════════════════════
# 3.  LEXER  (regex-based, satisfies Lab 6 requirement)
# ══════════════════════════════════════════════════════════════════════════════

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.col    = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.source):
            for pattern, ttype in _COMPILED:
                m = pattern.match(self.source, self.pos)
                if not m:
                    continue
                raw = m.group(0)
                if ttype is None:
                    # skip (whitespace / comments)
                    self._advance_by(raw)
                    break
                if ttype == TokenType.NEWLINE:
                    self.line += 1
                    self.col   = 1
                    self.pos  += 1
                    break
                # Distinguish KEYWORD vs IDENTIFIER
                if ttype == TokenType.KEYWORD:
                    ttype = TokenType.KEYWORD if raw in KEYWORDS else TokenType.IDENTIFIER
                # Strip surrounding quotes from strings
                value = raw
                if ttype == TokenType.STRING:
                    value = raw[1:-1].encode('raw_unicode_escape').decode('unicode_escape')
                tok = Token(ttype, value, self.line, self.col)
                tokens.append(tok)
                self._advance_by(raw)
                break
        tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return tokens

    def _advance_by(self, text: str):
        for ch in text:
            if ch == '\n':
                self.line += 1
                self.col   = 1
            else:
                self.col  += 1
        self.pos += len(text)


# ══════════════════════════════════════════════════════════════════════════════
# 4.  AST NODE HIERARCHY
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    pass

# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class NumberLiteral(ASTNode):
    value: Any          # int or float
    raw:   str

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class BoolLiteral(ASTNode):
    value: bool

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class BinaryOp(ASTNode):
    op:    str
    left:  ASTNode
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op:      str
    operand: ASTNode

@dataclass
class Assignment(ASTNode):
    name:  str
    value: ASTNode

@dataclass
class FunctionCall(ASTNode):
    callee: str
    args:   List[ASTNode] = field(default_factory=list)

# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class LetStatement(ASTNode):
    name:  str
    value: ASTNode

@dataclass
class ReturnStatement(ASTNode):
    value: ASTNode

@dataclass
class ExprStatement(ASTNode):
    expr: ASTNode

@dataclass
class Block(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass
class IfStatement(ASTNode):
    condition:   ASTNode
    then_branch: Block
    else_branch: Optional[Block] = None

@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body:      Block

@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# 5.  PARSER  (recursive descent)
# ══════════════════════════════════════════════════════════════════════════════

class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos    = 0

    # ── cursor helpers ────────────────────────────────────────────────────────

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _prev(self) -> Token:
        return self.tokens[self.pos - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, *ttypes) -> bool:
        return self._peek().type in ttypes

    def _match(self, *ttypes) -> bool:
        if self._check(*ttypes):
            self.pos += 1
            return True
        return False

    def _expect(self, ttype: TokenType, msg: str) -> Token:
        if self._check(ttype):
            tok = self._peek()
            self.pos += 1
            return tok
        tok = self._peek()
        raise ParseError(
            f"[line {tok.line}, col {tok.col}] {msg} "
            f"(got {tok.type.name} '{tok.value}')"
        )

    def _expect_keyword(self, word: str) -> Token:
        tok = self._peek()
        if tok.type == TokenType.KEYWORD and tok.value == word:
            self.pos += 1
            return tok
        raise ParseError(
            f"[line {tok.line}] Expected keyword '{word}' "
            f"(got {tok.type.name} '{tok.value}')"
        )

    # ── grammar rules ─────────────────────────────────────────────────────────

    def parse(self) -> Program:
        stmts = []
        while not self._is_at_end():
            stmts.append(self._statement())
        return Program(stmts)

    # statement → let | if | while | return | expr_stmt
    def _statement(self) -> ASTNode:
        tok = self._peek()
        if tok.type == TokenType.KEYWORD:
            if tok.value == 'let':
                return self._let_stmt()
            if tok.value == 'if':
                return self._if_stmt()
            if tok.value == 'while':
                return self._while_stmt()
            if tok.value == 'return':
                return self._return_stmt()
        return self._expr_stmt()

    def _let_stmt(self) -> LetStatement:
        self._expect_keyword('let')
        name = self._expect(TokenType.IDENTIFIER, "Expected variable name").value
        self._expect(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self._expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after let value")
        return LetStatement(name, value)

    def _if_stmt(self) -> IfStatement:
        self._expect_keyword('if')
        self._expect(TokenType.LPAREN, "Expected '(' after 'if'")
        cond = self._expression()
        self._expect(TokenType.RPAREN, "Expected ')' after condition")
        then_b = self._block()
        else_b = None
        if self._peek().type == TokenType.KEYWORD and self._peek().value == 'else':
            self.pos += 1
            else_b = self._block()
        return IfStatement(cond, then_b, else_b)

    def _while_stmt(self) -> WhileStatement:
        self._expect_keyword('while')
        self._expect(TokenType.LPAREN, "Expected '(' after 'while'")
        cond = self._expression()
        self._expect(TokenType.RPAREN, "Expected ')' after condition")
        body = self._block()
        return WhileStatement(cond, body)

    def _return_stmt(self) -> ReturnStatement:
        self._expect_keyword('return')
        value = self._expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after return value")
        return ReturnStatement(value)

    def _expr_stmt(self) -> ExprStatement:
        expr = self._expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStatement(expr)

    def _block(self) -> Block:
        self._expect(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmts.append(self._statement())
        self._expect(TokenType.RBRACE, "Expected '}'")
        return Block(stmts)

    # ── expression precedence levels (low → high) ─────────────────────────────

    def _expression(self) -> ASTNode:
        return self._assignment()

    def _assignment(self) -> ASTNode:
        # peek: if IDENT followed by '=' treat as assignment
        if (self._check(TokenType.IDENTIFIER) and
                self.pos + 1 < len(self.tokens) and
                self.tokens[self.pos + 1].type == TokenType.ASSIGN):
            name = self._peek().value
            self.pos += 2          # consume IDENT and '='
            value = self._assignment()
            return Assignment(name, value)
        return self._logical_or()

    def _logical_or(self) -> ASTNode:
        node = self._logical_and()
        while self._match(TokenType.OR):
            node = BinaryOp('||', node, self._logical_and())
        return node

    def _logical_and(self) -> ASTNode:
        node = self._equality()
        while self._match(TokenType.AND):
            node = BinaryOp('&&', node, self._equality())
        return node

    def _equality(self) -> ASTNode:
        node = self._comparison()
        while self._match(TokenType.EQ, TokenType.NEQ):
            op = self._prev().value
            node = BinaryOp(op, node, self._comparison())
        return node

    def _comparison(self) -> ASTNode:
        node = self._addition()
        while self._match(TokenType.LT, TokenType.GT, TokenType.LEQ, TokenType.GEQ):
            op = self._prev().value
            node = BinaryOp(op, node, self._addition())
        return node

    def _addition(self) -> ASTNode:
        node = self._multiply()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._prev().value
            node = BinaryOp(op, node, self._multiply())
        return node

    def _multiply(self) -> ASTNode:
        node = self._unary()
        while self._match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op = self._prev().value
            node = BinaryOp(op, node, self._unary())
        return node

    def _unary(self) -> ASTNode:
        if self._match(TokenType.NOT):
            return UnaryOp('!', self._unary())
        if self._match(TokenType.MINUS):
            return UnaryOp('-', self._unary())
        return self._power()

    def _power(self) -> ASTNode:
        node = self._call()
        while self._match(TokenType.POWER):
            node = BinaryOp('^', node, self._unary())
        return node

    def _call(self) -> ASTNode:
        node = self._primary()
        # function call: IDENT '(' args ')'
        while self._match(TokenType.LPAREN):
            if not isinstance(node, Identifier):
                raise ParseError("Can only call identifiers")
            args = []
            if not self._check(TokenType.RPAREN):
                args.append(self._expression())
                while self._match(TokenType.COMMA):
                    args.append(self._expression())
            self._expect(TokenType.RPAREN, "Expected ')' after arguments")
            node = FunctionCall(node.name, args)
        return node

    def _primary(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.FLOAT:
            self.pos += 1
            return NumberLiteral(float(tok.value), tok.value)

        if tok.type == TokenType.INTEGER:
            self.pos += 1
            return NumberLiteral(int(tok.value), tok.value)

        if tok.type == TokenType.STRING:
            self.pos += 1
            return StringLiteral(tok.value)

        if tok.type == TokenType.KEYWORD and tok.value in ('true', 'false'):
            self.pos += 1
            return BoolLiteral(tok.value == 'true')

        if tok.type in (TokenType.IDENTIFIER, TokenType.KEYWORD):
            self.pos += 1
            return Identifier(tok.value)

        if tok.type == TokenType.LPAREN:
            self.pos += 1
            expr = self._expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise ParseError(
            f"[line {tok.line}, col {tok.col}] "
            f"Unexpected token {tok.type.name} '{tok.value}'"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 6.  AST PRETTY-PRINTER
# ══════════════════════════════════════════════════════════════════════════════

def print_ast(node: ASTNode, indent: int = 0, prefix: str = ""):
    pad = "  " * indent
    if isinstance(node, Program):
        print(f"{pad}Program")
        for s in node.statements:
            print_ast(s, indent + 1)

    elif isinstance(node, LetStatement):
        print(f"{pad}LetStatement  name='{node.name}'")
        print_ast(node.value, indent + 1)

    elif isinstance(node, ReturnStatement):
        print(f"{pad}ReturnStatement")
        print_ast(node.value, indent + 1)

    elif isinstance(node, ExprStatement):
        print(f"{pad}ExprStatement")
        print_ast(node.expr, indent + 1)

    elif isinstance(node, IfStatement):
        print(f"{pad}IfStatement")
        print(f"{pad}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{pad}  then:")
        print_ast(node.then_branch, indent + 2)
        if node.else_branch:
            print(f"{pad}  else:")
            print_ast(node.else_branch, indent + 2)

    elif isinstance(node, WhileStatement):
        print(f"{pad}WhileStatement")
        print(f"{pad}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{pad}  body:")
        print_ast(node.body, indent + 2)

    elif isinstance(node, Block):
        print(f"{pad}Block")
        for s in node.statements:
            print_ast(s, indent + 1)

    elif isinstance(node, BinaryOp):
        print(f"{pad}BinaryOp  op='{node.op}'")
        print_ast(node.left,  indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, UnaryOp):
        print(f"{pad}UnaryOp  op='{node.op}'")
        print_ast(node.operand, indent + 1)

    elif isinstance(node, Assignment):
        print(f"{pad}Assignment  name='{node.name}'")
        print_ast(node.value, indent + 1)

    elif isinstance(node, FunctionCall):
        print(f"{pad}FunctionCall  callee='{node.callee}'")
        for a in node.args:
            print_ast(a, indent + 1)

    elif isinstance(node, NumberLiteral):
        print(f"{pad}NumberLiteral  value={node.value}")

    elif isinstance(node, StringLiteral):
        print(f"{pad}StringLiteral  value={node.value!r}")

    elif isinstance(node, BoolLiteral):
        print(f"{pad}BoolLiteral  value={node.value}")

    elif isinstance(node, Identifier):
        print(f"{pad}Identifier  name='{node.name}'")

    else:
        print(f"{pad}{type(node).__name__}")


# ══════════════════════════════════════════════════════════════════════════════
# 7.  DEMO  –  five representative inputs
# ══════════════════════════════════════════════════════════════════════════════

SAMPLES = [
    # ── Sample 1: arithmetic expression ───────────────────────────────────────
    ("Sample 1 – Arithmetic Expression",
     "3 + 4.5 * (2 - 1) / 0.5;"),

    # ── Sample 2: let + trig function calls ───────────────────────────────────
    ("Sample 2 – Let Statements & Trigonometric Calls",
     """
let angle = 1.5708;
let result = sin(angle) + cos(0.0) * tan(angle / 2);
"""),

    # ── Sample 3: if / else with logical operators ─────────────────────────────
    ("Sample 3 – If / Else with Logical Operators",
     """
// check if number is in range
let x = 42;
if (x >= 0 && x <= 100) {
    return true;
} else {
    return false;
}
"""),

    # ── Sample 4: string literal + power operator ──────────────────────────────
    ("Sample 4 – String Literal & Power Operator",
     """
let greeting = "Hello, World!";
let pi = 3.14159e0;
let tau = pi * 2;
let identity = pi^2 + tau^2;
"""),

    # ── Sample 5: while loop + assignment ─────────────────────────────────────
    ("Sample 5 – While Loop & In-place Assignment",
     """
let i = 0;
let total = 0;
while (i <= 10) {
    total = total + i;
    i = i + 1;
}
return total;
"""),
]


def run_sample(title: str, source: str):
    sep = "═" * 64
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)

    print("\n── Source ──────────────────────────────────────────────")
    for ln in source.strip().splitlines():
        print(f"  {ln}")

    # Lex
    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    sig_tokens = [t for t in tokens if t.type not in
                  (TokenType.NEWLINE, TokenType.EOF)]
    print("\n── Tokens ──────────────────────────────────────────────")
    for t in sig_tokens:
        print(f"  {t}")

    # Parse
    parser = Parser(tokens)
    ast    = parser.parse()
    print("\n── AST ─────────────────────────────────────────────────")
    print_ast(ast)


if __name__ == "__main__":
    for title, src in SAMPLES:
        run_sample(title, src)