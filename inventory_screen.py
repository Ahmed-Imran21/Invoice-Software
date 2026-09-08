"""
inventory_screen.py
The inventory management screen: view stock, add/subtract quantities,
and add brand-new items. No SQL, no typing item IDs — everything is
click-and-select, built for non-technical users.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import database
from models import Item


class InventoryScreen(tk.Frame):
    def __init__(self, parent, on_back=None):
        super().__init__(parent, bg="white")
        self.on_back = on_back
        self.selected_item_id = None

        self._build_layout()
        self._refresh_item_list()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------

    def _build_layout(self):
        # Top bar: title + back button
        top_bar = tk.Frame(self, bg="white")
        top_bar.pack(fill="x", padx=20, pady=15)

        if self.on_back:
            tk.Button(
                top_bar, text="← Back", font=("Segoe UI", 12),
                command=self.on_back, bg="#e0e0e0", relief="flat", padx=10, pady=5
            ).pack(side="left")

        tk.Label(
            top_bar, text="Inventory", font=("Segoe UI", 20, "bold"), bg="white"
        ).pack(side="left", padx=20)

        # Search bar
        search_frame = tk.Frame(self, bg="white")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(search_frame, text="Search:", font=("Segoe UI", 13), bg="white").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_item_list())
        tk.Entry(
            search_frame, textvariable=self.search_var, font=("Segoe UI", 13), width=30
        ).pack(side="left", padx=10)

        # Item list (table)
        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("code", "name", "unit", "rate", "stock")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        headings = {"code": "Code", "name": "Item Name", "unit": "Unit", "rate": "Rate", "stock": "Stock"}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, anchor="center", width=120)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_item)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 12), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

        # Action buttons
        action_frame = tk.Frame(self, bg="white")
        action_frame.pack(fill="x", padx=20, pady=15)

        self._make_button(action_frame, "＋ Add Stock", "#2e7d32", self._add_stock).pack(side="left", padx=5)
        self._make_button(action_frame, "－ Subtract Stock", "#c62828", self._subtract_stock).pack(side="left", padx=5)
        self._make_button(action_frame, "＋ New Item", "#1565c0", self._new_item).pack(side="left", padx=5)

    def _make_button(self, parent, text, color, command):
        return tk.Button(
            parent, text=text, font=("Segoe UI", 13, "bold"), fg="white", bg=color,
            activebackground=color, relief="flat", padx=15, pady=10, command=command
        )

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------

    def _refresh_item_list(self):
        search_text = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        self.items_by_row = {}

        for item in database.get_all_items():
            if search_text and search_text not in item.name.lower() and search_text not in item.code.lower():
                continue
            row_id = self.tree.insert(
                "", "end",
                values=(item.code, item.name, item.unit, f"{item.unit_rate:.2f}", f"{item.stock_qty:g}")
            )
            self.items_by_row[row_id] = item.item_id

    def _on_select_item(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_item_id = self.items_by_row.get(selected[0])
        else:
            self.selected_item_id = None

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _require_selection(self):
        if self.selected_item_id is None:
            messagebox.showwarning("No item selected", "Please click an item in the list first.")
            return False
        return True

    def _add_stock(self):
        if not self._require_selection():
            return
        qty = simpledialog.askfloat("Add Stock", "How much stock are you adding?", minvalue=0.01)
        if qty is None:
            return
        database.adjust_stock(self.selected_item_id, qty, reason="Manual Add")
        self._refresh_item_list()
        messagebox.showinfo("Done", "Stock added successfully.")

    def _subtract_stock(self):
        if not self._require_selection():
            return
        qty = simpledialog.askfloat("Subtract Stock", "How much stock are you removing?", minvalue=0.01)
        if qty is None:
            return
        try:
            database.adjust_stock(self.selected_item_id, -qty, reason="Manual Subtract")
            self._refresh_item_list()
            messagebox.showinfo("Done", "Stock updated successfully.")
        except ValueError as e:
            messagebox.showerror("Not enough stock", str(e))

    def _new_item(self):
        NewItemDialog(self, on_saved=self._refresh_item_list)


class NewItemDialog(tk.Toplevel):
    """A simple form window for adding a brand-new item."""

    def __init__(self, parent, on_saved):
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("New Item")
        self.geometry("360x360")
        self.resizable(False, False)
        self.configure(bg="white")

        self.entries = {}
        fields = [
            ("code", "Item Code"),
            ("name", "Item Name"),
            ("unit", "Unit (e.g. PCS, MT)"),
            ("unit_rate", "Rate per Unit"),
            ("stock_qty", "Starting Stock Quantity"),
        ]

        for key, label in fields:
            tk.Label(self, text=label, font=("Segoe UI", 12), bg="white").pack(pady=(12, 2))
            entry = tk.Entry(self, font=("Segoe UI", 12), width=25)
            entry.pack()
            self.entries[key] = entry

        tk.Button(
            self, text="Save Item", font=("Segoe UI", 13, "bold"), fg="white", bg="#1565c0",
            relief="flat", padx=15, pady=8, command=self._save
        ).pack(pady=20)

    def _save(self):
        code = self.entries["code"].get().strip()
        name = self.entries["name"].get().strip()
        unit = self.entries["unit"].get().strip()

        if not code or not name:
            messagebox.showwarning("Missing info", "Item code and name are required.")
            return

        try:
            unit_rate = float(self.entries["unit_rate"].get())
            stock_qty = float(self.entries["stock_qty"].get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid number", "Rate and stock quantity must be numbers.")
            return

        try:
            database.add_item(Item(name=name, code=code, unit=unit, unit_rate=unit_rate, stock_qty=stock_qty))
        except Exception as e:
            messagebox.showerror("Could not save", f"Item code might already exist.\n\n{e}")
            return

        self.on_saved()
        self.destroy()