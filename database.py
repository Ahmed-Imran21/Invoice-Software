"""
database.py
The only file in this project that talks to SQL. Every function opens
its own short-lived connection and ALWAYS closes it via try/finally —
even on error — so a failed operation (like a duplicate item code)
can never leave the database file locked for the next operation.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from config import DATABASE_PATH, STARTING_INVOICE_NUMBER
from models import Item, Invoice, InvoiceItem


def get_connection():
    # timeout=10 makes sqlite wait up to 10s for a lock to clear instead
    # of failing instantly if something else briefly holds it.
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL mode lets reads happen while a write is in progress, which
    # avoids most "database is locked" errors entirely.
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
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number   INTEGER UNIQUE NOT NULL,
                customer_name    TEXT,
                customer_address TEXT,
                customer_contact TEXT,
                invoice_date     TEXT NOT NULL,
                gross_total      REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                tax_percent      REAL DEFAULT 0,
                net_total        REAL NOT NULL,
                paid_amount      REAL DEFAULT 0,
                balance          REAL NOT NULL,
                prepared_by      TEXT
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
    """Raised when trying to add an item with a code that already exists."""
    pass


def add_item(item: Item) -> int:
    """Inserts a new item. Returns the new item_id. Raises
    DuplicateItemCodeError if the code is already used — the caller
    can catch this specifically and ask the user to re-enter."""
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
    """Adds/subtracts stock and logs the change. Always closes its
    connection, whether it succeeds or raises ValueError."""
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
    """Returns a summary of every saved invoice (customer, contact,
    totals, date) as plain dicts, newest first. Used by the invoice
    history screen. Doesn't include line items — open the saved PDF
    for the full breakdown."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM invoices ORDER BY invoice_number DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_invoice(invoice: Invoice) -> int:
    """Saves the invoice + line items and deducts stock, all in one
    transaction. Connection always closes via finally, success or not."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            invoice_number = invoice.invoice_number or get_next_invoice_number()

            cur.execute("""
                INSERT INTO invoices (
                    invoice_number, customer_name, customer_address, customer_contact,
                    invoice_date, gross_total, discount_percent, tax_percent,
                    net_total, paid_amount, balance, prepared_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_number, invoice.customer_name, invoice.customer_address,
                invoice.customer_contact, invoice.invoice_date, invoice.gross_total,
                invoice.discount_percent, invoice.tax_percent, invoice.net_total,
                invoice.paid_amount, invoice.balance, invoice.prepared_by
            ))
            invoice_id = cur.lastrowid
            invoice.invoice_number = invoice_number

            for line in invoice.items:
                cur.execute("""
                    INSERT INTO invoice_items (
                        invoice_id, item_id, item_name, code, qty, unit_rate, line_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id, line.item_id, line.item_name, line.code,
                    line.qty, line.unit_rate, line.line_total
                ))

                new_qty_row = cur.execute(
                    "SELECT stock_qty FROM items WHERE item_id = ?", (line.item_id,)
                ).fetchone()
                if new_qty_row is None or new_qty_row["stock_qty"] < line.qty:
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

            conn.commit()
            return invoice_id

        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()