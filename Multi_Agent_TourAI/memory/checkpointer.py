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
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


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


# Persistent Short-Term Memory & State Caching (Session Checkpointer)
@log_execution
def get_checkpointer() -> PostgresSaver:
    """
    Initializes and sets up the PostgresSaver checkpointer for LangGraph.
    
    Provides:
      - Persistent thread-level short-term memory.
      - Step-by-step intermediate state caching across multi-agent nodes.
      - Error recovery and workflow resumption without duplicate API calls.
    """
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




# In LangGraph, PostgresSaver acts as both Short-Term Memory and a Durable State Cache:
#
# 1. Thread-Level Short-Term Memory:
#    - Saves entire conversation history ('messages') and state ('TravelState') per 'thread_id'.
#    - Preserves context across multi-turn user conversations.
#
# 2. State & Intermediate Results Caching (Key Use Cases):
#    - Case A (Intermediate Outputs Cache): When an agent finishes (e.g. flight_agent, hotel_agent),
#      its output is cached in PostgreSQL state. Next agents read this cache without re-fetching APIs.
#    - Case B (Fault Recovery & Resumption): If a downstream agent fails (e.g. weather API error),
#      the workflow resumes from the last saved checkpoint instead of re-running earlier agents.
#      This saves significant LLM tokens and external API credits.
#    - Case C (Durable Session Cache): Because checkpoints live in PostgreSQL, cached sessions
#      survive server restarts and crashes.