# linter.py

from lexer import Lexer
from parser import Parser
from tkinter import messagebox

class Linter:
    def __init__(self, gui):
        self.gui = gui
        self.errors = []

    def lint(self, code):
        self.errors.clear()
        lexer = Lexer(code)
        try:
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            parser.parse()
        except SyntaxError as e:
            self.errors.append(str(e))
        self.gui.display_linter_errors(self.errors)