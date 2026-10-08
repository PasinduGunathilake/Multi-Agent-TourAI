import os
from urllib.parse import urlparse
import psycopg
import certifi
from dotenv import load_dotenv
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from Multi_Agent_TourAI.utils import get_logger, log_execution

logger = get_logger(__name__)

load_dotenv()
# Environment & SSL Certificate Setup (Windows SSL Fix)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUEST_CA_BUNDLE"] = certifi.where()


# Retrieves and formats the PostgreSQL database URL with SSL mode.
def get_databaseUrl() -> str:
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRESQL_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your Render PostgreSQL URL to .env."
        )

    if "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url





# persistance session/ working memory(persistance Short-term memory / Checkpointer)
# saving in postgreserver - Resumability & Fault Tolerance.
@log_execution
def get_checkpointer() -> PostgresSaver:
    # Initializes and sets up the PostgresSaver checkpointer for LangGraph memory.
    database_url = get_databaseUrl()

    parsed = urlparse(database_url)
    logger.info(f"Connecting to PostgreSQL at Host: '{parsed.hostname}', DB: '{parsed.path[1:]}'")

    conn = psycopg.connect(
        database_url,
        autocommit=True,
        row_factory=dict_row
    )

    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    logger.info("PostgreSQL Checkpointer connected & schema setup verified.")

    return checkpointer

