# gui.py

import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from custom_button import CustomButton
import re
import json
from lexer import Lexer
from parser import Parser
from test_runner import TestRunner
from linter import Linter
from profiler import Profiler
from plugin_system import PluginSystem
from debugger import Debugger
from interpreter import Interpreter
from utils import draw_rounded_rect

class SimpleScriptGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SimpleScript Interpreter")
        self.current_file = None

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        main_frame = tk.Frame(root, bg="#0d0d0d")
        main_frame.grid(row=0, column=0, sticky='nsew')

        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        main_frame.rowconfigure(2, weight=3)
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)

        # Notebook for Tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Code Tab
        code_frame = tk.Frame(self.notebook, bg="#0d0d0d")
        self.notebook.add(code_frame, text="Code")

        # Line Numbers
        self.line_numbers = tk.Text(
            code_frame,
            width=4,
            padx=4,
            takefocus=0,
            border=0,
            background="#1a1a1a",
            foreground="#ffffff",
            state='disabled',
            wrap='none',
            font=("Consolas", 12)
        )
        self.line_numbers.pack(side='left', fill='y')

        # Code Scrollbar
        self.code_scrollbar = tk.Scrollbar(code_frame, orient=tk.VERTICAL)
        self.code_scrollbar.pack(side='right', fill='y')

        # Code Area
        self.code_area = tk.Text(
            code_frame,
            wrap=tk.NONE,
            font=("Consolas", 12),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#e60012",
            selectforeground="#ffffff",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            yscrollcommand=self.on_code_area_scroll
        )
        self.code_area.pack(fill='both', expand=True, padx=(0, 10), pady=0)

        # Link Scrollbar to Code Area
        self.code_scrollbar.config(command=self.on_code_area_scrollbar)

        # Output Tab
        output_frame = tk.Frame(self.notebook, bg="#0d0d0d")
        self.notebook.add(output_frame, text="Output")

        self.output_area = tk.Text(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 12),
            state='disabled',
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#e60012",
            selectforeground="#ffffff",
        )
        self.output_area.pack(fill='both', expand=True, padx=10, pady=10)

        # Unit Tests Tab
        tests_frame = tk.Frame(self.notebook, bg="#0d0d0d")
        self.notebook.add(tests_frame, text="Unit Tests")

        self.test_label = tk.Label(tests_frame, text="Unit Tests (JSON Format):", bg="#0d0d0d", fg="white")
        self.test_label.pack(anchor='w', padx=10, pady=(10, 0))

        self.test_text = tk.Text(
            tests_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#e60012",
            selectforeground="#ffffff",
        )
        self.test_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.test_scrollbar = tk.Scrollbar(tests_frame, orient=tk.VERTICAL, command=self.test_text.yview)
        self.test_scrollbar.pack(side='right', fill='y')
        self.test_text.configure(yscrollcommand=self.test_scrollbar.set)

        sample_tests = json.dumps([
            {
                "name": "Addition Test",
                "expression": "add(2, 3)",
                "expected": 5
            },
            {
                "name": "Multiplication Test",
                "expression": "multiply(5, 7)",
                "expected": 35
            }
        ], indent=4)
        self.test_text.insert(tk.END, sample_tests)

        # Bind Events
        self.code_area.bind("<<Modified>>", self.on_text_change)
        self.code_area.bind("<KeyRelease>", self.on_key_release)
        self.code_area.bind("<Return>", self.auto_indent)

        for keysym in ['parenleft', 'braceleft', 'bracketleft', 'quotedbl', 'apostrophe']:
            self.code_area.bind(f"<KeyPress-{keysym}>", self.auto_close_brackets)

        self.code_area.bind("<BackSpace>", self.handle_backspace)

        # Initialize Syntax Highlighting Tags
        self.initialize_tags()

        self.highlighting = False

        # Sample Code (Read from sample_code.ss)
        try:
            with open('sample_code.ss', 'r') as f:
                sample_code = f.read()
        except FileNotFoundError:
            sample_code = "// sample_code.ss not found. Please ensure the file exists in the same directory."

        self.code_area.insert(tk.END, sample_code)
        self.code_area.edit_modified(False)

        self.update_line_numbers()
        self.highlight_syntax()  # Apply syntax highlighting initially

        # Initialize Themes
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "bg": "#0d0d0d",
                "fg": "#ffffff",
                "code_bg": "#1a1a1a",
                "code_fg": "#ffffff",
                "output_bg": "#1a1a1a",
                "output_fg": "#ffffff",
                "button_bg": "#e60012",
                "button_hover": "#ff0000",
                "text_color": "#ffffff",
                "select_bg": "#e60012",
                "select_fg": "#ffffff"
            },
            "light": {
                "bg": "#ffffff",
                "fg": "#000000",
                "code_bg": "#f5f5f5",
                "code_fg": "#000000",
                "output_bg": "#f5f5f5",
                "output_fg": "#000000",
                "button_bg": "#4CAF50",
                "button_hover": "#45a049",
                "text_color": "#000000",
                "select_bg": "#4CAF50",
                "select_fg": "#ffffff"
            }
        }

        # Create Toolbar Frame and Buttons BEFORE applying the theme
        self.toolbar_frame = tk.Frame(main_frame, bg=self.themes[self.current_theme]["bg"])
        self.toolbar_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky='w')

        # Run Button
        self.run_button = CustomButton(
            self.toolbar_frame,
            text="Run",
            command=self.run_code,
            width=80,
            height=30,
            bg_color=self.themes[self.current_theme]["button_bg"],
            hover_color=self.themes[self.current_theme]["button_hover"],
            text_color=self.themes[self.current_theme]["text_color"],
            corner_radius=15
        )
        self.run_button.pack(side='left', padx=5)

        # Run Tests Button
        self.run_tests_button = CustomButton(
            self.toolbar_frame,
            text="Run Tests",
            command=self.run_tests,
            width=100,
            height=30,
            bg_color=self.themes[self.current_theme]["button_bg"],
            hover_color=self.themes[self.current_theme]["button_hover"],
            text_color=self.themes[self.current_theme]["text_color"],
            corner_radius=15
        )
        self.run_tests_button.pack(side='left', padx=5)

        # Clear Output Button
        self.clear_button = CustomButton(
            self.toolbar_frame,
            text="Clear Output",
            command=self.clear_output,
            width=120,
            height=30,
            bg_color=self.themes[self.current_theme]["button_bg"],
            hover_color=self.themes[self.current_theme]["button_hover"],
            text_color=self.themes[self.current_theme]["text_color"],
            corner_radius=15
        )
        self.clear_button.pack(side='left', padx=5)

        # Apply the initial theme AFTER creating buttons
        self.apply_theme(self.current_theme)

        # Initialize Features
        self.linter = Linter(self)
        self.profiler = Profiler(self)

        # Initialize Plugin System AFTER toolbar_frame is defined
        self.plugin_system = PluginSystem(self)
        self.plugin_system.load_plugins()

        self.debugger = Debugger(None, self)  # Placeholder, link with interpreter when running

        # Initialize Modes
        self.current_mode = "Normal"  # Modes: Normal, Debug

        # Create Menu
        self.create_menu()

    # ===========================
    # Scrolling Methods
    # ===========================

    def on_code_area_scrollbar(self, *args):
        """Synchronize the code_area and line_numbers scroll with the scrollbar."""
        self.code_area.yview(*args)
        self.line_numbers.yview(*args)
        self.code_scrollbar.set(*args)

    def on_code_area_scroll(self, *args):
        """Update line_numbers when code_area is scrolled."""
        self.line_numbers.yview_moveto(args[0])
        self.code_scrollbar.set(*args)

    # ===========================
    # Syntax Highlighting
    # ===========================

    def initialize_tags(self):
        """Define tag configurations for syntax highlighting."""
        self.code_area.tag_configure("COMMENT", foreground="#a0a0a0")
        self.code_area.tag_configure("STRING", foreground="#ffdb4d")
        self.code_area.tag_configure("NUMBER", foreground="#ff6666")
        self.code_area.tag_configure("KEYWORD", foreground="#ff0000", font=("Consolas", 12, "bold"))
        self.code_area.tag_configure("BOOLEAN", foreground="#66ccff")
        self.code_area.tag_configure("OPERATOR", foreground="#ffffff")
        self.code_area.tag_configure("FUNCTION", foreground="#99ff66", font=("Consolas", 12, "bold"))
        self.code_area.tag_configure("BRACE", foreground="#ffffff")
        self.code_area.tag_configure("POINTER", foreground="#ff00ff")  # New tag for pointers
        self.code_area.tag_configure("ARRAY", foreground="#00ffff")    # New tag for arrays
        self.code_area.tag_configure("auto_inserted", foreground="#ffffff", background="#1a1a1a")

    def highlight_syntax(self, event=None, initial=False):
        """Trigger syntax highlighting."""
        if self.highlighting:
            return

        self.highlighting = True
        self.code_area.after(100, self._highlight_syntax)

    def _highlight_syntax(self):
        """Apply syntax highlighting to all lines."""
        total_lines = int(self.code_area.index('end-1c').split('.')[0])

        for line in range(1, total_lines + 1):
            line_start = f"{line}.0"
            line_end = f"{line}.end"
            line_text = self.code_area.get(line_start, line_end)

            # Remove existing tags in the line
            for tag in self.code_area.tag_names():
                self.code_area.tag_remove(tag, line_start, line_end)

            # Apply syntax highlighting
            for tag, pattern in {
                'COMMENT': r'//.*?$|/\*[\s\S]*?\*/',
                'STRING': r'"([^"\\]|\\.)*"',
                'NUMBER': r'\b\d+(\.\d+)?\b',
                'KEYWORD': r'\b(var|if|else|while|for|function|return|print|import|pointer)\b',
                'BOOLEAN': r'\b(true|false)\b',
                'FUNCTION': r'\b[A-Za-z_]\w*(?=\s*\()',
                'OPERATOR': r'[+\-*/=<>!]+',
                'BRACE': r'[{}()\[\]]',
                'POINTER': r'\*',
                'ARRAY': r'\[|\]',
            }.items():
                for match in re.finditer(pattern, line_text, re.MULTILINE | re.DOTALL):
                    start = f"{line}.{match.start()}"
                    end = f"{line}.{match.end()}"
                    self.code_area.tag_add(tag, start, end)

        self.highlighting = False

    # ===========================
    # Event Handlers
    # ===========================

    def on_text_change(self, event=None):
        """Handle text changes in the code area."""
        if self.code_area.edit_modified():
            self.update_line_numbers()
            self.highlight_syntax()
            self.linter.lint(self.code_area.get("1.0", tk.END))  # Run linter
            self.code_area.see("insert")  # Ensure cursor is visible
            self.code_area.edit_modified(False)

    def on_key_release(self, event=None):
        """Handle key release events for additional updates."""
        self.update_line_numbers()
        self.highlight_syntax()
        self.linter.lint(self.code_area.get("1.0", tk.END))  # Run linter
        self.code_area.see("insert")  # Ensure cursor is visible

    def auto_indent(self, event):
        """Automatically indent new lines based on previous line."""
        line = self.code_area.index("insert").split(".")[0]
        if int(line) > 1:
            prev_line = str(int(line) - 1)
            prev_text = self.code_area.get(prev_line + ".0", prev_line + ".end")
            indent = re.match(r'^\s*', prev_text).group()
            if prev_text.strip().endswith("{"):
                indent += "    "
        else:
            indent = ""
        self.code_area.insert("insert", "\n" + indent)
        self.code_area.see("insert")  # Ensure cursor is visible
        return "break"

    def auto_close_brackets(self, event):
        """Automatically insert closing brackets."""
        mapping = {
            'parenleft': ('(', ')'),
            'braceleft': ('{', '}'),
            'bracketleft': ('[', ']'),
            'quotedbl': ('"', '"'),
            'apostrophe': ("'", "'"),
        }
        keysym = event.keysym
        if keysym in mapping:
            opening, closing = mapping[keysym]
            self.code_area.insert("insert", opening + closing)
            # Move cursor back between the brackets
            self.code_area.mark_set("insert", "insert-1c")
            # Apply 'auto_inserted' tag only to the closing bracket
            closing_pos = self.code_area.index("insert +1c")
            self.code_area.tag_add("auto_inserted", "insert", closing_pos)
            self.code_area.see("insert")  # Ensure cursor is visible
            return "break"
        return

    def handle_backspace(self, event):
        """Handle backspace to remove auto-inserted closing brackets."""
        cursor_pos = self.code_area.index("insert")
        prev_char_pos = f"{cursor_pos} -1c"
        prev_char = self.code_area.get(prev_char_pos)
        next_char_pos = cursor_pos
        next_char = self.code_area.get(next_char_pos)

        opening_brackets = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}

        if prev_char in opening_brackets:
            expected_closing = opening_brackets[prev_char]
            if next_char == expected_closing:
                # Check if the closing bracket has 'auto_inserted' tag
                tags = self.code_area.tag_names(next_char_pos)
                if 'auto_inserted' in tags:
                    # Delete both opening and closing brackets
                    self.code_area.delete(prev_char_pos, f"{next_char_pos} +1c")
                    return "break"
        return

    # ===========================
    # Line Numbers
    # ===========================

    def update_line_numbers(self, event=None):
        """Update the line numbers in the line_numbers widget without resetting scroll."""
        self.line_numbers.configure(state='normal')
        # Save the current view position
        first, last = self.line_numbers.yview()
        self.line_numbers.delete("1.0", tk.END)
        line_count = int(self.code_area.index('end-1c').split('.')[0])
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert(tk.END, line_numbers_string)
        # Restore the view position
        self.line_numbers.yview_moveto(first)
        self.line_numbers.configure(state='disabled')

    # ===========================
    # Unit Testing Methods
    # ===========================

    def output(self, message):
        """Display a message in the output area."""
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, str(message) + '\n')
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)

    def display_linter_errors(self, errors):
        """Display linter errors in the output area."""
        if errors:
            error_text = "\n".join(errors)
            self.output(f"Linter Errors:\n{error_text}")
        else:
            self.output("No linting errors found.")

    def run_linter(self):
        """Run the linter on the current code."""
        code = self.code_area.get("1.0", tk.END)
        self.linter.lint(code)

    # ===========================
    # Theme Toggle Methods
    # ===========================

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.apply_theme("light")
            self.current_theme = "light"
        else:
            self.apply_theme("dark")
            self.current_theme = "dark"

    def apply_theme(self, theme_name):
        """Apply the selected theme to the GUI."""
        theme = self.themes[theme_name]
        self.root.configure(bg=theme["bg"])

        # Configure ttk.Notebook using ttk.Style
        style = ttk.Style()
        style.theme_use('default')  # Choose an appropriate theme

        # Configure the Notebook background
        style.configure('TNotebook', background=theme["bg"])

        # Configure the Notebook Tabs
        style.configure('TNotebook.Tab', background=theme["button_bg"], foreground=theme["text_color"])

        # Optional: Configure selected tab
        style.map('TNotebook.Tab',
                  background=[('selected', theme["button_hover"])],
                  foreground=[('selected', theme["text_color"])])

        # Configure the code_area and output_area
        self.code_area.configure(
            bg=theme["code_bg"],
            fg=theme["code_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],       # Now defined
            selectforeground=theme["select_fg"]        # Now defined
        )
        self.output_area.configure(
            bg=theme["output_bg"],
            fg=theme["output_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"]
        )
        self.line_numbers.configure(bg=theme["code_bg"], fg=theme["fg"])

        # Update menu colors (if implemented)
        self.update_menu_colors(theme)

        # Update buttons
        for button in [self.run_button, self.run_tests_button, self.clear_button]:
            button.itemconfig(button.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
            button.itemconfig(button.text_id, fill=theme["text_color"])
            button.bg_color = theme["button_bg"]
            button.hover_color = theme["button_hover"]
            button.text_color = theme["text_color"]

        # Update plugin-added buttons if any
        for child in self.toolbar_frame.winfo_children():
            if isinstance(child, CustomButton):
                child.itemconfig(child.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
                child.itemconfig(child.text_id, fill=theme["text_color"])
                child.bg_color = theme["button_bg"]
                child.hover_color = theme["button_hover"]
                child.text_color = theme["text_color"]

    def update_menu_colors(self, theme):
        """Update menu colors. Note: Tkinter does not support dynamic menu color changes directly."""
        # This is a placeholder. Implementing dynamic menu color changes requires more complex handling.
        pass

    # ===========================
    # Menu Creation
    # ===========================

    def create_menu(self):
        style = ttk.Style()
        style.theme_use('default')  # Ensure default theme for consistent styling

        menu = tk.Menu(self.root, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"],
                      activebackground=self.themes[self.current_theme]["button_bg"],
                      activeforeground=self.themes[self.current_theme]["text_color"])
        self.root.config(menu=menu)

        # File Menu
        file_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Run Menu
        run_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                           fg=self.themes[self.current_theme]["fg"],
                           activebackground=self.themes[self.current_theme]["button_bg"],
                           activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run", command=self.run_code)
        run_menu.add_command(label="Run Tests", command=self.run_tests)

        # Debug Menu
        debug_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Debug", menu=debug_menu)
        debug_menu.add_command(label="Step In", command=self.step_in)
        debug_menu.add_command(label="Step Over", command=self.step_over)
        debug_menu.add_command(label="Continue", command=self.continue_execution)

        # Tools Menu
        tools_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Linter", command=self.run_linter)
        tools_menu.add_command(label="Profile Code", command=self.profile_code)

        # Version Control Menu
        vc_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                          fg=self.themes[self.current_theme]["fg"],
                          activebackground=self.themes[self.current_theme]["button_bg"],
                          activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Version Control", menu=vc_menu)
        vc_menu.add_command(label="Commit", command=self.commit_code)
        vc_menu.add_command(label="Push", command=self.push_code)
        vc_menu.add_command(label="Pull", command=self.pull_code)

        # View Menu
        view_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Normal Mode", command=lambda: self.set_mode("Normal"))
        view_menu.add_command(label="Debug Mode", command=lambda: self.set_mode("Debug"))

        # Templates Menu
        templates_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                                  fg=self.themes[self.current_theme]["fg"],
                                  activebackground=self.themes[self.current_theme]["button_bg"],
                                  activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Templates", menu=templates_menu)
        templates_menu.add_command(label="If-Else", command=lambda: self.insert_template("If-Else"))
        templates_menu.add_command(label="Function", command=lambda: self.insert_template("Function"))
        templates_menu.add_command(label="For Loop", command=lambda: self.insert_template("For Loop"))
        templates_menu.add_command(label="While Loop", command=lambda: self.insert_template("While Loop"))

        # Cloud Menu
        cloud_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Cloud", menu=cloud_menu)
        cloud_menu.add_command(label="Save to Dropbox", command=self.save_to_cloud)
        cloud_menu.add_command(label="Load from Dropbox", command=self.load_from_cloud)

        # Help Menu
        help_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    # ===========================
    # Code Execution Methods
    # ===========================

    def run_code(self):
        code = self.code_area.get("1.0", tk.END)
        self.clear_output()

        def output_callback(message):
            self.output(message)

        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter = Interpreter(ast, output_callback=output_callback, profiler=self.profiler)
            self.debugger.interpreter = interpreter  # Link debugger with interpreter
            interpreter.run()
            if self.profiler:
                self.profiler.display_profile()
            # Switch to Output tab automatically
            self.notebook.select(self.notebook.tabs()[1])  # Assuming Output tab is second
        except SyntaxError as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Syntax Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])
        except ImportError as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Import Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])
        except Exception as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])

    def run_tests(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        if current_tab != self.notebook.nametowidget(self.notebook.tabs()[2]):
            self.notebook.select(self.notebook.tabs()[2])  # Switch to Unit Tests tab

        tests_json = self.test_text.get("1.0", tk.END)
        try:
            tests = json.loads(tests_json)
            runner = TestRunner(self.code_area.get("1.0", tk.END), self.output)
            results = runner.run_tests(tests)
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, "\n--- Unit Test Results ---\n")
            for res in results:
                self.output_area.insert(tk.END, res + '\n')
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            # Switch to Output tab automatically
            self.notebook.select(self.notebook.tabs()[1])  # Assuming Output tab is second
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Failed to parse tests: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while running tests: {e}")

    def step_in(self):
        messagebox.showinfo("Debugger", "Step In functionality not yet implemented.")

    def step_over(self):
        messagebox.showinfo("Debugger", "Step Over functionality not yet implemented.")

    def continue_execution(self):
        messagebox.showinfo("Debugger", "Continue functionality not yet implemented.")

    def clear_output(self):
        self.output_area.configure(state='normal')
        self.output_area.delete("1.0", tk.END)
        self.output_area.configure(state='disabled')

    # ===========================
    # Linter Methods
    # ===========================

    def display_linter_errors(self, errors):
        """Display linter errors in the output area."""
        if errors:
            error_text = "\n".join(errors)
            self.output(f"Linter Errors:\n{error_text}")
        else:
            self.output("No linting errors found.")

    # ===========================
    # Theme Toggle Methods
    # ===========================

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.apply_theme("light")
            self.current_theme = "light"
        else:
            self.apply_theme("dark")
            self.current_theme = "dark"

    def apply_theme(self, theme_name):
        """Apply the selected theme to the GUI."""
        theme = self.themes[theme_name]
        self.root.configure(bg=theme["bg"])

        # Configure ttk.Notebook using ttk.Style
        style = ttk.Style()
        style.theme_use('default')  # Choose an appropriate theme

        # Configure the Notebook background
        style.configure('TNotebook', background=theme["bg"])

        # Configure the Notebook Tabs
        style.configure('TNotebook.Tab', background=theme["button_bg"], foreground=theme["text_color"])

        # Optional: Configure selected tab
        style.map('TNotebook.Tab',
                  background=[('selected', theme["button_hover"])],
                  foreground=[('selected', theme["text_color"])])

        # Configure the code_area and output_area
        self.code_area.configure(
            bg=theme["code_bg"],
            fg=theme["code_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],       # Now defined
            selectforeground=theme["select_fg"]        # Now defined
        )
        self.output_area.configure(
            bg=theme["output_bg"],
            fg=theme["output_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"]
        )
        self.line_numbers.configure(bg=theme["code_bg"], fg=theme["fg"])

        # Update menu colors (if implemented)
        self.update_menu_colors(theme)

        # Update buttons
        for button in [self.run_button, self.run_tests_button, self.clear_button]:
            button.itemconfig(button.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
            button.itemconfig(button.text_id, fill=theme["text_color"])
            button.bg_color = theme["button_bg"]
            button.hover_color = theme["button_hover"]
            button.text_color = theme["text_color"]

        # Update plugin-added buttons if any
        for child in self.toolbar_frame.winfo_children():
            if isinstance(child, CustomButton):
                child.itemconfig(child.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
                child.itemconfig(child.text_id, fill=theme["text_color"])
                child.bg_color = theme["button_bg"]
                child.hover_color = theme["button_hover"]
                child.text_color = theme["text_color"]

    def update_menu_colors(self, theme):
        """Update menu colors. Note: Tkinter does not support dynamic menu color changes directly."""
        # This is a placeholder. Implementing dynamic menu color changes requires more complex handling.
        pass

    # ===========================
    # Menu Creation
    # ===========================

    def create_menu(self):
        style = ttk.Style()
        style.theme_use('default')  # Ensure default theme for consistent styling

        menu = tk.Menu(self.root, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"],
                      activebackground=self.themes[self.current_theme]["button_bg"],
                      activeforeground=self.themes[self.current_theme]["text_color"])
        self.root.config(menu=menu)

        # File Menu
        file_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Run Menu
        run_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                           fg=self.themes[self.current_theme]["fg"],
                           activebackground=self.themes[self.current_theme]["button_bg"],
                           activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run", command=self.run_code)
        run_menu.add_command(label="Run Tests", command=self.run_tests)

        # Debug Menu
        debug_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Debug", menu=debug_menu)
        debug_menu.add_command(label="Step In", command=self.step_in)
        debug_menu.add_command(label="Step Over", command=self.step_over)
        debug_menu.add_command(label="Continue", command=self.continue_execution)

        # Tools Menu
        tools_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Linter", command=self.run_linter)
        tools_menu.add_command(label="Profile Code", command=self.profile_code)

        # Version Control Menu
        vc_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                          fg=self.themes[self.current_theme]["fg"],
                          activebackground=self.themes[self.current_theme]["button_bg"],
                          activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Version Control", menu=vc_menu)
        vc_menu.add_command(label="Commit", command=self.commit_code)
        vc_menu.add_command(label="Push", command=self.push_code)
        vc_menu.add_command(label="Pull", command=self.pull_code)

        # View Menu
        view_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Normal Mode", command=lambda: self.set_mode("Normal"))
        view_menu.add_command(label="Debug Mode", command=lambda: self.set_mode("Debug"))

        # Templates Menu
        templates_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                                  fg=self.themes[self.current_theme]["fg"],
                                  activebackground=self.themes[self.current_theme]["button_bg"],
                                  activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Templates", menu=templates_menu)
        templates_menu.add_command(label="If-Else", command=lambda: self.insert_template("If-Else"))
        templates_menu.add_command(label="Function", command=lambda: self.insert_template("Function"))
        templates_menu.add_command(label="For Loop", command=lambda: self.insert_template("For Loop"))
        templates_menu.add_command(label="While Loop", command=lambda: self.insert_template("While Loop"))

        # Cloud Menu
        cloud_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Cloud", menu=cloud_menu)
        cloud_menu.add_command(label="Save to Dropbox", command=self.save_to_cloud)
        cloud_menu.add_command(label="Load from Dropbox", command=self.load_from_cloud)

        # Help Menu
        help_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    # ===========================
    # Code Execution Methods
    # ===========================

    def run_code(self):
        code = self.code_area.get("1.0", tk.END)
        self.clear_output()

        def output_callback(message):
            self.output(message)

        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter = Interpreter(ast, output_callback=output_callback, profiler=self.profiler)
            self.debugger.interpreter = interpreter  # Link debugger with interpreter
            interpreter.run()
            if self.profiler:
                self.profiler.display_profile()
            # Switch to Output tab automatically
            self.notebook.select(self.notebook.tabs()[1])  # Assuming Output tab is second
        except SyntaxError as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Syntax Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])
        except ImportError as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Import Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])
        except Exception as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])

    def run_tests(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        if current_tab != self.notebook.nametowidget(self.notebook.tabs()[2]):
            self.notebook.select(self.notebook.tabs()[2])  # Switch to Unit Tests tab

        tests_json = self.test_text.get("1.0", tk.END)
        try:
            tests = json.loads(tests_json)
            runner = TestRunner(self.code_area.get("1.0", tk.END), self.output)
            results = runner.run_tests(tests)
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, "\n--- Unit Test Results ---\n")
            for res in results:
                self.output_area.insert(tk.END, res + '\n')
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            # Switch to Output tab automatically
            self.notebook.select(self.notebook.tabs()[1])  # Assuming Output tab is second
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Failed to parse tests: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while running tests: {e}")

    def step_in(self):
        messagebox.showinfo("Debugger", "Step In functionality not yet implemented.")

    def step_over(self):
        messagebox.showinfo("Debugger", "Step Over functionality not yet implemented.")

    def continue_execution(self):
        messagebox.showinfo("Debugger", "Continue functionality not yet implemented.")

    def clear_output(self):
        self.output_area.configure(state='normal')
        self.output_area.delete("1.0", tk.END)
        self.output_area.configure(state='disabled')

    # ===========================
    # Linter Methods
    # ===========================

    def display_linter_errors(self, errors):
        """Display linter errors in the output area."""
        if errors:
            error_text = "\n".join(errors)
            self.output(f"Linter Errors:\n{error_text}")
        else:
            self.output("No linting errors found.")

    def run_linter(self):
        """Run the linter on the current code."""
        code = self.code_area.get("1.0", tk.END)
        self.linter.lint(code)

    # ===========================
    # Theme Toggle Methods
    # ===========================

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.apply_theme("light")
            self.current_theme = "light"
        else:
            self.apply_theme("dark")
            self.current_theme = "dark"

    def apply_theme(self, theme_name):
        """Apply the selected theme to the GUI."""
        theme = self.themes[theme_name]
        self.root.configure(bg=theme["bg"])

        # Configure ttk.Notebook using ttk.Style
        style = ttk.Style()
        style.theme_use('default')  # Choose an appropriate theme

        # Configure the Notebook background
        style.configure('TNotebook', background=theme["bg"])

        # Configure the Notebook Tabs
        style.configure('TNotebook.Tab', background=theme["button_bg"], foreground=theme["text_color"])

        # Optional: Configure selected tab
        style.map('TNotebook.Tab',
                  background=[('selected', theme["button_hover"])],
                  foreground=[('selected', theme["text_color"])])

        # Configure the code_area and output_area
        self.code_area.configure(
            bg=theme["code_bg"],
            fg=theme["code_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],       # Now defined
            selectforeground=theme["select_fg"]        # Now defined
        )
        self.output_area.configure(
            bg=theme["output_bg"],
            fg=theme["output_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"]
        )
        self.line_numbers.configure(bg=theme["code_bg"], fg=theme["fg"])

        # Update menu colors (if implemented)
        self.update_menu_colors(theme)

        # Update buttons
        for button in [self.run_button, self.run_tests_button, self.clear_button]:
            button.itemconfig(button.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
            button.itemconfig(button.text_id, fill=theme["text_color"])
            button.bg_color = theme["button_bg"]
            button.hover_color = theme["button_hover"]
            button.text_color = theme["text_color"]

        # Update plugin-added buttons if any
        for child in self.toolbar_frame.winfo_children():
            if isinstance(child, CustomButton):
                child.itemconfig(child.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
                child.itemconfig(child.text_id, fill=theme["text_color"])
                child.bg_color = theme["button_bg"]
                child.hover_color = theme["button_hover"]
                child.text_color = theme["text_color"]

    def update_menu_colors(self, theme):
        """Update menu colors. Note: Tkinter does not support dynamic menu color changes directly."""
        # This is a placeholder. Implementing dynamic menu color changes requires more complex handling.
        pass

    # ===========================
    # Menu Creation
    # ===========================

    def create_menu(self):
        style = ttk.Style()
        style.theme_use('default')  # Ensure default theme for consistent styling

        menu = tk.Menu(self.root, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"],
                      activebackground=self.themes[self.current_theme]["button_bg"],
                      activeforeground=self.themes[self.current_theme]["text_color"])
        self.root.config(menu=menu)

        # File Menu
        file_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Run Menu
        run_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                           fg=self.themes[self.current_theme]["fg"],
                           activebackground=self.themes[self.current_theme]["button_bg"],
                           activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run", command=self.run_code)
        run_menu.add_command(label="Run Tests", command=self.run_tests)

        # Debug Menu
        debug_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Debug", menu=debug_menu)
        debug_menu.add_command(label="Step In", command=self.step_in)
        debug_menu.add_command(label="Step Over", command=self.step_over)
        debug_menu.add_command(label="Continue", command=self.continue_execution)

        # Tools Menu
        tools_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Linter", command=self.run_linter)
        tools_menu.add_command(label="Profile Code", command=self.profile_code)

        # Version Control Menu
        vc_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                          fg=self.themes[self.current_theme]["fg"],
                          activebackground=self.themes[self.current_theme]["button_bg"],
                          activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Version Control", menu=vc_menu)
        vc_menu.add_command(label="Commit", command=self.commit_code)
        vc_menu.add_command(label="Push", command=self.push_code)
        vc_menu.add_command(label="Pull", command=self.pull_code)

        # View Menu
        view_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Normal Mode", command=lambda: self.set_mode("Normal"))
        view_menu.add_command(label="Debug Mode", command=lambda: self.set_mode("Debug"))

        # Templates Menu
        templates_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                                  fg=self.themes[self.current_theme]["fg"],
                                  activebackground=self.themes[self.current_theme]["button_bg"],
                                  activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Templates", menu=templates_menu)
        templates_menu.add_command(label="If-Else", command=lambda: self.insert_template("If-Else"))
        templates_menu.add_command(label="Function", command=lambda: self.insert_template("Function"))
        templates_menu.add_command(label="For Loop", command=lambda: self.insert_template("For Loop"))
        templates_menu.add_command(label="While Loop", command=lambda: self.insert_template("While Loop"))

        # Cloud Menu
        cloud_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Cloud", menu=cloud_menu)
        cloud_menu.add_command(label="Save to Dropbox", command=self.save_to_cloud)
        cloud_menu.add_command(label="Load from Dropbox", command=self.load_from_cloud)

        # Help Menu
        help_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    # ===========================
    # Code Execution Methods
    # ===========================

    def run_code(self):
        code = self.code_area.get("1.0", tk.END)
        self.clear_output()

        def output_callback(message):
            self.output(message)

        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter = Interpreter(ast, output_callback=output_callback, profiler=self.profiler)
            self.debugger.interpreter = interpreter  # Link debugger with interpreter
            interpreter.run()
            if self.profiler:
                self.profiler.display_profile()
            # Switch to Output tab automatically
            self.notebook.select(self.notebook.tabs()[1])  # Assuming Output tab is second
        except SyntaxError as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Syntax Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])
        except ImportError as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Import Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])
        except Exception as e:
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, f"Error: {e}\n")
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            self.notebook.select(self.notebook.tabs()[1])

    def run_tests(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        if current_tab != self.notebook.nametowidget(self.notebook.tabs()[2]):
            self.notebook.select(self.notebook.tabs()[2])  # Switch to Unit Tests tab

        tests_json = self.test_text.get("1.0", tk.END)
        try:
            tests = json.loads(tests_json)
            runner = TestRunner(self.code_area.get("1.0", tk.END), self.output)
            results = runner.run_tests(tests)
            self.output_area.configure(state='normal')
            self.output_area.insert(tk.END, "\n--- Unit Test Results ---\n")
            for res in results:
                self.output_area.insert(tk.END, res + '\n')
            self.output_area.configure(state='disabled')
            self.output_area.see(tk.END)
            # Switch to Output tab automatically
            self.notebook.select(self.notebook.tabs()[1])  # Assuming Output tab is second
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Failed to parse tests: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while running tests: {e}")

    def step_in(self):
        messagebox.showinfo("Debugger", "Step In functionality not yet implemented.")

    def step_over(self):
        messagebox.showinfo("Debugger", "Step Over functionality not yet implemented.")

    def continue_execution(self):
        messagebox.showinfo("Debugger", "Continue functionality not yet implemented.")

    def clear_output(self):
        self.output_area.configure(state='normal')
        self.output_area.delete("1.0", tk.END)
        self.output_area.configure(state='disabled')

    # ===========================
    # Linter Methods
    # ===========================

    def display_linter_errors(self, errors):
        """Display linter errors in the output area."""
        if errors:
            error_text = "\n".join(errors)
            self.output(f"Linter Errors:\n{error_text}")
        else:
            self.output("No linting errors found.")

    def run_linter(self):
        """Run the linter on the current code."""
        code = self.code_area.get("1.0", tk.END)
        self.linter.lint(code)

    # ===========================
    # Theme Toggle Methods
    # ===========================

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.apply_theme("light")
            self.current_theme = "light"
        else:
            self.apply_theme("dark")
            self.current_theme = "dark"

    def apply_theme(self, theme_name):
        """Apply the selected theme to the GUI."""
        theme = self.themes[theme_name]
        self.root.configure(bg=theme["bg"])

        # Configure ttk.Notebook using ttk.Style
        style = ttk.Style()
        style.theme_use('default')  # Choose an appropriate theme

        # Configure the Notebook background
        style.configure('TNotebook', background=theme["bg"])

        # Configure the Notebook Tabs
        style.configure('TNotebook.Tab', background=theme["button_bg"], foreground=theme["text_color"])

        # Optional: Configure selected tab
        style.map('TNotebook.Tab',
                  background=[('selected', theme["button_hover"])],
                  foreground=[('selected', theme["text_color"])])

        # Configure the code_area and output_area
        self.code_area.configure(
            bg=theme["code_bg"],
            fg=theme["code_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],       # Now defined
            selectforeground=theme["select_fg"]        # Now defined
        )
        self.output_area.configure(
            bg=theme["output_bg"],
            fg=theme["output_fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"]
        )
        self.line_numbers.configure(bg=theme["code_bg"], fg=theme["fg"])

        # Update menu colors (if implemented)
        self.update_menu_colors(theme)

        # Update buttons
        for button in [self.run_button, self.run_tests_button, self.clear_button]:
            button.itemconfig(button.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
            button.itemconfig(button.text_id, fill=theme["text_color"])
            button.bg_color = theme["button_bg"]
            button.hover_color = theme["button_hover"]
            button.text_color = theme["text_color"]

        # Update plugin-added buttons if any
        for child in self.toolbar_frame.winfo_children():
            if isinstance(child, CustomButton):
                child.itemconfig(child.rounded_rect, fill=theme["button_bg"], outline=theme["button_bg"])
                child.itemconfig(child.text_id, fill=theme["text_color"])
                child.bg_color = theme["button_bg"]
                child.hover_color = theme["button_hover"]
                child.text_color = theme["text_color"]

    def update_menu_colors(self, theme):
        """Update menu colors. Note: Tkinter does not support dynamic menu color changes directly."""
        # This is a placeholder. Implementing dynamic menu color changes requires more complex handling.
        pass

    # ===========================
    # Menu Creation
    # ===========================

    def create_menu(self):
        style = ttk.Style()
        style.theme_use('default')  # Ensure default theme for consistent styling

        menu = tk.Menu(self.root, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"],
                      activebackground=self.themes[self.current_theme]["button_bg"],
                      activeforeground=self.themes[self.current_theme]["text_color"])
        self.root.config(menu=menu)

        # File Menu
        file_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Run Menu
        run_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                           fg=self.themes[self.current_theme]["fg"],
                           activebackground=self.themes[self.current_theme]["button_bg"],
                           activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run", command=self.run_code)
        run_menu.add_command(label="Run Tests", command=self.run_tests)

        # Debug Menu
        debug_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Debug", menu=debug_menu)
        debug_menu.add_command(label="Step In", command=self.step_in)
        debug_menu.add_command(label="Step Over", command=self.step_over)
        debug_menu.add_command(label="Continue", command=self.continue_execution)

        # Tools Menu
        tools_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Linter", command=self.run_linter)
        tools_menu.add_command(label="Profile Code", command=self.profile_code)

        # Version Control Menu
        vc_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                          fg=self.themes[self.current_theme]["fg"],
                          activebackground=self.themes[self.current_theme]["button_bg"],
                          activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Version Control", menu=vc_menu)
        vc_menu.add_command(label="Commit", command=self.commit_code)
        vc_menu.add_command(label="Push", command=self.push_code)
        vc_menu.add_command(label="Pull", command=self.pull_code)

        # View Menu
        view_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Normal Mode", command=lambda: self.set_mode("Normal"))
        view_menu.add_command(label="Debug Mode", command=lambda: self.set_mode("Debug"))

        # Templates Menu
        templates_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                                  fg=self.themes[self.current_theme]["fg"],
                                  activebackground=self.themes[self.current_theme]["button_bg"],
                                  activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Templates", menu=templates_menu)
        templates_menu.add_command(label="If-Else", command=lambda: self.insert_template("If-Else"))
        templates_menu.add_command(label="Function", command=lambda: self.insert_template("Function"))
        templates_menu.add_command(label="For Loop", command=lambda: self.insert_template("For Loop"))
        templates_menu.add_command(label="While Loop", command=lambda: self.insert_template("While Loop"))

        # Cloud Menu
        cloud_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             activebackground=self.themes[self.current_theme]["button_bg"],
                             activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Cloud", menu=cloud_menu)
        cloud_menu.add_command(label="Save to Dropbox", command=self.save_to_cloud)
        cloud_menu.add_command(label="Load from Dropbox", command=self.load_from_cloud)

        # Help Menu
        help_menu = tk.Menu(menu, tearoff=0, bg=self.themes[self.current_theme]["bg"],
                            fg=self.themes[self.current_theme]["fg"],
                            activebackground=self.themes[self.current_theme]["button_bg"],
                            activeforeground=self.themes[self.current_theme]["text_color"])
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    # ===========================
    # File Operations
    # ===========================

    def open_file(self):
        """Open a file and load its content into the code area."""
        file_path = filedialog.askopenfilename(filetypes=[("SimpleScript Files", "*.ss"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    code = file.read()
                self.code_area.delete("1.0", tk.END)
                self.code_area.insert(tk.END, code)
                self.current_file = file_path
                self.highlight_syntax()
                self.update_line_numbers()
                self.code_area.see("end")  # Scroll to the end after opening a file
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_file(self):
        """Save the current code to the existing file."""
        if self.current_file:
            try:
                with open(self.current_file, 'w') as file:
                    code = self.code_area.get("1.0", tk.END)
                    file.write(code)
                messagebox.showinfo("Success", "File saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
        else:
            self.save_as_file()

    def save_as_file(self):
        """Save the current code to a new file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".ss", filetypes=[("SimpleScript Files", "*.ss"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    code = self.code_area.get("1.0", tk.END)
                    file.write(code)
                self.current_file = file_path
                messagebox.showinfo("Success", "File saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    # ===========================
    # Documentation
    # ===========================

    def show_documentation(self):
        """Display the documentation in a new window."""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x400")
        doc_window.configure(bg="#0d0d0d")

        doc_text = tk.Text(
            doc_window,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#e60012",
            selectforeground="#ffffff",
        )
        doc_text.pack(expand=True, fill='both')

        documentation = """
SimpleScript Documentation

Keywords:
- var: Variable declaration
- if, else: Conditional statements
- while, for: Loops
- function: Function declaration
- return: Return statement
- print: Output
- import: Import modules
- pointer: Pointer declaration

Operators:
- Arithmetic: +, -, *, /
- Comparison: ==, !=, >, <, >=, <=
- Logical: AND, OR, NOT

Functions:
- Define using 'function' keyword
- Call functions with arguments

Examples:
1. Variable Declaration:
   var integer x = 10;

2. Pointer Declaration:
   *integer ptr = x;

3. If-Else Statement:
   if (x > 5) {
       print("x is greater than 5");
   } else {
       print("x is 5 or less");
   }

4. Function:
   function add(a, b) {
       return a + b;
   }
   var integer sum = add(3, 4);
   print(sum);

5. Using Pointers:
   var integer y = 20;
   *integer ptr = y;
   print(ptr);    // Prints {'pointer': 'y'}
   print(*ptr);   // Prints 20

6. Importing Modules:
   import "math";
   var float sqrt_val = math.sqrt(16);
   print(sqrt_val);
"""

        doc_text.insert(tk.END, documentation)
        doc_text.configure(state='disabled')

    # ===========================
    # Performance Profiling Methods
    # ===========================

    def profile_code(self):
        """Profile the performance of the current code."""
        self.profiler.execution_times.clear()
        self.run_code()

    def display_profiler_results(self, profile_data):
        """Display profiler results in the output area."""
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, "\n--- Performance Profiling ---\n")
        self.output_area.insert(tk.END, profile_data + '\n')
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)

    # ===========================
    # Version Control Methods
    # ===========================

    def commit_code(self):
        """Commit the current file to Git."""
        if not hasattr(self, 'git'):
            try:
                import git
                self.git = git
            except ImportError:
                messagebox.showerror("Error", "GitPython is not installed.")
                return
        if not self.current_file:
            messagebox.showerror("Error", "Please save the file before committing.")
            return
        repo_path = os.path.dirname(self.current_file)
        try:
            repo = self.git.Repo(repo_path)
        except self.git.exc.InvalidGitRepositoryError:
            repo = self.git.Repo.init(repo_path)
        try:
            repo.index.add([os.path.basename(self.current_file)])
            commit_message = simpledialog.askstring("Commit Message", "Enter commit message:")
            if commit_message:
                repo.index.commit(commit_message)
                messagebox.showinfo("Success", "Commit successful.")
            else:
                messagebox.showwarning("Cancelled", "Commit cancelled.")
        except Exception as e:
            messagebox.showerror("Error", f"Commit failed: {e}")

    def push_code(self):
        """Push commits to the remote repository."""
        if not hasattr(self, 'git'):
            try:
                import git
                self.git = git
            except ImportError:
                messagebox.showerror("Error", "GitPython is not installed.")
                return

        try:
            repo = self.git.Repo(os.getcwd())
            origin = repo.remote(name='origin')
            origin.push()
            messagebox.showinfo("Success", "Push successful.")
        except Exception as e:
            messagebox.showerror("Error", f"Push failed: {e}")

    def pull_code(self):
        """Pull commits from the remote repository."""
        if not hasattr(self, 'git'):
            try:
                import git
                self.git = git
            except ImportError:
                messagebox.showerror("Error", "GitPython is not installed.")
                return

        try:
            repo = self.git.Repo(os.getcwd())
            origin = repo.remote(name='origin')
            origin.pull()
            messagebox.showinfo("Success", "Pull successful.")
            # Reload the current file after pulling
            if self.current_file:
                with open(self.current_file, 'r') as file:
                    code = file.read()
                self.code_area.delete("1.0", tk.END)
                self.code_area.insert(tk.END, code)
                self.highlight_syntax()
                self.update_line_numbers()
        except Exception as e:
            messagebox.showerror("Error", f"Pull failed: {e}")

    # ===========================
    # Cloud Integration Methods
    # ===========================

    def save_to_cloud(self):
        """Save the current file to Dropbox."""
        if not hasattr(self, 'dropbox'):
            try:
                import dropbox
                self.dropbox = dropbox
            except ImportError:
                messagebox.showerror("Error", "Dropbox SDK is not installed.")
                return
        if not self.current_file:
            messagebox.showwarning("Warning", "No file is currently open to save.")
            return
        access_token = simpledialog.askstring("Dropbox Access Token", "Enter your Dropbox access token:")
        if not access_token:
            messagebox.showwarning("Cancelled", "Save to cloud cancelled.")
            return
        dbx = self.dropbox.Dropbox(access_token)
        file_path = self.current_file
        try:
            with open(file_path, 'rb') as f:
                dbx.files_upload(f.read(), f'/{os.path.basename(file_path)}', mode=self.dropbox.files.WriteMode.overwrite)
            messagebox.showinfo("Success", "File saved to Dropbox successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to Dropbox: {e}")

    def load_from_cloud(self):
        """Load a file from Dropbox."""
        if not hasattr(self, 'dropbox'):
            try:
                import dropbox
                self.dropbox = dropbox
            except ImportError:
                messagebox.showerror("Error", "Dropbox SDK is not installed.")
                return
        access_token = simpledialog.askstring("Dropbox Access Token", "Enter your Dropbox access token:")
        if not access_token:
            messagebox.showwarning("Cancelled", "Load from cloud cancelled.")
            return
        dbx = self.dropbox.Dropbox(access_token)
        try:
            files = dbx.files_list_folder('').entries
            filenames = [file.name for file in files if isinstance(file, self.dropbox.files.FileMetadata)]
            if not filenames:
                messagebox.showinfo("No Files", "No files found in Dropbox.")
                return
            selected = simpledialog.askstring("Select File", f"Available files:\n" + "\n".join(filenames) + "\n\nEnter filename to load:")
            if selected not in filenames:
                messagebox.showerror("Error", "File not found in Dropbox.")
                return
            metadata, res = dbx.files_download(f'/{selected}')
            content = res.content.decode('utf-8')
            self.code_area.delete("1.0", tk.END)
            self.code_area.insert(tk.END, content)
            self.highlight_syntax()
            self.update_line_numbers()
            self.output("Loaded file from Dropbox.")
            # Switch to Code tab after loading
            self.notebook.select(self.notebook.tabs()[0])
            self.current_file = selected  # Update current_file
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load from Dropbox: {e}")

    # ===========================
    # Debugger Methods
    # ===========================

    def highlight_line(self, line):
        """Highlight the specified line number."""
        # Remove existing highlights
        self.code_area.tag_remove("current_line", "1.0", tk.END)
        # Add highlight to the current line
        self.code_area.tag_configure("current_line", background="#333333")
        self.code_area.tag_add("current_line", f"{line}.0", f"{line}.end")

    def add_breakpoint(self, line):
        """Add a breakpoint indicator to the specified line number."""
        # Implementation depends on how line numbers are displayed
        # Placeholder: Show a red dot or similar indicator
        pass  # To be implemented

    def remove_breakpoint(self, line):
        """Remove a breakpoint indicator from the specified line number."""
        # Implementation depends on how line numbers are displayed
        pass  # To be implemented

    def pause_execution(self):
        """Pause the execution of the interpreter."""
        # Placeholder for pausing execution
        pass

    # ===========================
    # Modes Management
    # ===========================

    def set_mode(self, mode):
        """Set the current mode and update the GUI accordingly."""
        self.current_mode = mode
        if mode == "Normal":
            # Hide debug tools
            self.hide_debug_tools()
        elif mode == "Debug":
            # Show debug tools
            self.show_debug_tools()

    def show_debug_tools(self):
        """Display debug-specific tools."""
        # For example, show Step In, Step Over, Continue buttons
        # You can add these buttons to the toolbar_frame or create a separate debug toolbar
        if not hasattr(self, 'debug_buttons'):
            self.debug_buttons = []
            # Step In Button
            step_in_button = CustomButton(
                self.toolbar_frame,
                text="Step In",
                command=self.step_in,
                width=80,
                height=30,
                bg_color="#2196F3",
                hover_color="#0b7dda",
                text_color="white",
                corner_radius=15
            )
            step_in_button.pack(side='left', padx=5)
            self.debug_buttons.append(step_in_button)
            # Step Over Button
            step_over_button = CustomButton(
                self.toolbar_frame,
                text="Step Over",
                command=self.step_over,
                width=100,
                height=30,
                bg_color="#2196F3",
                hover_color="#0b7dda",
                text_color="white",
                corner_radius=15
            )
            step_over_button.pack(side='left', padx=5)
            self.debug_buttons.append(step_over_button)
            # Continue Button
            continue_button = CustomButton(
                self.toolbar_frame,
                text="Continue",
                command=self.continue_execution,
                width=120,
                height=30,
                bg_color="#2196F3",
                hover_color="#0b7dda",
                text_color="white",
                corner_radius=15
            )
            continue_button.pack(side='left', padx=5)
            self.debug_buttons.append(continue_button)

    def hide_debug_tools(self):
        """Hide debug-specific tools."""
        if hasattr(self, 'debug_buttons'):
            for btn in self.debug_buttons:
                btn.pack_forget()
            self.debug_buttons = []

    # ===========================
    # Plugin System Integration
    # ===========================

    # Plugins can add functionalities to the GUI by accessing self.toolbar_frame
    # Ensure that plugins are loaded after all necessary GUI components are initialized

    # ===========================
    # Templates Management
    # ===========================

    def insert_template(self, selection):
        """Insert code templates based on user selection."""
        templates = {
            "If-Else": {
                "code": '''if (condition) {
    // code
} else {
    // code
}''',
                "dependencies": ""
            },
            "Function": {
                "code": '''function functionName(params) {
    // code
}''',
                "dependencies": ""
            },
            "For Loop": {
                "code": '''for (var integer i = 0; i < limit; i = i + 1) {
    // code
}''',
                "dependencies": ""
            },
            "While Loop": {
                "code": '''while (condition) {
    // code
}''',
                "dependencies": ""
            }
        }

        template = templates.get(selection, None)
        if template:
            # Insert dependencies first if any
            if template["dependencies"]:
                self.code_area.insert("insert", template["dependencies"] + "\n")
            # Insert the template code
            self.code_area.insert("insert", template["code"] + "\n")
            self.highlight_syntax()
            self.update_line_numbers()
        else:
            messagebox.showwarning("Template Not Found", f"No template found for {selection}.")