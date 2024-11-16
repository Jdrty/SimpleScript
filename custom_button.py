# custom_button.py

import tkinter as tk
from utils import draw_rounded_rect

class CustomButton(tk.Canvas):
    def __init__(self, parent, text, command, width=100, height=40, bg_color="#e60012", hover_color="#ff0000",
                 text_color="white", corner_radius=20, *args, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent['bg'], *args, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.width = width
        self.height = height
        self.text_content = text  # Store text separately to prevent issues during animation

        self.rounded_rect = draw_rounded_rect(
            self,
            0, 0, width, height,
            radius=corner_radius,
            fill=bg_color,
            outline=bg_color
        )

        self.text_id = self.create_text(
            width / 2, height / 2,
            text=self.text_content,
            fill=text_color,
            font=("Helvetica", 12, "bold")
        )

        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        # Ensure all items respond to events
        for item in self.find_all():
            self.tag_bind(item, "<Enter>", self.on_hover)
            self.tag_bind(item, "<Leave>", self.on_leave)
            self.tag_bind(item, "<Button-1>", self.on_click)

    def on_hover(self, event):
        self.itemconfig(self.rounded_rect, fill=self.hover_color, outline=self.hover_color)

    def on_leave(self, event):
        self.itemconfig(self.rounded_rect, fill=self.bg_color, outline=self.bg_color)

    def on_click(self, event):
        self.command()