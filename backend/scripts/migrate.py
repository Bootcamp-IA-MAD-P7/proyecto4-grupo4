"""Phase-7 database migration script.

Adds the three MLOps columns introduced in T-7.1 to an *existing*
``predictions`` table.  Use this against any environment where the table
was already created (e.g. the EC2 production database) because SQLAlchemy's
``create_all`` does **not** ALTER existing tables.

Usage (run once per environment)::

    DATABASE_URL=postgresql://user:pass@host:5432/db python scripts/migrate.py

Exit codes:
    0 — migration applied successfully (or columns already present).
    1 — unexpected error; details printed to stderr.
"""

from __future__ import annotations

import sys

from sqlalchemy import text

# Import engine factory so we share the same DATABASE_URL logic.
from app.database import get_engine


_MIGRATION_SQL = """
ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS predicted_multiple DOUBLE PRECISION NOT NULL DEFAULT 0.0;

ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS actual_multiple DOUBLE PRECISION;

ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS model_version VARCHAR(50) NOT NULL DEFAULT 'prod';
"""


def run_migration() -> None:
    """Execute the ALTER TABLE statements against the configured database."""
    engine = get_engine()
    with engine.begin() as conn:
        for statement in _MIGRATION_SQL.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
    print("[migrate] Phase-7 columns applied (or already present). Done.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as exc:
        print(f"[migrate] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
