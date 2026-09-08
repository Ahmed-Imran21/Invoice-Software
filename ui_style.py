"""
ui_style.py
One place to control how the whole app looks: fonts, colors, and a
shared button/label style. Built for 50+ year old, non-technical
users — large fonts, high contrast, generous spacing. Change values
here and it reflects everywhere the helpers are used.
"""

import tkinter as tk

# ---------- Fonts ----------
FONT_FAMILY = "Segoe UI"

FONT_TITLE = (FONT_FAMILY, 26, "bold")       # Home screen title
FONT_HEADING = (FONT_FAMILY, 20, "bold")     # Screen headings ("Inventory", "Make Invoice")
FONT_LABEL = (FONT_FAMILY, 13)               # Regular text, form labels
FONT_LABEL_BOLD = (FONT_FAMILY, 13, "bold")
FONT_BUTTON = (FONT_FAMILY, 14, "bold")
FONT_BUTTON_LARGE = (FONT_FAMILY, 18, "bold")  # Home screen's big nav buttons
FONT_TABLE = (FONT_FAMILY, 12)
FONT_TABLE_HEADING = (FONT_FAMILY, 12, "bold")

# ---------- Colors ----------
COLOR_BG = "white"
COLOR_TEXT = "#212121"
COLOR_MUTED_TEXT = "#616161"
COLOR_BORDER = "#e0e0e0"

COLOR_PRIMARY = "#1565c0"      # main actions — e.g. "Inventory", "New Item"
COLOR_SUCCESS = "#2e7d32"      # positive actions — e.g. "Add Stock", "Make Invoice"
COLOR_DANGER = "#c62828"       # subtractive/destructive actions — e.g. "Subtract Stock"
COLOR_NEUTRAL = "#e0e0e0"      # low-emphasis actions — e.g. "Back"
COLOR_NEUTRAL_TEXT = "#212121"

# ---------- Spacing ----------
PAD_SMALL = 5
PAD_MEDIUM = 15
PAD_LARGE = 30


# ---------- Reusable widget builders ----------

def make_button(parent, text, command, color=COLOR_PRIMARY, font=FONT_BUTTON, text_color="white"):
    """Standard app button: solid color, flat, generous padding for easy clicking."""
    return tk.Button(
        parent, text=text, font=font, fg=text_color, bg=color,
        activebackground=color, activeforeground=text_color,
        relief="flat", padx=15, pady=10, command=command, cursor="hand2"
    )


def make_big_nav_button(parent, text, command, color):
    """Extra-large button for the home screen's main navigation."""
    return tk.Button(
        parent, text=text, font=FONT_BUTTON_LARGE, fg="white", bg=color,
        activebackground=color, activeforeground="white",
        relief="flat", width=16, height=3, command=command, cursor="hand2"
    )


def make_heading(parent, text):
    return tk.Label(parent, text=text, font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT)


def make_label(parent, text, bold=False):
    font = FONT_LABEL_BOLD if bold else FONT_LABEL
    return tk.Label(parent, text=text, font=font, bg=COLOR_BG, fg=COLOR_TEXT)


def apply_treeview_style(style):
    """Call once per Treeview (table) to make rows tall and text large enough to read easily."""
    style.configure("Treeview", font=FONT_TABLE, rowheight=32, foreground=COLOR_TEXT)
    style.configure("Treeview.Heading", font=FONT_TABLE_HEADING)