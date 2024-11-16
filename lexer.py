# lexer.py

import re
from ast_nodes import *

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f'Token({self.type}, {self.value}, Line: {self.line}, Column: {self.column})'

class Lexer:
    def __init__(self, code):
        self.code = code
        self.keywords = {'var', 'if', 'else', 'while', 'for', 'function', 'return', 'print', 'import', 'pointer'}
        self.token_specification = [
            ('MCOMMENT', r'/\*[\s\S]*?\*/'),          # Multiline Comment
            ('COMMENT',  r'//.*'),                    # Single Line Comment
            ('NUMBER',   r'\b\d+(\.\d+)?\b'),         # Integer or Decimal Number
            ('STRING',   r'"([^"\\]|\\.)*"'),         # String Literal
            ('AND',      r'\bAND\b'),                 # Logical AND
            ('OR',       r'\bOR\b'),                  # Logical OR
            ('NOT',      r'\bNOT\b'),                 # Logical NOT
            ('ID',       r'\b[A-Za-z_]\w*\b'),        # Identifiers
            ('POINTER',  r'\*'),                      # Pointer Symbol
            ('ASSIGN',   r'='),                        # Assignment Operator
            ('END',      r';'),                        # Statement Terminator
            ('EQ',       r'=='),                       # Equal Operator
            ('NEQ',      r'!='),                       # Not Equal Operator
            ('GTE',      r'>='),                       # Greater Than or Equal
            ('LTE',      r'<='),                       # Less Than or Equal
            ('GT',       r'>'),                        # Greater Than
            ('LT',       r'<'),                        # Less Than
            ('OP',       r'[+\-*/]'),                  # Arithmetic Operators
            ('LPAREN',   r'\('),                       # Left Parenthesis
            ('RPAREN',   r'\)'),                       # Right Parenthesis
            ('LBRACE',   r'\{'),                       # Left Brace
            ('RBRACE',   r'\}'),                       # Right Brace
            ('LBRACKET', r'\['),                       # Left Bracket
            ('RBRACKET', r'\]'),                       # Right Bracket
            ('COMMA',    r','),                        # Comma
            ('DOT',      r'\.'),                       # Dot for Attribute Access
            ('NEWLINE',  r'\n'),                       # Line Break
            ('SKIP',     r'[ \t]+'),                   # Skip Over Spaces and Tabs
            ('MISMATCH', r'.'),                        # Any Other Character
        ]

        self.token_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.token_specification)
        self.line = 1
        self.column = 1

    def tokenize(self):
        tokens = []
        for mo in re.finditer(self.token_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'NUMBER':
                value = float(value) if '.' in value else int(value)
                tokens.append(Token('NUMBER', value, self.line, self.column))
            elif kind == 'STRING':
                # Handle escape sequences within strings
                value = bytes(value[1:-1], "utf-8").decode("unicode_escape")
                tokens.append(Token('STRING', value, self.line, self.column))
            elif kind in {'AND', 'OR', 'NOT'}:
                tokens.append(Token(kind, value, self.line, self.column))
            elif kind == 'ID':
                lower_val = value.lower()
                if lower_val in self.keywords:
                    tokens.append(Token(lower_val.upper(), value, self.line, self.column))
                elif lower_val in {'true', 'false'}:
                    tokens.append(Token('BOOLEAN', lower_val == 'true', self.line, self.column))
                else:
                    tokens.append(Token('ID', value, self.line, self.column))
            elif kind in {'ASSIGN', 'END', 'EQ', 'NEQ', 'GTE', 'LTE', 'GT', 'LT', 'OP', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'COMMA', 'DOT', 'LBRACKET', 'RBRACKET', 'POINTER'}:
                tokens.append(Token(kind, value, self.line, self.column))
            elif kind == 'NEWLINE':
                self.line += 1
                self.column = 0
            elif kind in {'SKIP', 'COMMENT', 'MCOMMENT'}:
                pass  # Ignore whitespace and comments
            elif kind == 'MISMATCH':
                raise SyntaxError(f'Unexpected character {value!r} at line {self.line} column {self.column}')
            self.column += mo.end() - mo.start()
        tokens.append(Token('EOF', '', self.line, self.column))
        return tokens