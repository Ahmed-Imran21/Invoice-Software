"""
backup.py
Silently backs up the database once per day so a corrupted file or an
accidental mistake never means losing the entire stock/invoice
history. Runs automatically every time the app starts — the user
never has to think about it.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from config import DATABASE_PATH, BACKUP_DIR, BACKUP_RETENTION_DAYS


def _todays_backup_path() -> Path:
    return BACKUP_DIR / f"inventory_backup_{date.today().isoformat()}.db"


def run_daily_backup():
    """Creates today's backup if one doesn't already exist, then removes
    backups older than BACKUP_RETENTION_DAYS. Safe to call every time
    the app starts — does nothing extra if today's backup already exists."""
    if not DATABASE_PATH.exists():
        return  # first-ever run, nothing to back up yet

    target = _todays_backup_path()
    if not target.exists():
        _backup_now(target)

    _cleanup_old_backups()


def _backup_now(dest_path: Path):
    """Uses SQLite's own backup API rather than copying the .db file
    directly. A plain file copy can grab an inconsistent snapshot while
    the app is using WAL mode; this stays safe and consistent."""
    src = sqlite3.connect(DATABASE_PATH)
    dst = sqlite3.connect(dest_path)
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
        src.close()


def _cleanup_old_backups():
    cutoff = date.today() - timedelta(days=BACKUP_RETENTION_DAYS)
    for backup_file in BACKUP_DIR.glob("inventory_backup_*.db"):
        date_part = backup_file.stem.replace("inventory_backup_", "")
        try:
            backup_date = date.fromisoformat(date_part)
        except ValueError:
            continue  # not one of our files — leave it alone
        if backup_date < cutoff:
            backup_file.unlink(missing_ok=True)


def list_backups():
    """Returns backup files, newest first. Not used yet, but handy if
    a 'restore from backup' option gets added later."""
    if not BACKUP_DIR.exists():
        return []
    return sorted(BACKUP_DIR.glob("inventory_backup_*.db"), reverse=True)