# test_runner.py

from interpreter import Interpreter
from lexer import Lexer
from parser import Parser
import json

class TestRunner:
    def __init__(self, code, output_callback):
        self.code = code
        self.output_callback = output_callback

    def output(self, message):
        """Handle output by using the provided callback."""
        if self.output_callback:
            self.output_callback(message)

    def run_tests(self, tests):
        results = []
        for test in tests:
            lexer = Lexer(self.code)
            try:
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
                interpreter = Interpreter(ast, output_callback=self.output_callback, profiler=None, debugger=None)
                
                # Create a dummy print function to capture output
                def dummy_print(*args):
                    # For simplicity, join args with space
                    interpreter.current_env.define("test_output", ' '.join(map(str, args)))
                
                # Bind the dummy print function to the interpreter's environment
                interpreter.current_env.define("print", dummy_print)
                
                # Evaluate the expression in the test
                expression = test["expression"]
                
                # Tokenize and parse the expression
                lexer_test = Lexer(expression)
                tokens_test = lexer_test.tokenize()
                parser_test = Parser(tokens_test)
                ast_test = parser_test.parse()
                
                # Execute the expression
                for stmt in ast_test.statements:
                    interpreter.execute(stmt)
                
                # Retrieve the output
                result = interpreter.current_env.get('test_output')
                
                # Compare the result with the expected value
                passed = result == str(test["expected"])
                if passed:
                    results.append(f"Test '{test['name']}': Passed")
                else:
                    results.append(f"Test '{test['name']}': Failed - Expected {test['expected']}, got {result}")
            except Exception as e:
                results.append(f"Test '{test['name']}': Failed - {e}")
        return results