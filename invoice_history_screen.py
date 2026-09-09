"""
invoice_history_screen.py
Lists every invoice that's been saved: invoice #, customer, contact,
amount, and date — with a button (or double-click) to reopen the
saved PDF for any of them.
"""

import os
import tkinter as tk
from tkinter import ttk

import database
import dialogs
import invoice_generator
import ui_style as style


class InvoiceHistoryScreen(tk.Frame):
    def __init__(self, parent, on_back=None):
        super().__init__(parent, bg=style.COLOR_BG)
        self.on_back = on_back
        self.selected_invoice_number = None

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
        style.make_heading(top_bar, "Invoice History").pack(side="left", padx=20)

        search_frame = tk.Frame(self, bg=style.COLOR_BG)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        style.make_label(search_frame, "Search customer:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        style.make_entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=10)

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("invoice_number", "customer_name", "customer_contact", "net_total", "invoice_date")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        headings = {
            "invoice_number": "Invoice #",
            "customer_name": "Customer",
            "customer_contact": "Contact",
            "net_total": "Amount",
            "invoice_date": "Date",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, anchor="center", width=130)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._view_invoice())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        style.apply_treeview_style(ttk.Style())

        action_frame = tk.Frame(self, bg=style.COLOR_BG)
        action_frame.pack(fill="x", padx=20, pady=15)
        style.make_button(
            action_frame, "📄 View Invoice", self._view_invoice, color=style.COLOR_PRIMARY
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------

    def _refresh_list(self):
        search_text = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        for inv in database.get_all_invoices():
            customer = (inv["customer_name"] or "").lower()
            if search_text and search_text not in customer:
                continue
            self.tree.insert(
                "", "end",
                values=(
                    inv["invoice_number"],
                    inv["customer_name"] or "-",
                    inv["customer_contact"] or "-",
                    f"{inv['net_total']:.2f}",
                    inv["invoice_date"],
                )
            )

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_invoice_number = self.tree.item(selected[0])["values"][0]
        else:
            self.selected_invoice_number = None

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _view_invoice(self):
        if self.selected_invoice_number is None:
            dialogs.show_error(self, "No Invoice Selected", "Please click an invoice in the list first.")
            return

        filepath = invoice_generator.get_invoice_pdf_path(self.selected_invoice_number)
        if not os.path.exists(filepath):
            dialogs.show_error(
                self, "Invoice File Not Found",
                f"Could not find the saved PDF for invoice #{self.selected_invoice_number}."
            )
            return

        try:
            invoice_generator.open_pdf_for_viewing(filepath)
        except Exception as e:
            dialogs.show_error(self, "Could Not Open Invoice", str(e))