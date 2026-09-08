"""
models.py
Simple data containers matching the database tables. No logic here —
just structured objects so other files can pass around Item/Invoice
data without juggling raw tuples or dicts.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Item:
    name: str
    code: str
    unit: str
    unit_rate: float
    stock_qty: float = 0.0
    low_stock_alert: float = 0.0
    item_id: Optional[int] = None  # set once saved to the database


@dataclass
class InvoiceItem:
    item_id: int
    item_name: str      # snapshot — stays accurate even if the item is renamed later
    code: str            # snapshot
    qty: float
    unit_rate: float     # snapshot — stays accurate even if price changes later
    invoice_item_id: Optional[int] = None

    @property
    def line_total(self) -> float:
        return round(self.qty * self.unit_rate, 2)


@dataclass
class Invoice:
    customer_name: str
    customer_address: str
    customer_contact: str
    invoice_date: str          # e.g. "2026-09-08"
    items: List[InvoiceItem] = field(default_factory=list)
    discount_percent: float = 0.0
    tax_percent: float = 0.0
    paid_amount: float = 0.0
    prepared_by: str = ""
    invoice_number: Optional[int] = None
    invoice_id: Optional[int] = None

    @property
    def gross_total(self) -> float:
        return round(sum(item.line_total for item in self.items), 2)

    @property
    def discount_amount(self) -> float:
        return round(self.gross_total * (self.discount_percent / 100), 2)

    @property
    def taxable_amount(self) -> float:
        # discount applied first, then tax on the discounted amount
        return round(self.gross_total - self.discount_amount, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.taxable_amount * (self.tax_percent / 100), 2)

    @property
    def net_total(self) -> float:
        return round(self.taxable_amount + self.tax_amount, 2)

    @property
    def balance(self) -> float:
        return round(self.net_total - self.paid_amount, 2)