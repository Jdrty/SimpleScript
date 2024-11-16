# interpreter.py

import importlib
import time
from ast_nodes import *
from lexer import Lexer
from parser import Parser
from debugger import Debugger
from profiler import Profiler

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        if name in self.vars:
            raise NameError(f"Variable '{name}' already defined.")
        self.vars[name] = value

    def set(self, name, value):
        if name in self.vars:
            self.vars[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise NameError(f"Variable '{name}' is not defined.")

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise NameError(f"Variable '{name}' is not defined.")

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class UserFunction:
    def __init__(self, declaration, interpreter):
        self.declaration = declaration
        self.interpreter = interpreter

    def __call__(self, *args):
        if len(args) != len(self.declaration.params):
            raise TypeError(f"Function '{self.declaration.name}' expects {len(self.declaration.params)} arguments, got {len(args)}.")
        # Create a new environment for the function
        new_env = Environment(parent=self.interpreter.current_env)
        # Bind parameters
        for param, arg in zip(self.declaration.params, args):
            new_env.define(param, arg)
        # Save current environment
        previous_env = self.interpreter.current_env
        self.interpreter.current_env = new_env
        try:
            for stmt in self.declaration.body:
                self.interpreter.execute(stmt)
        except ReturnException as ret:
            # Restore previous environment
            self.interpreter.current_env = previous_env
            return ret.value
        # Restore previous environment
        self.interpreter.current_env = previous_env
        return None

class Interpreter:
    def __init__(self, ast, output_callback=None, profiler=None, debugger=None):
        self.ast = ast
        self.global_env = Environment()
        self.current_env = self.global_env
        self.output_callback = output_callback
        self.profiler = profiler
        self.debugger = debugger
        self.outputs = []  # Store outputs for testing

        # Initialize built-in functions
        self.global_env.define("print", self.builtin_print)
        self.global_env.define("length", self.builtin_length)
        self.global_env.define("push", self.builtin_push)
        self.global_env.define("pop", self.builtin_pop)

    def run(self):
        try:
            for stmt in self.ast.statements:
                self.execute(stmt)
        except ReturnException as ret:
            self.output(f"Runtime error: 'return' outside of function with value {ret.value}")
        except Exception as e:
            self.output(f'Runtime error: {e}')

    def execute(self, node):
        if self.debugger:
            self.debugger.check_breakpoint(node)
        if isinstance(node, VarDeclaration):
            value = self.evaluate(node.expr)
            self.current_env.define(node.name, value)
        elif isinstance(node, PointerDeclaration):
            # Assuming 'expr' is a Variable node indicating which variable to point to
            # The pointer itself stores the name of the variable it points to
            referenced_var_name = self.get_variable_name(node.expr)
            if not referenced_var_name:
                raise TypeError("Pointer must point to a variable name.")
            if not self.is_variable_defined(referenced_var_name):
                raise NameError(f"Variable '{referenced_var_name}' does not exist to be pointed to.")
            self.current_env.define(node.name, {"pointer": referenced_var_name})
        elif isinstance(node, ImportStatement):
            self.handle_import(node)
        elif isinstance(node, Assignment):
            value = self.evaluate(node.expr)
            self.current_env.set(node.name, value)
        elif isinstance(node, ArrayAssignment):
            array = self.current_env.get(node.array_name)
            index = self.evaluate(node.index_expr)
            value = self.evaluate(node.expr)
            if not isinstance(array, list):
                raise TypeError(f"Variable '{node.array_name}' is not an array.")
            if not isinstance(index, int):
                raise TypeError("Array index must be an integer.")
            if index < 0 or index >= len(array):
                raise IndexError("Array index out of bounds.")
            array[index] = value
            self.current_env.set(node.array_name, array)
        elif isinstance(node, PrintStatement):
            value = self.evaluate(node.expr)
            self.output(value)
        elif isinstance(node, IfStatement):
            condition = self.evaluate(node.condition)
            if condition:
                for stmt in node.then_branch:
                    self.execute(stmt)
            elif node.else_branch:
                for stmt in node.else_branch:
                    self.execute(stmt)
        elif isinstance(node, WhileStatement):
            while self.evaluate(node.condition):
                for stmt in node.body:
                    self.execute(stmt)
        elif isinstance(node, ForStatement):
            # Create a new environment for the loop
            loop_env = Environment(parent=self.current_env)
            previous_env = self.current_env
            self.current_env = loop_env
            try:
                self.execute(node.init)
                while self.evaluate(node.condition):
                    for stmt in node.body:
                        self.execute(stmt)
                    self.execute(node.increment)
            finally:
                self.current_env = previous_env
        elif isinstance(node, FunctionDeclaration):
            func = UserFunction(node, self)
            self.current_env.define(node.name, func)
        elif isinstance(node, FunctionCall):
            self.evaluate(node)
        elif isinstance(node, ReturnStatement):
            value = self.evaluate(node.expr)
            raise ReturnException(value)
        elif isinstance(node, ArrayAccess):
            # Handle standalone array access if necessary
            self.evaluate(node)
        elif isinstance(node, PointerDereference):
            # Handle dereferencing
            pointer_ref = self.evaluate(node.var)
            if not isinstance(pointer_ref, dict) or "pointer" not in pointer_ref:
                raise TypeError(f"Variable '{node.var.name}' is not a valid pointer.")
            referenced_var_name = pointer_ref["pointer"]
            return self.current_env.get(referenced_var_name)
        else:
            raise RuntimeError(f'Unknown node type: {type(node)}')

    def handle_import(self, node):
        module_name = node.module_name
        try:
            module = importlib.import_module(module_name)
            self.current_env.define(module_name, module)
            self.output(f"Imported module '{module_name}' successfully.")
        except ImportError:
            raise ImportError(f"Module '{module_name}' not found.")

    def evaluate(self, node):
        if isinstance(node, Number):
            return node.value
        elif isinstance(node, String):
            return node.value
        elif isinstance(node, Boolean):
            return node.value
        elif isinstance(node, Variable):
            return self.current_env.get(node.name)
        elif isinstance(node, Array):
            return [self.evaluate(elem) for elem in node.elements]
        elif isinstance(node, ArrayAccess):
            array = self.evaluate(node.array)
            index = self.evaluate(node.index)
            if not isinstance(array, list):
                raise TypeError(f"Variable '{node.array.name}' is not an array.")
            if not isinstance(index, int):
                raise TypeError("Array index must be an integer.")
            if index < 0 or index >= len(array):
                raise IndexError("Array index out of bounds.")
            return array[index]
        elif isinstance(node, AttributeAccess):
            obj = self.evaluate(node.obj)
            if hasattr(obj, node.attribute):
                return getattr(obj, node.attribute)
            else:
                raise AttributeError(f"Object '{obj}' has no attribute '{node.attribute}'.")
        elif isinstance(node, BinaryOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if self.profiler:
                start_time = time.time()
            if node.op == '+':
                if isinstance(left, str) or isinstance(right, str):
                    result = str(left) + str(right)
                elif isinstance(left, list) and isinstance(right, list):
                    result = left + right
                else:
                    result = left + right
            elif node.op == '-':
                result = left - right
            elif node.op == '*':
                if isinstance(left, str) and isinstance(right, int):
                    result = left * right
                elif isinstance(right, str) and isinstance(left, int):
                    result = right * left
                else:
                    result = left * right
            elif node.op == '/':
                if right == 0:
                    raise ZeroDivisionError("Division by zero.")
                result = left / right
            elif node.op == '==':
                result = left == right
            elif node.op == '!=':
                result = left != right
            elif node.op == '>':
                result = left > right
            elif node.op == '<':
                result = left < right
            elif node.op == '>=':
                result = left >= right
            elif node.op == '<=':
                result = left <= right
            elif node.op.upper() == 'AND':
                result = left and right
            elif node.op.upper() == 'OR':
                result = left or right
            elif node.op.upper() == 'NOT':
                result = not right
            else:
                raise RuntimeError(f'Unknown operator: {node.op}')
            if self.profiler:
                end_time = time.time()
                self.profiler.profile(node.op, end_time - start_time)
            return result
        elif isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand)
            if node.op.upper() == 'NOT':
                return not operand
            else:
                raise RuntimeError(f'Unknown unary operator: {node.op}')
        elif isinstance(node, FunctionCall):
            return self.call_function(node)
        elif isinstance(node, PointerDereference):
            pointer_ref = self.evaluate(node.var)
            if not isinstance(pointer_ref, dict) or "pointer" not in pointer_ref:
                raise TypeError(f"Variable '{node.var.name}' is not a valid pointer.")
            referenced_var_name = pointer_ref["pointer"]
            return self.current_env.get(referenced_var_name)
        elif isinstance(node, ArrayLiteral):
            return [self.evaluate(elem) for elem in node.elements]
        else:
            raise RuntimeError(f'Unknown node type: {type(node)}')

    def call_function(self, node):
        func = self.evaluate(node.name)
        if callable(func):
            args = [self.evaluate(arg) for arg in node.args]
            try:
                if self.debugger:
                    self.debugger.before_function_call(func, args)
                return func(*args)
            except Exception as e:
                raise RuntimeError(f"Error calling function '{node.name.name}': {e}")
        else:
            raise TypeError(f"'{node.name.name}' is not callable.")

    def builtin_print(self, *args):
        message = ' '.join(str(arg) for arg in args)
        self.output(message)

    def builtin_length(self, array):
        if not isinstance(array, list):
            raise TypeError("Argument to 'length' must be an array.")
        return len(array)

    def builtin_push(self, array, value):
        if not isinstance(array, list):
            raise TypeError("First argument to 'push' must be an array.")
        array.append(value)
        return array

    def builtin_pop(self, array):
        if not isinstance(array, list):
            raise TypeError("Argument to 'pop' must be an array.")
        if not array:
            raise IndexError("Cannot pop from an empty array.")
        return array.pop()

    def output(self, message):
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message)

    def get_variable_name(self, expr):
        if isinstance(expr, Variable):
            return expr.name
        elif isinstance(expr, AttributeAccess):
            # Could extend to handle object attributes
            return expr.attribute
        else:
            return None

    def is_variable_defined(self, name):
        try:
            self.current_env.get(name)
            return True
        except NameError:
            return False