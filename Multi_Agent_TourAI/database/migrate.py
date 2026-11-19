import os
import sys
from pathlib import Path
import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_migration_database_url() -> str:
    url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRESQL_URL")
    if not url:
        raise ValueError("MIGRATION_DATABASE_URL or POSTGRESQL_URL is missing in environment.")
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def run_migration(migration_file: str) -> None:
    path = Path(migration_file)
    if not path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")

    sql = path.read_text(encoding="utf-8")
    db_url = get_migration_database_url()
    print(f"Applying migration: {migration_file} ...")

    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print(f"Migration {migration_file} successfully applied!")


def setup_langgraph_schemas() -> None:
    """Explicitly initializes LangGraph checkpointer and store schemas using migration credentials."""
    from Multi_Agent_TourAI.memory.checkpointer import get_checkpointer
    from Multi_Agent_TourAI.memory.store import get_store
    print("Verifying LangGraph checkpoint and store schema setup with admin credentials...")
    get_checkpointer(run_setup=True)
    get_store(run_setup=True)
    print("LangGraph schemas successfully verified!")


if __name__ == "__main__":
    file_to_run = sys.argv[1] if len(sys.argv) > 1 else "migrations/002_create_application_auth.sql"
    if file_to_run == "--setup-langgraph":
        setup_langgraph_schemas()
    else:
        run_migration(file_to_run)
