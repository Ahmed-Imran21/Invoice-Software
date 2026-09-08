"""
invoice_generator.py
Builds the printable invoice PDF, styled after the improved layout we
mocked up, then saves a copy and opens it (which lets the user print
via their normal Windows print dialog).
"""

import os
import subprocess
import sys

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

    # ---------- Header ----------
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

    # ---------- Invoice info ----------
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Invoice #: {invoice.invoice_number}")
    c.drawString(width / 2, y, f"Date: {invoice.invoice_date}")
    y -= 5 * mm
    c.drawString(margin, y, f"Customer: {invoice.customer_name or '-'}")
    c.drawString(width / 2, y, f"Contact: {invoice.customer_contact or '-'}")
    y -= 4 * mm
    c.line(margin, y, width - margin, y)
    y -= 8 * mm

    # ---------- Item table header ----------
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

    # ---------- Item rows ----------
    c.setFont("Helvetica", 9)
    for line in invoice.items:
        c.drawString(col_item, y, line.item_name[:32])
        c.drawRightString(col_qty + 12 * mm, y, f"{line.qty:g}")
        c.drawRightString(col_rate + 12 * mm, y, f"{line.unit_rate:.2f}")
        c.drawRightString(col_total + 18 * mm, y, f"{line.line_total:,.2f}")
        y -= 6 * mm

        if y < 50 * mm:  # start a new page if we run out of room
            c.showPage()
            y = height - margin

    y -= 3 * mm
    c.line(margin, y, width - margin, y)
    y -= 8 * mm

    # ---------- Totals box ----------
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

    # ---------- Footer ----------
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(margin, y, "Items only replaceable/returnable within 7 days with original bill.")

    c.save()
    return filepath


def open_for_printing(filepath: str):
    """Opens the PDF in the user's default viewer so they can print it from there."""
    if sys.platform == "win32":
        os.startfile(filepath, "print")  # sends straight to the default printer
    else:
        subprocess.run(["xdg-open", filepath])  # fallback for testing on Linux/Mac


def generate_and_print(invoice: Invoice) -> str:
    """Convenience function: build the PDF, save it, and send it to print."""
    filepath = generate_invoice_pdf(invoice)
    open_for_printing(filepath)
    return filepath