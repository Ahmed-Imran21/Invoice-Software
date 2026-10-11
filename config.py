"""
config.py
Central place for app-wide settings: business info, file paths, and defaults.
Edit this file to rebrand the invoice or change how it behaves — no other
file should need touching for these kinds of changes.
"""

import sys
from pathlib import Path

# ---------- Business info (shown on every invoice) ----------
# Single source of truth for the invoice header — invoice_generator.py reads
# these, so rebranding never means touching PDF layout code.
COMPANY_NAME = "ITTEFAQ PLASTIC INDUSTRIES"
COMPANY_ADDRESS = "PLOT NO 261, SARAN STOP, KAHUTA ROAD, MODEL TOWN ISLAMABAD"
COMPANY_CONTACT = "M IMRAN 0300-8514000, 0321-5178240"

# ---------- File paths ----------
# When PyInstaller runs a --onefile build, __file__ resolves inside the
# temporary _MEIPASS extraction folder — a new, throwaway directory every
# launch. Writable data (database/invoices/backups) must live next to the
# actual .exe instead, or it would silently vanish between runs.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    ASSETS_DIR = Path(sys._MEIPASS) / "assets"
else:
    BASE_DIR = Path(__file__).resolve().parent
    ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "inventory.db"
INVOICES_DIR = DATA_DIR / "invoices"
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
# APP_NAME is the product; APP_TITLE is what the window titlebar shows.
# They're kept separate because the home screen prints COMPANY_NAME large
# and APP_NAME underneath it — the combined string is too wide to render
# as a single heading at the app's font scale.
APP_NAME = "Stock & Invoice Manager"
APP_TITLE = f"{COMPANY_NAME} - {APP_NAME}"