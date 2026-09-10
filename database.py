"""
database.py
The only file in this project that talks to SQL. Every function opens
its own connection and ALWAYS closes it via try/finally, even on
error, so a failed operation never leaves the database locked.

Includes the "khata" (running credit ledger) system: customers are
matched by contact number, and every invoice snapshots what they owed
before (prev_balance) and what they owe now (crnt_balance), while the
customers table always holds their live current_balance.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from config import DATABASE_PATH, STARTING_INVOICE_NUMBER
from models import Item, Invoice, InvoiceItem, Customer


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                code            TEXT UNIQUE NOT NULL,
                name            TEXT NOT NULL,
                unit            TEXT,
                unit_rate       REAL NOT NULL,
                stock_qty       REAL NOT NULL DEFAULT 0,
                low_stock_alert REAL DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_log (
                log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     INTEGER NOT NULL,
                change_qty  REAL NOT NULL,
                reason      TEXT,
                timestamp   TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                contact         TEXT UNIQUE NOT NULL,
                current_balance REAL NOT NULL DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id  INTEGER NOT NULL,
                amount       REAL NOT NULL,
                payment_date TEXT NOT NULL,
                note         TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number   INTEGER UNIQUE NOT NULL,
                customer_id      INTEGER,
                customer_name    TEXT,
                customer_address TEXT,
                customer_contact TEXT,
                invoice_date     TEXT NOT NULL,
                gross_total      REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                tax_percent      REAL DEFAULT 0,
                net_total        REAL NOT NULL,
                paid_amount      REAL DEFAULT 0,
                prev_balance     REAL NOT NULL DEFAULT 0,
                invoice_balance  REAL NOT NULL DEFAULT 0,
                crnt_balance     REAL NOT NULL DEFAULT 0,
                prepared_by      TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                invoice_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id      INTEGER NOT NULL,
                item_id         INTEGER NOT NULL,
                item_name       TEXT NOT NULL,
                code            TEXT NOT NULL,
                qty             REAL NOT NULL,
                unit_rate       REAL NOT NULL,
                line_total      REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        """)

        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------
# ITEMS
# ---------------------------------------------------------------------

class DuplicateItemCodeError(Exception):
    pass


def add_item(item: Item) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO items (code, name, unit, unit_rate, stock_qty, low_stock_alert)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item.code, item.name, item.unit, item.unit_rate, item.stock_qty, item.low_stock_alert))
        except sqlite3.IntegrityError:
            raise DuplicateItemCodeError(f"Item code '{item.code}' already exists.")
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_all_items() -> List[Item]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM items ORDER BY name").fetchall()
        return [
            Item(
                item_id=row["item_id"], code=row["code"], name=row["name"],
                unit=row["unit"], unit_rate=row["unit_rate"],
                stock_qty=row["stock_qty"], low_stock_alert=row["low_stock_alert"]
            )
            for row in rows
        ]
    finally:
        conn.close()


def get_item_by_code(code: str) -> Optional[Item]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM items WHERE code = ?", (code,)).fetchone()
        if row is None:
            return None
        return Item(
            item_id=row["item_id"], code=row["code"], name=row["name"],
            unit=row["unit"], unit_rate=row["unit_rate"],
            stock_qty=row["stock_qty"], low_stock_alert=row["low_stock_alert"]
        )
    finally:
        conn.close()


def adjust_stock(item_id: int, change_qty: float, reason: str = "Manual Adjustment"):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT stock_qty FROM items WHERE item_id = ?", (item_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"No item found with item_id={item_id}")

        new_qty = row["stock_qty"] + change_qty
        if new_qty < 0:
            raise ValueError("This change would make stock negative — not allowed.")

        cur.execute("UPDATE items SET stock_qty = ? WHERE item_id = ?", (new_qty, item_id))
        cur.execute("""
            INSERT INTO stock_log (item_id, change_qty, reason, timestamp)
            VALUES (?, ?, ?, ?)
        """, (item_id, change_qty, reason, datetime.now().isoformat(timespec="seconds")))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------
# CUSTOMERS / KHATA LEDGER
# ---------------------------------------------------------------------

def get_customer_by_contact(contact: str) -> Optional[Customer]:
    contact = (contact or "").strip()
    if not contact:
        return None
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM customers WHERE contact = ?", (contact,)).fetchone()
        if row is None:
            return None
        return Customer(
            customer_id=row["customer_id"], name=row["name"],
            contact=row["contact"], current_balance=row["current_balance"]
        )
    finally:
        conn.close()


def get_all_customers() -> List[Customer]:
    """Highest balance (most owed) first, so the owner sees who to
    follow up with at a glance."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM customers ORDER BY current_balance DESC, name"
        ).fetchall()
        return [
            Customer(
                customer_id=row["customer_id"], name=row["name"],
                contact=row["contact"], current_balance=row["current_balance"]
            )
            for row in rows
        ]
    finally:
        conn.close()


def record_payment(customer_id: int, amount: float, note: str = "") -> float:
    """Records a payment against a customer's balance — settling khata
    dues without a new purchase. Returns the customer's new balance."""
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT current_balance FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Customer not found.")

        new_balance = round(row["current_balance"] - amount, 2)
        cur.execute(
            "UPDATE customers SET current_balance = ? WHERE customer_id = ?",
            (new_balance, customer_id)
        )
        cur.execute("""
            INSERT INTO payments (customer_id, amount, payment_date, note)
            VALUES (?, ?, ?, ?)
        """, (customer_id, amount, datetime.now().isoformat(timespec="seconds"), note))

        conn.commit()
        return new_balance
    finally:
        conn.close()


# ---------------------------------------------------------------------
# INVOICES
# ---------------------------------------------------------------------

def get_next_invoice_number() -> int:
    conn = get_connection()
    try:
        row = conn.execute("SELECT MAX(invoice_number) AS max_num FROM invoices").fetchone()
        if row["max_num"] is None:
            return STARTING_INVOICE_NUMBER
        return row["max_num"] + 1
    finally:
        conn.close()


def get_all_invoices() -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM invoices ORDER BY invoice_number DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_invoice(invoice: Invoice) -> int:
    """
    Saves the invoice, resolves/updates the customer's khata ledger,
    and deducts stock — all in ONE transaction. If anything fails,
    everything rolls back: no half-saved invoice, no stock touched,
    no customer balance changed.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            # ---- Resolve customer + previous balance (khata) ----
            customer_id = None
            prev_balance = 0.0
            contact = (invoice.customer_contact or "").strip()

            if contact:
                row = cur.execute(
                    "SELECT customer_id, name, current_balance FROM customers WHERE contact = ?",
                    (contact,)
                ).fetchone()

                if row is None:
                    cur.execute(
                        "INSERT INTO customers (name, contact, current_balance) VALUES (?, ?, 0)",
                        (invoice.customer_name or "Walk-in Customer", contact)
                    )
                    customer_id = cur.lastrowid
                    prev_balance = 0.0
                else:
                    customer_id = row["customer_id"]
                    prev_balance = row["current_balance"]
                    if invoice.customer_name and invoice.customer_name != row["name"]:
                        cur.execute(
                            "UPDATE customers SET name = ? WHERE customer_id = ?",
                            (invoice.customer_name, customer_id)
                        )

            invoice.customer_id = customer_id
            invoice.prev_balance = prev_balance

            # ---- Invoice number ----
            row = cur.execute("SELECT MAX(invoice_number) AS max_num FROM invoices").fetchone()
            invoice_number = invoice.invoice_number or (
                (row["max_num"] + 1) if row["max_num"] is not None else STARTING_INVOICE_NUMBER
            )
            invoice.invoice_number = invoice_number

            invoice_balance = invoice.invoice_balance
            crnt_balance = round(prev_balance + invoice_balance, 2)

            # ---- Save the invoice itself ----
            cur.execute("""
                INSERT INTO invoices (
                    invoice_number, customer_id, customer_name, customer_address, customer_contact,
                    invoice_date, gross_total, discount_percent, tax_percent,
                    net_total, paid_amount, prev_balance, invoice_balance, crnt_balance, prepared_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_number, customer_id, invoice.customer_name, invoice.customer_address,
                invoice.customer_contact, invoice.invoice_date, invoice.gross_total,
                invoice.discount_percent, invoice.tax_percent, invoice.net_total,
                invoice.paid_amount, prev_balance, invoice_balance, crnt_balance, invoice.prepared_by
            ))
            invoice_id = cur.lastrowid

            # ---- Line items + stock deduction ----
            for line in invoice.items:
                cur.execute("""
                    INSERT INTO invoice_items (
                        invoice_id, item_id, item_name, code, qty, unit_rate, line_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id, line.item_id, line.item_name, line.code,
                    line.qty, line.unit_rate, line.line_total
                ))

                stock_row = cur.execute(
                    "SELECT stock_qty FROM items WHERE item_id = ?", (line.item_id,)
                ).fetchone()
                if stock_row is None or stock_row["stock_qty"] < line.qty:
                    raise ValueError(f"Not enough stock for '{line.item_name}'.")

                cur.execute(
                    "UPDATE items SET stock_qty = stock_qty - ? WHERE item_id = ?",
                    (line.qty, line.item_id)
                )
                cur.execute("""
                    INSERT INTO stock_log (item_id, change_qty, reason, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    line.item_id, -line.qty, f"Invoice #{invoice_number}",
                    datetime.now().isoformat(timespec="seconds")
                ))

            # ---- Update the customer's running balance (khata) ----
            if customer_id is not None:
                cur.execute(
                    "UPDATE customers SET current_balance = ? WHERE customer_id = ?",
                    (crnt_balance, customer_id)
                )

            conn.commit()
            return invoice_id

        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()