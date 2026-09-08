"""
main.py
The entry point of the app. Shows a simple home screen with two big
buttons: Inventory and Make Invoice. Run this file to start the app.
"""

import tkinter as tk
from tkinter import messagebox

import database
from config import APP_TITLE, ICON_PATH
from inventory_screen import InventoryScreen
import ui_style as style
from invoice_screen import InvoiceScreen

# invoice_screen isn't built yet — import it once it exists, then
# uncomment the "Make Invoice" button logic below.
# from invoice_screen import InvoiceScreen


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.configure(bg=style.COLOR_BG)

        # Set the window/taskbar icon, if present
        try:
            self.iconbitmap(ICON_PATH)
        except tk.TclError:
            pass  # icon file not ready yet — fine during development

        self.current_screen = None
        self._show_home()

    # ------------------------------------------------------------------

    def _clear_screen(self):
        if self.current_screen is not None:
            self.current_screen.destroy()
            self.current_screen = None

    def _show_home(self):
        self._clear_screen()

        home = tk.Frame(self, bg=style.COLOR_BG)
        home.pack(fill="both", expand=True)

        tk.Label(
            home, text=APP_TITLE, font=style.FONT_TITLE,
            bg=style.COLOR_BG, fg=style.COLOR_TEXT
        ).pack(pady=(80, 40))

        button_frame = tk.Frame(home, bg=style.COLOR_BG)
        button_frame.pack()

        style.make_big_nav_button(
            button_frame, "📦 Inventory", self._show_inventory, style.COLOR_PRIMARY
        ).grid(row=0, column=0, padx=20)

        style.make_big_nav_button(
            button_frame, "🧾 Make Invoice", self._show_invoice, style.COLOR_SUCCESS
        ).grid(row=0, column=1, padx=20)

        self.current_screen = home

    def _show_inventory(self):
        self._clear_screen()
        self.current_screen = InventoryScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)


    def _show_invoice(self):
        self._clear_screen()
        self.current_screen = InvoiceScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)


if __name__ == "__main__":
    database.init_db()
    app = App()
    app.mainloop()