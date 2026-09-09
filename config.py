"""
config.py
Central place for app-wide settings: business info, file paths, and defaults.
Edit this file to rebrand the invoice or change how it behaves — no other
file should need touching for these kinds of changes.
"""

from pathlib import Path

# ---------- Business info (shown on every invoice) ----------
COMPANY_NAME = "Your Company Name"
COMPANY_ADDRESS = "Plot No, Street, City"
COMPANY_CONTACT = "0300-0000000"

# ---------- File paths ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "inventory.db"
INVOICES_DIR = DATA_DIR / "invoices"
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icon.ico"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Make sure required folders exist the first time the app runs
DATA_DIR.mkdir(exist_ok=True)
INVOICES_DIR.mkdir(exist_ok=True)

BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
BACKUP_RETENTION_DAYS = 30

# ---------- Invoice defaults ----------
DEFAULT_TAX_PERCENT = 0.0
DEFAULT_DISCOUNT_PERCENT = 0.0
DISCOUNT_APPLIED_BEFORE_TAX = True  # matches our earlier decision: discount first, then tax on the discounted amount

# ---------- Invoice numbering ----------
STARTING_INVOICE_NUMBER = 1  # used only if no invoices exist yet in the database

# ---------- UI ----------
APP_TITLE = "Stock & Invoice Manager"