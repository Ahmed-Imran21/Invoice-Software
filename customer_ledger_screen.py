"""
customer_ledger_screen.py
The "Khata" screen — every customer being tracked, what they currently
owe (highest debt first), and a way to record a payment against their
balance without needing to create a new invoice.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
import dialogs
import ui_style as style


class CustomerLedgerScreen(tk.Frame):
    def __init__(self, parent, on_back=None):
        super().__init__(parent, bg=style.COLOR_BG)
        self.on_back = on_back
        self.selected_customer = None  # a Customer object, not just an id

        self._build_layout()
        self._refresh_list()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------

    def _build_layout(self):
        top_bar = tk.Frame(self, bg=style.COLOR_BG)
        top_bar.pack(fill="x", padx=20, pady=15)

        if self.on_back:
            style.make_button(
                top_bar, "← Back", self.on_back,
                color=style.COLOR_NEUTRAL, text_color=style.COLOR_NEUTRAL_TEXT
            ).pack(side="left")
        style.make_heading(top_bar, "Customer Ledger (Khata)").pack(side="left", padx=20)

        search_frame = tk.Frame(self, bg=style.COLOR_BG)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        style.make_label(search_frame, "Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        style.make_entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=10)

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("name", "contact", "balance")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        headings = {"name": "Customer", "contact": "Contact", "balance": "Owes (Rs.)"}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        style.apply_treeview_style(ttk.Style())

        action_frame = tk.Frame(self, bg=style.COLOR_BG)
        action_frame.pack(fill="x", padx=20, pady=15)
        style.make_button(
            action_frame, "💵 Record Payment", self._record_payment, color=style.COLOR_SUCCESS
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------

    def _refresh_list(self):
        search_text = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        self.customers_by_row = {}

        for customer in database.get_all_customers():
            if search_text and search_text not in customer.name.lower() and search_text not in customer.contact.lower():
                continue
            row_id = self.tree.insert(
                "", "end",
                values=(customer.name, customer.contact, f"{customer.current_balance:.2f}")
            )
            self.customers_by_row[row_id] = customer

    def _on_select(self, event):
        selected = self.tree.selection()
        self.selected_customer = self.customers_by_row.get(selected[0]) if selected else None

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _record_payment(self):
        if self.selected_customer is None:
            dialogs.show_error(self, "No Customer Selected", "Please click a customer in the list first.")
            return

        customer = self.selected_customer
        if customer.current_balance <= 0:
            dialogs.show_error(
                self, "Nothing Owed",
                f"{customer.name} doesn't currently owe anything."
            )
            return

        amount = dialogs.ask_quantity(
            self, "Record Payment",
            f"{customer.name} currently owes {customer.current_balance:.2f}.\nHow much are they paying now?",
            min_value=0.01
        )
        if amount is None:
            return

        try:
            new_balance = database.record_payment(customer.customer_id, amount, note="Khata payment")
        except ValueError as e:
            dialogs.show_error(self, "Could Not Record Payment", str(e))
            return

        messagebox.showinfo(
            "Payment Recorded",
            f"{customer.name}'s balance is now {new_balance:.2f}."
        )
        self._refresh_list()