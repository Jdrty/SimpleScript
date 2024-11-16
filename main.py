# main.py

import tkinter as tk
from gui import SimpleScriptGUI
from tkinter import messagebox

def main():
    root = tk.Tk()
    app = SimpleScriptGUI(root)
    root.geometry("1200x800")
    root.configure(bg=app.themes[app.current_theme]["bg"])

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r') as file:
                code = file.read()
            app.code_area.delete("1.0", tk.END)
            app.code_area.insert(tk.END, code)
            app.current_file = file_path
            app.highlight_syntax()
            app.update_line_numbers()
            app.code_area.see("end")  # Scroll to the end after opening a file
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

    root.mainloop()

if __name__ == '__main__':
    import sys
    main()