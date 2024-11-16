# debugger.py

import queue

class Debugger:
    def __init__(self, interpreter, gui):
        self.interpreter = interpreter
        self.gui = gui
        self.breakpoints = set()
        self.current_line = None
        self.paused = False
        self.step_mode = False
        self.step_over_mode = False
        self.continue_mode = False
        self.execution_queue = queue.Queue()

    def toggle_breakpoint(self, line):
        if line in self.breakpoints:
            self.breakpoints.remove(line)
            self.gui.remove_breakpoint(line)
        else:
            self.breakpoints.add(line)
            self.gui.add_breakpoint(line)

    def check_breakpoint(self, node):
        if self.paused:
            self.paused = False
            self.gui.pause_execution()
            return
        # Placeholder: Implement line tracking if AST nodes have line information
        # For simplicity, this example does not track lines
        # You can extend AST nodes to include line information

    def before_function_call(self, func, args):
        pass  # Placeholder for potential future use

    def output(self, message):
        self.interpreter.output(message)