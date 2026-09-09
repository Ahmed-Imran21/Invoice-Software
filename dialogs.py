"""
dialogs.py
Custom popups, built to replace tkinter's built-in messagebox/simpledialog
for the specific cases that need to be more noticeable for older,
non-technical users: bigger text, and — for errors — a distinct sound
so a mistake is never silently missed.
"""

import sys
import tkinter as tk

import ui_style as style


def _play_error_sound(widget):
    """Plays a clear 'something is wrong' sound. Uses Windows' real
    system error sound where available; falls back to a plain bell
    on other systems (only relevant during development on Linux/Mac)."""
    if sys.platform == "win32":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return
        except Exception:
            pass
    widget.bell()


def _center_over(popup, parent):
    ref = parent.winfo_toplevel()
    popup.update_idletasks()
    width = popup.winfo_reqwidth()
    height = popup.winfo_reqheight()
    px = ref.winfo_rootx() + (ref.winfo_width() // 2) - (width // 2)
    py = ref.winfo_rooty() + (ref.winfo_height() // 2) - (height // 2)
    popup.geometry(f"{width}x{height}+{px}+{py}")


def show_error(parent, title, message):
    """Bigger error popup with a distinct error sound. Use this instead
    of tkinter.messagebox.showerror/showwarning for anything the user
    needs to clearly notice and fix before continuing."""
    popup = tk.Toplevel(parent)
    popup.title(title)
    popup.configure(bg=style.COLOR_BG)
    popup.resizable(False, False)
    popup.transient(parent)

    body = tk.Frame(popup, bg=style.COLOR_BG)
    body.pack(fill="both", expand=True, padx=30, pady=25)

    row = tk.Frame(body, bg=style.COLOR_BG)
    row.pack(fill="x")
    tk.Label(
        row, text="⚠", font=(style.FONT_FAMILY, 30), fg=style.COLOR_DANGER, bg=style.COLOR_BG
    ).pack(side="left", padx=(0, 15))
    tk.Label(
        row, text=message, font=style.FONTS["heading"], fg=style.COLOR_TEXT,
        bg=style.COLOR_BG, wraplength=420, justify="left"
    ).pack(side="left", fill="both", expand=True)

    style.make_button(
        body, "OK", popup.destroy, color=style.COLOR_DANGER, font_key="button_large"
    ).pack(fill="x", pady=(25, 0))

    body.update_idletasks()
    min_width = max(popup.winfo_reqwidth(), 420)
    popup.geometry(f"{min_width}x{popup.winfo_reqheight()}")
    _center_over(popup, parent)

    popup.deiconify()
    popup.update()          # make sure it's actually drawn before the sound plays
    _play_error_sound(popup)

    popup.grab_set()
    popup.wait_window()


def ask_quantity(parent, title, prompt, min_value=0.01):
    """
    Bigger quantity-entry popup, used for 'how much stock are you
    adding/subtracting' and 'how many of this item' on the invoice
    screen. Returns a float, or None if the user cancels.
    """
    popup = tk.Toplevel(parent)
    popup.title(title)
    popup.configure(bg=style.COLOR_BG)
    popup.resizable(False, False)
    popup.transient(parent)
    result = {"value": None}

    body = tk.Frame(popup, bg=style.COLOR_BG)
    body.pack(fill="both", expand=True, padx=30, pady=25)

    style.make_label(body, prompt, bold=True).pack(anchor="w", pady=(0, 15))

    var = tk.StringVar()
    entry = tk.Entry(body, textvariable=var, font=style.FONTS["heading"], width=10, justify="center")
    entry.pack(pady=(0, 15))
    entry.focus_set()

    error_label = tk.Label(body, text="", font=style.FONTS["label"], fg=style.COLOR_DANGER, bg=style.COLOR_BG)
    error_label.pack(anchor="w", pady=(0, 10))

    def submit(event=None):
        text = var.get().strip()
        try:
            value = float(text)
        except ValueError:
            error_label.config(text="Please enter a valid number.")
            _play_error_sound(popup)
            return
        if value < min_value:
            error_label.config(text=f"Must be at least {min_value:g}.")
            _play_error_sound(popup)
            return
        result["value"] = value
        popup.destroy()

    def cancel():
        result["value"] = None
        popup.destroy()

    entry.bind("<Return>", submit)
    popup.bind("<Escape>", lambda e: cancel())

    button_row = tk.Frame(body, bg=style.COLOR_BG)
    button_row.pack(fill="x", pady=(10, 0))
    style.make_button(
        button_row, "Cancel", cancel, color=style.COLOR_NEUTRAL,
        text_color=style.COLOR_NEUTRAL_TEXT, font_key="button_large"
    ).pack(side="left", expand=True, fill="x", padx=(0, 8))
    style.make_button(
        button_row, "OK", submit, color=style.COLOR_PRIMARY, font_key="button_large"
    ).pack(side="left", expand=True, fill="x", padx=(8, 0))

    body.update_idletasks()
    min_width = max(popup.winfo_reqwidth(), 380)
    popup.geometry(f"{min_width}x{popup.winfo_reqheight()}")
    _center_over(popup, parent)

    popup.grab_set()
    popup.wait_window()
    return result["value"]