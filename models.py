"""
models.py
Simple data containers matching the database tables. No logic beyond
the totals math — other files stay SQL-free and calculation-free by
using these.
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
    item_id: Optional[int] = None


@dataclass
class InvoiceItem:
    item_id: int
    item_name: str
    code: str
    qty: float
    unit_rate: float
    invoice_item_id: Optional[int] = None

    @property
    def line_total(self) -> float:
        return round(self.qty * self.unit_rate, 2)


@dataclass
class Customer:
    """A customer tracked for the khata (running credit) ledger.
    Matched by contact number — not name — since names get typo'd
    or shortened, but a phone number is a reliable repeat-match."""
    name: str
    contact: str
    current_balance: float = 0.0
    customer_id: Optional[int] = None


@dataclass
class Invoice:
    customer_name: str
    customer_address: str
    customer_contact: str
    invoice_date: str
    items: List[InvoiceItem] = field(default_factory=list)
    discount_percent: float = 0.0
    tax_percent: float = 0.0
    paid_amount: float = 0.0
    prepared_by: str = ""
    invoice_number: Optional[int] = None
    invoice_id: Optional[int] = None

    # Khata (ledger) fields — resolved and snapshotted by database.save_invoice()
    customer_id: Optional[int] = None
    prev_balance: float = 0.0  # what this customer owed BEFORE this invoice

    @property
    def gross_total(self) -> float:
        return round(sum(item.line_total for item in self.items), 2)

    @property
    def discount_amount(self) -> float:
        return round(self.gross_total * (self.discount_percent / 100), 2)

    @property
    def taxable_amount(self) -> float:
        return round(self.gross_total - self.discount_amount, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.taxable_amount * (self.tax_percent / 100), 2)

    @property
    def net_total(self) -> float:
        return round(self.taxable_amount + self.tax_amount, 2)

    @property
    def invoice_balance(self) -> float:
        """This invoice's own unpaid amount — Net Total minus what was
        paid right now. Does NOT include older unpaid invoices."""
        return round(self.net_total - self.paid_amount, 2)

    @property
    def balance(self) -> float:
        """Kept as an alias for invoice_balance for backward compatibility."""
        return self.invoice_balance

    @property
    def crnt_balance(self) -> float:
        """The customer's new running total after this invoice — what
        they owed before, plus whatever's unpaid on this invoice.
        This becomes their prev_balance next time they buy something."""
        return round(self.prev_balance + self.invoice_balance, 2)