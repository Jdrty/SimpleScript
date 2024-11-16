# plugins/array_plugin.py

from custom_button import CustomButton
import tkinter as tk  # Import tkinter

def init(gui):
    def array_sum():
        code = gui.code_area.get("1.0", tk.END)
        sum_code = '\nvar integer total = 0;\nfor (var integer i = 0; i < length(array); i = i + 1) {\n    total = total + array[i];\n}\nprint(total);\n'
        gui.code_area.insert(tk.END, sum_code)
        gui.highlight_syntax()

    array_sum_button = CustomButton(
        gui.toolbar_frame,
        text="Sum Array",
        command=array_sum,
        width=100,
        height=30,
        bg_color="#2196F3",
        hover_color="#0b7dda",
        text_color="white",
        corner_radius=15
    )
    array_sum_button.pack(side='left', padx=5)