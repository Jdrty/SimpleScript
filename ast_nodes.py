# ast_nodes.py

class ASTNode:
    """Base class for all AST nodes."""
    pass

class Number(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Number({self.value})'

class String(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'String("{self.value}")'

class Boolean(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Boolean({self.value})'

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'Variable("{self.name}")'

class Array(ASTNode):
    def __init__(self, elements):
        self.elements = elements

    def __repr__(self):
        return f'Array({self.elements})'

class AttributeAccess(ASTNode):
    def __init__(self, obj, attribute):
        self.obj = obj
        self.attribute = attribute

    def __repr__(self):
        return f'AttributeAccess({self.obj}, "{self.attribute}")'

class BinaryOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f'BinaryOp({self.left}, "{self.op}", {self.right})'

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f'UnaryOp("{self.op}", {self.operand})'

class VarDeclaration(ASTNode):
    def __init__(self, var_type, name, expr):
        self.var_type = var_type
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f'VarDeclaration(type="{self.var_type}", name="{self.name}", expr={self.expr})'

class PointerDeclaration(ASTNode):
    def __init__(self, var_type, name, expr):
        self.var_type = var_type
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f'PointerDeclaration(type="{self.var_type}", name="{self.name}", expr={self.expr})'

class ImportStatement(ASTNode):
    def __init__(self, module_name):
        self.module_name = module_name

    def __repr__(self):
        return f'ImportStatement(module="{self.module_name}")'

class Assignment(ASTNode):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f'Assignment(name="{self.name}", expr={self.expr})'

class ArrayAssignment(ASTNode):
    def __init__(self, array_name, index_expr, expr):
        self.array_name = array_name
        self.index_expr = index_expr
        self.expr = expr

    def __repr__(self):
        return f'ArrayAssignment(array="{self.array_name}", index={self.index_expr}, expr={self.expr})'

class PrintStatement(ASTNode):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f'PrintStatement(expr={self.expr})'

class IfStatement(ASTNode):
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __repr__(self):
        return f'IfStatement(condition={self.condition}, then={self.then_branch}, else={self.else_branch})'

class WhileStatement(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f'WhileStatement(condition={self.condition}, body={self.body})'

class ForStatement(ASTNode):
    def __init__(self, init, condition, increment, body):
        self.init = init
        self.condition = condition
        self.increment = increment
        self.body = body

    def __repr__(self):
        return f'ForStatement(init={self.init}, condition={self.condition}, increment={self.increment}, body={self.body})'

class FunctionDeclaration(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        return f'FunctionDeclaration(name="{self.name}", params={self.params}, body={self.body})'

class FunctionCall(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return f'FunctionCall(name={self.name}, args={self.args})'

class ReturnStatement(ASTNode):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f'ReturnStatement(expr={self.expr})'

class ArrayAccess(ASTNode):
    def __init__(self, array, index):
        self.array = array
        self.index = index

    def __repr__(self):
        return f'ArrayAccess(array={self.array}, index={self.index})'

class ArrayLiteral(ASTNode):
    def __init__(self, elements):
        self.elements = elements

    def __repr__(self):
        return f'ArrayLiteral(elements={self.elements})'

class PointerDereference(ASTNode):
    def __init__(self, var):
        self.var = var

    def __repr__(self):
        return f'PointerDereference(var={self.var})'

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f'Program(statements={self.statements})'