"""
backup.py
Silently backs up the database once per day so a corrupted file or an
accidental mistake never means losing the entire stock/invoice
history. Runs automatically every time the app starts — the user
never has to think about it.
"""

import sqlite3
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

from config import DATABASE_PATH, BACKUP_DIR, BACKUP_RETENTION_DAYS

# Backup failures are written here rather than shown on screen: this runs
# at startup, before the window exists, and a backup problem shouldn't stop
# the shop from invoicing. But it must not vanish either — if backups have
# been quietly failing for weeks, this file is how anyone finds out.
ERROR_LOG_PATH = DATABASE_PATH.parent / "backup_errors.log"


def _log_error(what: str, exc: BaseException):
    try:
        ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(
                f"[{datetime.now().isoformat(timespec='seconds')}] {what}: "
                f"{type(exc).__name__}: {exc}\n"
            )
            fh.write(
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            )
            fh.write("\n")
    except Exception:
        # Logging the failure must never itself break startup.
        pass


def _todays_backup_path() -> Path:
    return BACKUP_DIR / f"inventory_backup_{date.today().isoformat()}.db"


def run_daily_backup():
    """Creates today's backup if one doesn't already exist, then removes
    backups older than BACKUP_RETENTION_DAYS. Safe to call every time
    the app starts — does nothing extra if today's backup already exists.

    Never raises: this is called during startup, so any failure is logged
    to ERROR_LOG_PATH and swallowed rather than preventing the app from
    opening."""
    if not DATABASE_PATH.exists():
        return  # first-ever run, nothing to back up yet

    try:
        target = _todays_backup_path()
        if not target.exists():
            _backup_now(target)
    except Exception as e:
        _log_error("Daily backup failed", e)

    try:
        _cleanup_old_backups()
    except Exception as e:
        _log_error("Pruning old backups failed", e)


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
            try:
                backup_file.unlink(missing_ok=True)
            except OSError as e:
                # One undeletable file (locked, permissions) shouldn't stop
                # the rest from being pruned — note it and carry on.
                _log_error(f"Could not delete old backup {backup_file.name}", e)


def list_backups():
    """Returns backup files, newest first. Not used yet, but handy if
    a 'restore from backup' option gets added later."""
    if not BACKUP_DIR.exists():
        return []
    return sorted(BACKUP_DIR.glob("inventory_backup_*.db"), reverse=True)