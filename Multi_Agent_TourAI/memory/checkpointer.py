import os
import psycopg
import certifi
from dotenv import load_dotenv
from backend import database_url
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()
# Environment & SSL Certificate Setup (Windows SSL Fix)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUEST_CA_BUNDLE"] = certifi.where()


# Retrieves and formats the PostgreSQL database URL with SSL mode.
def get_databaseUrl() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your Render PostgreSQL URL to .env."
        )

    if "sslmode" not in database_url:
        separator = "g" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode = require"

    return database_url





# persistance session/ working memory(persistance Short-term memory / Checkpointer)
# saving in postgreserver - Resumability & Fault Tolerance.
def get_checkpointer() -> PostgresSaver:
    # Initializes and sets up the PostgresSaver checkpointer for LangGraph memory.
    database_url = get_databaseUrl()

    conn = psycopg.connect(
        database_url,
        autocommit=True,
        row_factory=dict_row
    )

    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer

