"""
ui_style.py
Central style control — now with automatic font scaling. Fonts are
shared tkinter.font.Font objects, not static tuples, so when the
window is resized or maximized, every widget using them updates its
text size live, instead of staying frozen at the size it was created.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

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


class ScrollableFrame(tk.Frame):
    """A vertically scrollable container (Canvas + Scrollbar + inner Frame),
    since tkinter has no built-in one. Needed because pack() doesn't make
    overflowing content visible or scrollable on its own — it silently
    compresses whatever doesn't fit down to near-zero height instead, which
    is exactly what happened to the invoice screen's Save & Print button
    at a large font scale.

    Build content inside `.interior`, then call `.enable_mousewheel()`
    once everything has been added. When the content is shorter than the
    visible area it stretches to fill it (looks the same as a plain pack()
    layout); when it's taller, it scrolls instead of getting crushed.
    Mouse-wheel scrolling works anywhere over the scrollable area except
    directly over a Treeview, which keeps scrolling its own rows."""

    def __init__(self, parent, bg=None):
        bg = bg or COLOR_BG
        super().__init__(parent, bg=bg)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.interior = tk.Frame(self.canvas, bg=bg)
        self._window_id = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")

        self.interior.bind("<Configure>", self._sync_scrollregion)
        self.canvas.bind("<Configure>", self._sync_scrollregion)

    def _sync_scrollregion(self, event=None):
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        content_height = self.interior.winfo_reqheight()
        self.canvas.itemconfig(
            self._window_id, width=canvas_width, height=max(content_height, canvas_height)
        )
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def enable_mousewheel(self):
        """Call once after all content has been added, so scroll wheel
        input works anywhere over the scrollable area."""
        self._bind_wheel_recursive(self.canvas)

    def _bind_wheel_recursive(self, widget):
        if isinstance(widget, ttk.Treeview):
            return  # keep its own native row-by-row scrolling untouched
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_wheel_recursive(child)

    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")
        return "break"