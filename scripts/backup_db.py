"""Cross-platform automated PostgreSQL backup script for CDMS.

Works on Windows, Linux, and macOS.
Usage:
    python scripts/backup_db.py
"""

import gzip
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Read environment variables
DB_HOST = os.getenv("POSTGRES_SERVER", "127.0.0.1")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "cdms_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cdms_password")
DB_NAME = os.getenv("POSTGRES_DB", "cdms_db")
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))

timestamp = time.strftime("%Y%m%d_%H%M%S")
backup_sql = BACKUP_DIR / f"cdms_backup_{timestamp}.sql"
backup_gz = BACKUP_DIR / f"cdms_backup_{timestamp}.sql.gz"


def run_backup() -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting CDMS backup for '{DB_NAME}' on {DB_HOST}:{DB_PORT}...")
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    cmd = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", str(DB_PORT),
        "-U", DB_USER,
        "-d", DB_NAME,
        "--clean",
        "--if-exists",
        "-f", str(backup_sql),
    ]

    try:
        subprocess.run(cmd, env=env, check=True)
    except FileNotFoundError:
        print("Error: pg_dump utility not found in PATH. Please install PostgreSQL client tools.")
        return
    except subprocess.CalledProcessError as exc:
        print(f"Error: pg_dump failed with exit code {exc.returncode}")
        if backup_sql.exists():
            backup_sql.unlink()
        return

    # Compress with gzip
    with open(backup_sql, "rb") as f_in, gzip.open(backup_gz, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    backup_sql.unlink()

    file_size_kb = round(backup_gz.stat().st_size / 1024, 2)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS: Backup created at {backup_gz} ({file_size_kb} KB)")

    # Prune old backups
    now = time.time()
    cutoff = now - (RETENTION_DAYS * 86400)
    pruned_count = 0
    for f in BACKUP_DIR.glob("cdms_backup_*.sql.gz"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            pruned_count += 1
    if pruned_count > 0:
        print(f"Pruned {pruned_count} old backup(s) older than {RETENTION_DAYS} days.")


if __name__ == "__main__":
    run_backup()
