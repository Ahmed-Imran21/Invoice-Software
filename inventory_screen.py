"""
inventory_screen.py
The inventory management screen: view stock, add/subtract quantities,
and add brand-new items. No SQL, no typing item IDs — everything is
click-and-select, built for non-technical users. Errors use the
custom dialogs.show_error popup (bigger text + error sound); quantity
entry uses dialogs.ask_quantity (bigger than tkinter's default).
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
import dialogs
from models import Item
import ui_style as style


class InventoryScreen(tk.Frame):
    def __init__(self, parent, on_back=None):
        super().__init__(parent, bg=style.COLOR_BG)
        self.on_back = on_back
        self.selected_item_id = None

        self._build_layout()
        self._refresh_item_list()

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

        style.make_heading(top_bar, "Inventory").pack(side="left", padx=20)

        scroll = style.ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        content = scroll.interior

        search_frame = tk.Frame(content, bg=style.COLOR_BG)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        style.make_label(search_frame, "Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_item_list())
        style.make_entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=10)

        list_frame = tk.Frame(content)
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

        style.apply_treeview_style(ttk.Style())

        action_frame = tk.Frame(content, bg=style.COLOR_BG)
        action_frame.pack(fill="x", padx=20, pady=15)

        style.make_button(
            action_frame, "＋ Add Stock", self._add_stock, color=style.COLOR_SUCCESS
        ).pack(side="left", padx=5)
        style.make_button(
            action_frame, "－ Subtract Stock", self._subtract_stock, color=style.COLOR_DANGER
        ).pack(side="left", padx=5)
        style.make_button(
            action_frame, "＋ New Item", self._new_item, color=style.COLOR_PRIMARY
        ).pack(side="left", padx=5)

        scroll.enable_mousewheel()

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
            dialogs.show_error(self, "No Item Selected", "Please click an item in the list first.")
            return False
        return True

    def _add_stock(self):
        if not self._require_selection():
            return
        qty = dialogs.ask_quantity(self, "Add Stock", "How much stock are you adding?", min_value=0.01)
        if qty is None:
            return
        try:
            database.adjust_stock(self.selected_item_id, qty, reason="Manual Add")
            self._refresh_item_list()
            messagebox.showinfo("Done", "Stock added successfully.")
        except ValueError as e:
            dialogs.show_error(self, "Could Not Add Stock", str(e))
        except Exception as e:
            dialogs.show_error(
                self, "Could Not Add Stock",
                f"The stock was not changed because of an unexpected problem.\n\nError: {e}"
            )

    def _subtract_stock(self):
        if not self._require_selection():
            return
        qty = dialogs.ask_quantity(self, "Subtract Stock", "How much stock are you removing?", min_value=0.01)
        if qty is None:
            return
        try:
            database.adjust_stock(self.selected_item_id, -qty, reason="Manual Subtract")
            self._refresh_item_list()
            messagebox.showinfo("Done", "Stock updated successfully.")
        except ValueError as e:
            dialogs.show_error(self, "Not Enough Stock", str(e))
        except Exception as e:
            dialogs.show_error(
                self, "Could Not Update Stock",
                f"The stock was not changed because of an unexpected problem.\n\nError: {e}"
            )

    def _new_item(self):
        NewItemDialog(self, on_saved=self._refresh_item_list)


class NewItemDialog(tk.Toplevel):
    """A simple form window for adding a brand-new item."""

    def __init__(self, parent, on_saved):
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("New Item")
        self.configure(bg=style.COLOR_BG)
        self.resizable(True, True)
        self.minsize(360, 260)

        self.entries = {}
        fields = [
            ("code", "Item Code"),
            ("name", "Item Name"),
            ("unit", "Unit (e.g. PCS, MT)"),
            ("unit_rate", "Rate per Unit"),
            ("stock_qty", "Starting Stock Quantity"),
        ]

        # Packed first with side="bottom" so it always keeps its own space
        # at the bottom of the dialog — it can never be pushed out of view
        # by the form above it, no matter how tall that gets or how far
        # the user has scrolled.
        style.make_button(
            self, "Save Item", self._save, color=style.COLOR_PRIMARY
        ).pack(side="bottom", fill="x", padx=20, pady=20)

        scroll = style.ScrollableFrame(self)
        scroll.pack(side="top", fill="both", expand=True)
        form = tk.Frame(scroll.interior, bg=style.COLOR_BG)
        form.pack(fill="both", expand=True, padx=20, pady=15)

        for key, label in fields:
            style.make_label(form, label).pack(pady=(10, 2), anchor="w")
            entry = style.make_entry(form, width=28)
            entry.pack(fill="x")
            self.entries[key] = entry

        scroll.enable_mousewheel()

        self.update_idletasks()
        width = max(self.winfo_reqwidth(), 360)
        height = min(self.winfo_reqheight(), int(self.winfo_screenheight() * 0.85))
        ref = parent.winfo_toplevel()
        px = ref.winfo_rootx() + (ref.winfo_width() // 2) - (width // 2)
        py = ref.winfo_rooty() + (ref.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{px}+{py}")

    def _save(self):
        code = self.entries["code"].get().strip()
        name = self.entries["name"].get().strip()
        unit = self.entries["unit"].get().strip()

        if not code or not name:
            dialogs.show_error(self, "Missing Info", "Item code and name are required.")
            return

        try:
            unit_rate = float(self.entries["unit_rate"].get())
            stock_qty = float(self.entries["stock_qty"].get() or 0)
        except ValueError:
            dialogs.show_error(self, "Invalid Number", "Rate and stock quantity must be numbers.")
            return

        try:
            database.add_item(Item(name=name, code=code, unit=unit, unit_rate=unit_rate, stock_qty=stock_qty))
        except database.DuplicateItemCodeError:
            dialogs.show_error(
                self, "Item Code Already Used",
                f"'{code}' is already in the system. Please enter a different item code."
            )
            return  # dialog stays open, fields untouched — just fix the code and retry
        except Exception as e:
            dialogs.show_error(
                self, "Could Not Save Item",
                f"The item was not saved because of an unexpected problem.\n\nError: {e}"
            )
            return  # keep the form open so the typed details aren't lost

        self.on_saved()
        self.destroy()