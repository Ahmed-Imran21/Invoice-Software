"""
main.py
The entry point of the app. Shows a simple home screen with four big
buttons: Inventory, Make Invoice, Invoice History, and Customer Ledger.
Run this file to start the app.
"""

import tkinter as tk
from tkinter import messagebox

import database
import backup
from config import APP_TITLE, ICON_PATH, DATABASE_PATH
from inventory_screen import InventoryScreen
from invoice_screen import InvoiceScreen
from invoice_history_screen import InvoiceHistoryScreen
from customer_ledger_screen import CustomerLedgerScreen
import ui_style as style


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.configure(bg=style.COLOR_BG)
        style.init_scaling(self)  # must come before any screen is built

        # `default=` applies the icon to this window AND every Toplevel
        # opened later (the New Item form, the error popups), so they all
        # match. Purely cosmetic, so a failure here falls back silently to
        # Tk's stock icon rather than blocking the app from starting.
        try:
            self.iconbitmap(default=str(ICON_PATH))
        except Exception:
            pass

        self.current_screen = None
        self._show_home()

    def _clear_screen(self):
        if self.current_screen is not None:
            self.current_screen.destroy()
            self.current_screen = None

    def _show_home(self):
        self._clear_screen()

        home = tk.Frame(self, bg=style.COLOR_BG)
        home.pack(fill="both", expand=True)

        tk.Label(
            home, text=APP_TITLE, font=style.FONTS["title"],
            bg=style.COLOR_BG, fg=style.COLOR_TEXT
        ).pack(pady=(60, 40))

        button_frame = tk.Frame(home, bg=style.COLOR_BG)
        button_frame.pack()

        style.make_big_nav_button(
            button_frame, "📦 Inventory", self._show_inventory, style.COLOR_PRIMARY
        ).grid(row=0, column=0, padx=20, pady=10)

        style.make_big_nav_button(
            button_frame, "🧾 Make Invoice", self._show_invoice, style.COLOR_SUCCESS
        ).grid(row=0, column=1, padx=20, pady=10)

        style.make_big_nav_button(
            button_frame, "📜 Invoice History", self._show_history, "#6a1b9a"
        ).grid(row=1, column=0, padx=20, pady=10)

        style.make_big_nav_button(
            button_frame, "📒 Customer Ledger", self._show_ledger, "#ef6c00"
        ).grid(row=1, column=1, padx=20, pady=10)

        self.current_screen = home

    def _show_inventory(self):
        self._clear_screen()
        self.current_screen = InventoryScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)

    def _show_invoice(self):
        self._clear_screen()
        self.current_screen = InvoiceScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)

    def _show_history(self):
        self._clear_screen()
        self.current_screen = InvoiceHistoryScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)

    def _show_ledger(self):
        self._clear_screen()
        self.current_screen = CustomerLedgerScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)


def _show_startup_failure(message):
    """Startup failures happen before the main window exists, and this app
    is built with --windowed (no console), so an uncaught error here would
    mean the user double-clicks the icon and absolutely nothing visible
    happens. Put a real dialog on screen instead."""
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_TITLE, message)
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        database.init_db()
    except Exception as e:
        # Without a database the app genuinely cannot run — say so plainly
        # instead of dying invisibly.
        _show_startup_failure(
            "Could not open or create the database, so the program can't start.\n\n"
            f"It tried to use:\n{DATABASE_PATH}\n\n"
            f"Error: {e}\n\n"
            "This usually means the folder is read-only or the program was "
            "placed somewhere it isn't allowed to write to. Try moving the "
            "program to your Desktop or Documents folder and opening it again."
        )
        raise SystemExit(1)

    # The daily backup is a background nicety — it must never stop the app
    # from opening. run_daily_backup() records its own failures to
    # data/backup_errors.log so a silent failure stays discoverable.
    backup.run_daily_backup()

    app = App()
    app.mainloop()