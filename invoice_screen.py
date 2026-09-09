"""
invoice_screen.py
The invoice creation screen: pick items, set quantity, apply discount%
and tax%, see live totals, then save + print. Saving automatically
deducts stock (handled by database.save_invoice()). Quantity entry
and errors use the bigger custom dialogs from dialogs.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import database
import dialogs
import invoice_generator
from config import DEFAULT_DISCOUNT_PERCENT, DEFAULT_TAX_PERCENT
from models import Invoice, InvoiceItem
import ui_style as style


class InvoiceScreen(tk.Frame):
    def __init__(self, parent, on_back=None):
        super().__init__(parent, bg=style.COLOR_BG)
        self.on_back = on_back
        self.selected_catalog_item_id = None
        self.invoice_lines = []

        self._build_layout()
        self._refresh_catalog_list()
        self._refresh_invoice_table()
        self._recalculate_totals()

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
        style.make_heading(top_bar, "Make Invoice").pack(side="left", padx=20)

        body = tk.Frame(self, bg=style.COLOR_BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_catalog_panel(body)
        self._build_invoice_panel(body)

    def _build_catalog_panel(self, parent):
        panel = tk.Frame(parent, bg=style.COLOR_BG)
        panel.pack(side="left", fill="both", expand=True, padx=(0, 15))

        style.make_label(panel, "Available Items", bold=True).pack(anchor="w")

        self.catalog_search_var = tk.StringVar()
        self.catalog_search_var.trace_add("write", lambda *_: self._refresh_catalog_list())
        style.make_entry(panel, textvariable=self.catalog_search_var).pack(fill="x", pady=8)

        columns = ("code", "name", "rate", "stock")
        self.catalog_tree = ttk.Treeview(panel, columns=columns, show="headings", height=14)
        headings = {"code": "Code", "name": "Item Name", "rate": "Rate", "stock": "In Stock"}
        for col in columns:
            self.catalog_tree.heading(col, text=headings[col])
            self.catalog_tree.column(col, anchor="center", width=90)
        self.catalog_tree.pack(fill="both", expand=True)
        self.catalog_tree.bind("<<TreeviewSelect>>", self._on_select_catalog_item)
        style.apply_treeview_style(ttk.Style())

        style.make_button(
            panel, "Add to Invoice →", self._add_line_item, color=style.COLOR_SUCCESS
        ).pack(fill="x", pady=10)

    def _build_invoice_panel(self, parent):
        panel = tk.Frame(parent, bg=style.COLOR_BG)
        panel.pack(side="left", fill="both", expand=True)

        style.make_label(panel, "Current Invoice", bold=True).pack(anchor="w")

        columns = ("name", "qty", "rate", "total")
        self.invoice_tree = ttk.Treeview(panel, columns=columns, show="headings", height=8)
        headings = {"name": "Item", "qty": "Qty", "rate": "Rate", "total": "Line Total"}
        for col in columns:
            self.invoice_tree.heading(col, text=headings[col])
            self.invoice_tree.column(col, anchor="center", width=100)
        self.invoice_tree.pack(fill="both", expand=True, pady=8)
        style.apply_treeview_style(ttk.Style())

        style.make_button(
            panel, "Remove Selected Item", self._remove_line_item, color=style.COLOR_DANGER
        ).pack(fill="x", pady=(0, 10))

        form = tk.Frame(panel, bg=style.COLOR_BG)
        form.pack(fill="x", pady=5)
        self.customer_name_var = tk.StringVar()
        self.customer_contact_var = tk.StringVar()
        self._make_form_row(form, "Customer Name", self.customer_name_var)
        self._make_form_row(form, "Contact", self.customer_contact_var)

        percent_frame = tk.Frame(panel, bg=style.COLOR_BG)
        percent_frame.pack(fill="x", pady=10)

        self.discount_var = tk.StringVar(value=str(DEFAULT_DISCOUNT_PERCENT))
        self.tax_var = tk.StringVar(value=str(DEFAULT_TAX_PERCENT))
        self.discount_var.trace_add("write", lambda *_: self._recalculate_totals())
        self.tax_var.trace_add("write", lambda *_: self._recalculate_totals())

        self._make_percent_field(percent_frame, "Discount %", self.discount_var)
        self._make_percent_field(percent_frame, "Tax %", self.tax_var)

        self.totals_frame = tk.Frame(panel, bg=style.COLOR_BG)
        self.totals_frame.pack(fill="x", pady=10)
        self.totals_labels = {}
        for key in ["Gross Total", "Discount", "Tax", "Net Total"]:
            row = tk.Frame(self.totals_frame, bg=style.COLOR_BG)
            row.pack(fill="x")
            style.make_label(row, key).pack(side="left")
            value_label = style.make_label(row, "0.00", bold=(key == "Net Total"))
            value_label.pack(side="right")
            self.totals_labels[key] = value_label

        style.make_button(
            panel, "🖨 Save & Print Invoice", self._save_and_print,
            color=style.COLOR_PRIMARY, font_key="button_large"
        ).pack(fill="x", pady=15)

    def _make_form_row(self, parent, label_text, var):
        row = tk.Frame(parent, bg=style.COLOR_BG)
        row.pack(fill="x", pady=3)
        style.make_label(row, label_text).pack(side="left")
        style.make_entry(row, textvariable=var).pack(side="right", fill="x", expand=True, padx=10)

    def _make_percent_field(self, parent, label_text, var):
        row = tk.Frame(parent, bg=style.COLOR_BG)
        row.pack(side="left", padx=(0, 20))
        style.make_label(row, label_text).pack(side="left")
        style.make_entry(row, textvariable=var, width=6).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # CATALOG (left side)
    # ------------------------------------------------------------------

    def _refresh_catalog_list(self):
        search_text = self.catalog_search_var.get().strip().lower()
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        self.catalog_rows = {}

        for item in database.get_all_items():
            if search_text and search_text not in item.name.lower() and search_text not in item.code.lower():
                continue
            row_id = self.catalog_tree.insert(
                "", "end", values=(item.code, item.name, f"{item.unit_rate:.2f}", f"{item.stock_qty:g}")
            )
            self.catalog_rows[row_id] = item

    def _on_select_catalog_item(self, event):
        selected = self.catalog_tree.selection()
        self.selected_catalog_item_id = self.catalog_rows.get(selected[0]) if selected else None

    def _add_line_item(self):
        item = self.selected_catalog_item_id
        if item is None:
            dialogs.show_error(self, "No Item Selected", "Please click an item from the list first.")
            return

        qty = dialogs.ask_quantity(self, "Quantity", f"How many of '{item.name}'?", min_value=0.01)
        if qty is None:
            return
        if qty > item.stock_qty:
            dialogs.show_error(self, "Not Enough Stock", f"Only {item.stock_qty:g} available in stock.")
            return

        self.invoice_lines.append(InvoiceItem(
            item_id=item.item_id, item_name=item.name, code=item.code,
            qty=qty, unit_rate=item.unit_rate
        ))
        self._refresh_invoice_table()
        self._recalculate_totals()

    def _remove_line_item(self):
        selected = self.invoice_tree.selection()
        if not selected:
            dialogs.show_error(self, "No Item Selected", "Select an item in the invoice to remove it.")
            return
        index = self.invoice_tree.index(selected[0])
        del self.invoice_lines[index]
        self._refresh_invoice_table()
        self._recalculate_totals()

    # ------------------------------------------------------------------
    # INVOICE TABLE + TOTALS (right side)
    # ------------------------------------------------------------------

    def _refresh_invoice_table(self):
        self.invoice_tree.delete(*self.invoice_tree.get_children())
        for line in self.invoice_lines:
            self.invoice_tree.insert(
                "", "end",
                values=(line.item_name, f"{line.qty:g}", f"{line.unit_rate:.2f}", f"{line.line_total:.2f}")
            )

    def _build_invoice_object(self) -> Invoice:
        try:
            discount = float(self.discount_var.get() or 0)
            tax = float(self.tax_var.get() or 0)
        except ValueError:
            discount, tax = 0.0, 0.0

        return Invoice(
            customer_name=self.customer_name_var.get().strip(),
            customer_address="",
            customer_contact=self.customer_contact_var.get().strip(),
            invoice_date=date.today().isoformat(),
            items=self.invoice_lines,
            discount_percent=discount,
            tax_percent=tax,
            paid_amount=0.0,
            prepared_by="",
        )

    def _recalculate_totals(self):
        invoice = self._build_invoice_object()
        self.totals_labels["Gross Total"].config(text=f"{invoice.gross_total:.2f}")
        self.totals_labels["Discount"].config(text=f"-{invoice.discount_amount:.2f}")
        self.totals_labels["Tax"].config(text=f"+{invoice.tax_amount:.2f}")
        self.totals_labels["Net Total"].config(text=f"{invoice.net_total:.2f}")

    # ------------------------------------------------------------------
    # SAVE + PRINT
    # ------------------------------------------------------------------

    def _save_and_print(self):
        if not self.invoice_lines:
            dialogs.show_error(self, "Empty Invoice", "Add at least one item before saving.")
            return

        invoice = self._build_invoice_object()

        try:
            invoice.invoice_id = database.save_invoice(invoice)
        except ValueError as e:
            dialogs.show_error(self, "Could Not Save Invoice", str(e))
            return

        try:
            filepath, print_status = invoice_generator.generate_and_print(invoice)
            messagebox.showinfo(
                "Invoice Saved",
                f"Invoice saved and stock updated.\nNet Total: {invoice.net_total:.2f}\n\n{print_status}"
            )
        except Exception as e:
            dialogs.show_error(
                self, "Invoice Saved, But Printing Failed",
                f"The invoice was saved and stock was updated, but the PDF could not be "
                f"opened/printed automatically.\n\nError: {e}"
            )

        self.invoice_lines = []
        self.customer_name_var.set("")
        self.customer_contact_var.set("")
        self._refresh_invoice_table()
        self._refresh_catalog_list()
        self._recalculate_totals()