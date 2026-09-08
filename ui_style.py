"""
ui_style.py
Central style control — now with automatic font scaling. Fonts are
shared tkinter.font.Font objects, not static tuples, so when the
window is resized or maximized, every widget using them updates its
text size live, instead of staying frozen at the size it was created.
"""

import tkinter as tk
import tkinter.font as tkfont

FONT_FAMILY = "Segoe UI"

# Base sizes, tuned for a 900x600 window — these are what gets scaled.
_BASE_SIZES = {
    "title": 26,
    "heading": 20,
    "label": 13,
    "label_bold": 13,
    "button": 14,
    "button_large": 18,
    "table": 12,
    "table_heading": 12,
}
_BOLD_KEYS = {"title", "heading", "label_bold", "button", "button_large", "table_heading"}

BASE_WIDTH = 900
BASE_HEIGHT = 600

MIN_SCALE = 0.85
MAX_SCALE = 1.8

FONTS = {}
_root = None
_resize_job = None
_treeview_styles = []


def init_scaling(root):
    global _root
    _root = root

    for key, base_size in _BASE_SIZES.items():
        weight = "bold" if key in _BOLD_KEYS else "normal"
        FONTS[key] = tkfont.Font(family=FONT_FAMILY, size=base_size, weight=weight)

    root.bind("<Configure>", _on_resize)


def _on_resize(event):
    global _resize_job
    if event.widget != _root:
        return
    if _resize_job is not None:
        _root.after_cancel(_resize_job)
    _resize_job = _root.after(120, _apply_scale)


def _apply_scale():
    width = _root.winfo_width()
    height = _root.winfo_height()
    if width <= 1 or height <= 1:
        return

    scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
    scale = max(MIN_SCALE, min(MAX_SCALE, scale))

    for key, base_size in _BASE_SIZES.items():
        FONTS[key].configure(size=max(8, round(base_size * scale)))

    for ttk_style in _treeview_styles:
        ttk_style.configure("Treeview", rowheight=int(32 * scale))


COLOR_BG = "white"
COLOR_TEXT = "#212121"
COLOR_MUTED_TEXT = "#616161"
COLOR_BORDER = "#e0e0e0"

COLOR_PRIMARY = "#1565c0"
COLOR_SUCCESS = "#2e7d32"
COLOR_DANGER = "#c62828"
COLOR_NEUTRAL = "#e0e0e0"
COLOR_NEUTRAL_TEXT = "#212121"

PAD_SMALL = 5
PAD_MEDIUM = 15
PAD_LARGE = 30


def make_button(parent, text, command, color=COLOR_PRIMARY, font_key="button", text_color="white"):
    return tk.Button(
        parent, text=text, font=FONTS[font_key], fg=text_color, bg=color,
        activebackground=color, activeforeground=text_color,
        relief="flat", padx=15, pady=10, command=command, cursor="hand2"
    )


def make_big_nav_button(parent, text, command, color):
    return tk.Button(
        parent, text=text, font=FONTS["button_large"], fg="white", bg=color,
        activebackground=color, activeforeground="white",
        relief="flat", width=16, height=3, command=command, cursor="hand2"
    )


def make_heading(parent, text):
    return tk.Label(parent, text=text, font=FONTS["heading"], bg=COLOR_BG, fg=COLOR_TEXT)


def make_label(parent, text, bold=False):
    font_key = "label_bold" if bold else "label"
    return tk.Label(parent, text=text, font=FONTS[font_key], bg=COLOR_BG, fg=COLOR_TEXT)


def make_entry(parent, textvariable=None, width=None):
    kwargs = {"font": FONTS["label"]}
    if textvariable is not None:
        kwargs["textvariable"] = textvariable
    if width is not None:
        kwargs["width"] = width
    return tk.Entry(parent, **kwargs)


def apply_treeview_style(style):
    style.configure("Treeview", font=FONTS["table"], rowheight=32, foreground=COLOR_TEXT)
    style.configure("Treeview.Heading", font=FONTS["table_heading"])
    if style not in _treeview_styles:
        _treeview_styles.append(style)