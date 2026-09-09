"""
invoice_generator.py
Builds the printable invoice PDF, saves a copy, and sends it to print.
Errors are raised with clear messages instead of failing silently, so
the UI layer can show the user exactly what went wrong.
"""

import os
import subprocess
import sys
import shutil

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from config import COMPANY_NAME, COMPANY_ADDRESS, COMPANY_CONTACT, INVOICES_DIR
from models import Invoice


def generate_invoice_pdf(invoice: Invoice) -> str:
    """Builds the PDF file and returns its file path."""
    filename = f"invoice_{invoice.invoice_number}.pdf"
    filepath = os.path.join(INVOICES_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=A5)
    width, height = A5
    margin = 12 * mm
    y = height - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, COMPANY_NAME)
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, COMPANY_ADDRESS)
    y -= 5 * mm
    c.drawCentredString(width / 2, y, COMPANY_CONTACT)
    y -= 4 * mm
    c.line(margin, y, width - margin, y)
    y -= 8 * mm

    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Invoice #: {invoice.invoice_number}")
    c.drawString(width / 2, y, f"Date: {invoice.invoice_date}")
    y -= 5 * mm
    c.drawString(margin, y, f"Customer: {invoice.customer_name or '-'}")
    c.drawString(width / 2, y, f"Contact: {invoice.customer_contact or '-'}")
    y -= 4 * mm
    c.line(margin, y, width - margin, y)
    y -= 8 * mm

    col_item = margin
    col_qty = width - margin - 55 * mm
    col_rate = width - margin - 38 * mm
    col_total = width - margin - 18 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_item, y, "Item")
    c.drawRightString(col_qty + 12 * mm, y, "Qty")
    c.drawRightString(col_rate + 12 * mm, y, "Rate")
    c.drawRightString(col_total + 18 * mm, y, "Total")
    y -= 3 * mm
    c.line(margin, y, width - margin, y)
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    for line in invoice.items:
        c.drawString(col_item, y, line.item_name[:32])
        c.drawRightString(col_qty + 12 * mm, y, f"{line.qty:g}")
        c.drawRightString(col_rate + 12 * mm, y, f"{line.unit_rate:.2f}")
        c.drawRightString(col_total + 18 * mm, y, f"{line.line_total:,.2f}")
        y -= 6 * mm
        if y < 50 * mm:
            c.showPage()
            y = height - margin

    y -= 3 * mm
    c.line(margin, y, width - margin, y)
    y -= 8 * mm

    totals = [
        ("Gross Total", f"{invoice.gross_total:,.2f}"),
        (f"Discount ({invoice.discount_percent:g}%)", f"-{invoice.discount_amount:,.2f}"),
        (f"Tax ({invoice.tax_percent:g}%)", f"+{invoice.tax_amount:,.2f}"),
    ]
    c.setFont("Helvetica", 9)
    for label, value in totals:
        c.drawString(width - margin - 55 * mm, y, label)
        c.drawRightString(width - margin, y, value)
        y -= 5.5 * mm

    c.line(width - margin - 55 * mm, y, width - margin, y)
    y -= 6 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - margin - 55 * mm, y, "Net Total")
    c.drawRightString(width - margin, y, f"{invoice.net_total:,.2f}")
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    c.drawString(width - margin - 55 * mm, y, "Paid")
    c.drawRightString(width - margin, y, f"{invoice.paid_amount:,.2f}")
    y -= 5.5 * mm

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#c62828"))
    c.drawString(width - margin - 55 * mm, y, "Balance Due")
    c.drawRightString(width - margin, y, f"{invoice.balance:,.2f}")
    c.setFillColor(colors.black)
    y -= 10 * mm

    c.setFont("Helvetica-Oblique", 7)
    c.drawString(margin, y, "Items only replaceable/returnable within 7 days with original bill.")

    c.save()
    return filepath


def get_invoice_pdf_path(invoice_number) -> str:
    """Returns where a given invoice's PDF should be, regardless of
    whether it's been generated yet."""
    return os.path.join(INVOICES_DIR, f"invoice_{invoice_number}.pdf")


def open_pdf_for_viewing(filepath: str):
    """Opens a PDF to look at (not print) — used by the invoice history
    screen. Different from open_for_printing: this never sends the file
    straight to a printer."""
    if sys.platform == "win32":
        os.startfile(filepath)  # no "print" verb — just opens in the default viewer
        return

    opener = shutil.which("xdg-open") or shutil.which("open")
    if opener is None:
        raise RuntimeError(f"No PDF viewer found. The file is at:\n{filepath}")
    subprocess.run([opener, filepath], check=True)


def open_for_printing(filepath: str) -> str:
    """
    Sends the PDF to print (Windows) or opens it in a viewer as a
    fallback (Linux/Mac, used only during development). Returns a
    short status message describing what actually happened, so the
    caller can show it to the user instead of assuming it worked.
    """
    if sys.platform == "win32":
        # Sends straight to the default printer without opening a dialog.
        os.startfile(filepath, "print")
        return "Sent to your default printer."

    # We're on Linux/Mac — this only matters during development testing,
    # since the real deployment target is Windows. There's no direct
    # "print" equivalent here, so we just open the PDF.
    opener = shutil.which("xdg-open") or shutil.which("open")
    if opener is None:
        raise RuntimeError(
            "No PDF viewer command found (xdg-open/open missing). "
            f"The invoice was still saved at:\n{filepath}\n"
            "You can open it manually to check it looks right."
        )
    subprocess.run([opener, filepath], check=True)
    return "Opened the PDF (this dev machine can't send directly to a printer — Windows will)."


def generate_and_print(invoice: Invoice) -> tuple[str, str]:
    """Builds the PDF, saves it, and attempts to print/open it.
    Returns (filepath, status_message)."""
    filepath = generate_invoice_pdf(invoice)
    status = open_for_printing(filepath)
    return filepath, status