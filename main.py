"""
main.py
The entry point of the app. Shows a simple home screen with two big
buttons: Inventory and Make Invoice. Run this file to start the app.
"""

import tkinter as tk

import database
from config import APP_TITLE, ICON_PATH
from inventory_screen import InventoryScreen

# invoice_screen isn't built yet — import it once it exists, then
# uncomment the "Make Invoice" button logic below.
# from invoice_screen import InvoiceScreen


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.configure(bg="white")

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

        home = tk.Frame(self, bg="white")
        home.pack(fill="both", expand=True)

        tk.Label(
            home, text=APP_TITLE, font=("Segoe UI", 26, "bold"), bg="white"
        ).pack(pady=(80, 40))

        button_frame = tk.Frame(home, bg="white")
        button_frame.pack()

        tk.Button(
            button_frame, text="📦 Inventory", font=("Segoe UI", 18, "bold"),
            fg="white", bg="#1565c0", relief="flat", width=16, height=3,
            command=self._show_inventory
        ).grid(row=0, column=0, padx=20)

        tk.Button(
            button_frame, text="🧾 Make Invoice", font=("Segoe UI", 18, "bold"),
            fg="white", bg="#2e7d32", relief="flat", width=16, height=3,
            command=self._show_invoice
        ).grid(row=0, column=1, padx=20)

        self.current_screen = home

    def _show_inventory(self):
        self._clear_screen()
        self.current_screen = InventoryScreen(self, on_back=self._show_home)
        self.current_screen.pack(fill="both", expand=True)

    def _show_invoice(self):
        # Placeholder until invoice_screen.py is built.
        # Once it exists, replace this with:
        #   self._clear_screen()
        #   self.current_screen = InvoiceScreen(self, on_back=self._show_home)
        #   self.current_screen.pack(fill="both", expand=True)
        tk.messagebox_shown = True
        from tkinter import messagebox
        messagebox.showinfo("Coming soon", "The invoice screen isn't built yet.")


if __name__ == "__main__":
    database.init_db()
    app = App()
    app.mainloop()