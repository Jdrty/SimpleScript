# parser.py

from ast_nodes import *
import re

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    def expect(self, type_):
        token = self.peek()
        if token.type == type_:
            self.advance()
            return token
        else:
            raise SyntaxError(f'Expected token {type_}, got {token.type} at line {token.line} column {token.column}')

    def parse(self):
        statements = []
        while self.peek().type != 'EOF':
            stmt = self.statement()
            statements.append(stmt)
        return Program(statements)  # Assuming a Program node to encapsulate all statements

    def statement(self):
        token = self.peek()
        if token.type == 'VAR':
            return self.var_declaration()
        elif token.type == 'POINTER':
            return self.pointer_declaration()
        elif token.type == 'IMPORT':
            return self.import_statement()
        elif token.type == 'FUNCTION':
            return self.function_declaration()
        elif token.type == 'IF':
            return self.if_statement()
        elif token.type == 'WHILE':
            return self.while_statement()
        elif token.type == 'FOR':
            return self.for_statement()
        elif token.type == 'RETURN':
            return self.return_statement()
        elif token.type == 'PRINT':
            return self.print_statement()
        elif token.type == 'ID':
            if self.pos + 1 < len(self.tokens):
                next_token = self.tokens[self.pos + 1]
                if next_token.type == 'ASSIGN':
                    return self.assignment()
                elif next_token.type == 'LPAREN':
                    return self.function_call_statement()
                elif next_token.type == 'LBRACKET':
                    return self.array_assignment()
                else:
                    raise SyntaxError(f'Unexpected token {next_token.type} after ID at line {next_token.line} column {next_token.column}')
            else:
                raise SyntaxError(f'Unexpected end of input after ID at line {token.line} column {token.column}')
        else:
            raise SyntaxError(f'Unexpected token {token.type} at line {token.line} column {token.column}')

    def var_declaration(self):
        self.expect('VAR')
        var_type_token = self.peek()
        if var_type_token.type not in {'ID'}:
            raise SyntaxError(f'Invalid variable type {var_type_token.value} at line {var_type_token.line} column {var_type_token.column}')
        var_type = var_type_token.value.lower()
        if var_type not in {'integer', 'float', 'string', 'boolean'}:
            raise SyntaxError(f'Unknown variable type {var_type} at line {var_type_token.line} column {var_type_token.column}')
        self.advance()
        var_name = self.expect('ID').value
        self.expect('ASSIGN')
        expr = self.expression()
        self.expect('END')
        return VarDeclaration(var_type, var_name, expr)

    def pointer_declaration(self):
        self.expect('POINTER')
        var_type_token = self.peek()
        if var_type_token.type not in {'ID'}:
            raise SyntaxError(f'Invalid pointer type {var_type_token.value} at line {var_type_token.line} column {var_type_token.column}')
        var_type = var_type_token.value.lower()
        if var_type not in {'integer', 'float', 'string', 'boolean'}:
            raise SyntaxError(f'Unknown pointer type {var_type} at line {var_type_token.line} column {var_type_token.column}')
        self.advance()
        var_name = self.expect('ID').value
        self.expect('ASSIGN')
        expr = self.expression()
        self.expect('END')
        return PointerDeclaration(var_type, var_name, expr)  # Correctly references the new AST node

    def import_statement(self):
        self.expect('IMPORT')
        module_name_token = self.peek()
        if module_name_token.type != 'STRING':
            raise SyntaxError(f'Expected module name as string in import statement at line {module_name_token.line} column {module_name_token.column}')
        module_name = module_name_token.value
        self.advance()
        self.expect('END')
        return ImportStatement(module_name)

    def assignment(self):
        var_name = self.expect('ID').value
        self.expect('ASSIGN')
        expr = self.expression()
        self.expect('END')
        return Assignment(var_name, expr)

    def array_assignment(self):
        array_name = self.expect('ID').value
        self.expect('LBRACKET')
        index_expr = self.expression()
        self.expect('RBRACKET')
        self.expect('ASSIGN')
        expr = self.expression()
        self.expect('END')
        return ArrayAssignment(array_name, index_expr, expr)  # Correctly references the new AST node

    def print_statement(self):
        self.expect('PRINT')
        self.expect('LPAREN')
        expr = self.expression()
        self.expect('RPAREN')
        self.expect('END')
        return PrintStatement(expr)

    def if_statement(self):
        self.expect('IF')
        self.expect('LPAREN')
        condition = self.expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        then_branch = []
        while self.peek().type != 'RBRACE':
            then_branch.append(self.statement())
        self.expect('RBRACE')
        else_branch = None
        if self.peek().type == 'ELSE':
            self.advance()
            self.expect('LBRACE')
            else_branch = []
            while self.peek().type != 'RBRACE':
                else_branch.append(self.statement())
            self.expect('RBRACE')
        return IfStatement(condition, then_branch, else_branch)

    def while_statement(self):
        self.expect('WHILE')
        self.expect('LPAREN')
        condition = self.expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = []
        while self.peek().type != 'RBRACE':
            body.append(self.statement())
        self.expect('RBRACE')
        return WhileStatement(condition, body)

    def for_statement(self):
        self.expect('FOR')
        self.expect('LPAREN')
        if self.peek().type == 'VAR':
            init = self.var_declaration()
        elif self.peek().type == 'POINTER':
            init = self.pointer_declaration()
        elif self.peek().type == 'ID':
            init = self.assignment()
        else:
            raise SyntaxError(f'Invalid initialization in for loop at line {self.peek().line} column {self.peek().column}')
        condition = self.expression()
        self.expect('END')
        if self.peek().type in {'ID', 'POINTER'}:
            if self.peek().type == 'POINTER':
                increment = self.pointer_declaration()
            else:
                var_name = self.expect('ID').value
                self.expect('ASSIGN')
                expr = self.expression()
                increment = Assignment(var_name, expr)
        else:
            raise SyntaxError(f'Invalid increment in for loop at line {self.peek().line} column {self.peek().column}')
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = []
        while self.peek().type != 'RBRACE':
            body.append(self.statement())
        self.expect('RBRACE')
        return ForStatement(init, condition, increment, body)

    def function_declaration(self):
        self.expect('FUNCTION')
        func_name = self.expect('ID').value
        self.expect('LPAREN')
        params = []
        if self.peek().type != 'RPAREN':
            while True:
                param = self.expect('ID').value
                params.append(param)
                if self.peek().type != 'COMMA':
                    break
                self.expect('COMMA')
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = []
        while self.peek().type != 'RBRACE':
            body.append(self.statement())
        self.expect('RBRACE')
        return FunctionDeclaration(func_name, params, body)

    def function_call_statement(self):
        call = self.function_call()
        self.expect('END')
        return call

    def function_call(self):
        name = self.variable()
        self.expect('LPAREN')
        args = []
        if self.peek().type != 'RPAREN':
            while True:
                arg = self.expression()
                args.append(arg)
                if self.peek().type != 'COMMA':
                    break
                self.expect('COMMA')
        self.expect('RPAREN')
        return FunctionCall(name, args)

    def return_statement(self):
        self.expect('RETURN')
        expr = self.expression()
        self.expect('END')
        return ReturnStatement(expr)

    def expression(self):
        return self.logical_or()

    def logical_or(self):
        node = self.logical_and()
        while self.peek().type == 'OR':
            op = self.expect('OR').value
            right = self.logical_and()
            node = BinaryOp(node, op, right)
        return node

    def logical_and(self):
        node = self.equality()
        while self.peek().type == 'AND':
            op = self.expect('AND').value
            right = self.equality()
            node = BinaryOp(node, op, right)
        return node

    def equality(self):
        node = self.comparison()
        while self.peek().type in {'EQ', 'NEQ'}:
            op = self.expect(self.peek().type).value
            right = self.comparison()
            node = BinaryOp(node, op, right)
        return node

    def comparison(self):
        node = self.term()
        while self.peek().type in {'GT', 'LT', 'GTE', 'LTE'}:
            op = self.expect(self.peek().type).value
            right = self.term()
            node = BinaryOp(node, op, right)
        return node

    def term(self):
        node = self.factor()
        while self.peek().type == 'OP' and self.peek().value in {'+', '-', '*', '/'}:
            op = self.expect('OP').value
            right = self.factor()
            node = BinaryOp(node, op, right)
        return node

    def factor(self):
        node = self.unary()
        return node

    def unary(self):
        token = self.peek()
        if token.type == 'NOT':
            op = self.expect('NOT').value
            operand = self.unary()
            node = UnaryOp(op, operand)
            return node
        elif token.type == 'POINTER':
            self.expect('POINTER')
            var_name = self.expect('ID').value
            return PointerDereference(Variable(var_name))  # Correctly references the new AST node
        else:
            return self.primary()

    def primary(self):
        token = self.peek()
        if token.type == 'NUMBER':
            self.advance()
            return Number(token.value)
        elif token.type == 'STRING':
            self.advance()
            return String(token.value)
        elif token.type == 'BOOLEAN':
            self.advance()
            return Boolean(token.value)
        elif token.type == 'ID':
            node = Variable(self.expect('ID').value)
            while self.peek().type == 'DOT':
                self.expect('DOT')
                attr = self.expect('ID').value
                node = AttributeAccess(node, attr)
            while self.peek().type == 'LPAREN':
                node = self.function_call_with_node(node)
            while self.peek().type == 'LBRACKET':
                self.expect('LBRACKET')
                index = self.expression()
                self.expect('RBRACKET')
                node = ArrayAccess(node, index)
            return node
        elif token.type == 'LBRACKET':
            return self.array_literal()
        elif token.type == 'LPAREN':
            self.expect('LPAREN')
            node = self.expression()
            self.expect('RPAREN')
            return node
        else:
            raise SyntaxError(f'Unexpected token {token.type} at line {token.line} column {token.column}')

    def array_literal(self):
        elements = []
        self.expect('LBRACKET')
        if self.peek().type != 'RBRACKET':
            while True:
                elem = self.expression()
                elements.append(elem)
                if self.peek().type != 'COMMA':
                    break
                self.expect('COMMA')
        self.expect('RBRACKET')
        return ArrayLiteral(elements)  # Correctly references the new AST node

    def function_call_with_node(self, node):
        self.expect('LPAREN')
        args = []
        if self.peek().type != 'RPAREN':
            while True:
                arg = self.expression()
                args.append(arg)
                if self.peek().type != 'COMMA':
                    break
                self.expect('COMMA')
        self.expect('RPAREN')
        return FunctionCall(node, args)

    def variable(self):
        var = self.expect('ID').value
        return Variable(var)