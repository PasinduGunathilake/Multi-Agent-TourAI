import os
from urllib.parse import urlparse
import psycopg
import certifi
from dotenv import load_dotenv
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from Multi_Agent_TourAI.database.connection import (
    get_connection_pool,
    get_db_connection,
    get_database_url as get_db_url_normalized,
)
from Multi_Agent_TourAI.utils import get_logger, log_execution

logger = get_logger(__name__)

load_dotenv()
# Environment & SSL Certificate Setup (Windows SSL Fix)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


# Retrieves and formats the PostgreSQL database URL with SSL mode (preserved for backward compatibility).
def get_databaseUrl() -> str:
    return get_db_url_normalized()


# Persistent Short-Term Memory & State Caching (Session Checkpointer)
@log_execution
def get_checkpointer(run_setup: bool = False) -> PostgresSaver:
    """
    Initializes the PostgresSaver checkpointer for LangGraph using the centralized connection pool.
    
    Provides:
      - Thread-safe, non-blocking checkpointer access across concurrent multi-user requests.
      - Persistent thread-level short-term memory.
      - Step-by-step intermediate state caching across multi-agent nodes.
      - Error recovery and workflow resumption without duplicate API calls.

    When run_setup=True (used strictly by migrations/admin scripts), runs checkpointer.setup().
    In normal runtime, operates with DML permissions only without attempting DDL schema alterations.
    """
    pool = get_connection_pool()
    checkpointer = PostgresSaver(pool)

    if run_setup:
        checkpointer.setup()
        logger.info("PostgreSQL Checkpointer DDL setup verified via admin context.")
    else:
        logger.info("PostgreSQL Checkpointer initialized with connection pool.")

    return checkpointer


def delete_thread_checkpoints(thread_id: str) -> bool:
    """
    Deletes all LangGraph checkpoints associated with a given thread_id from PostgreSQL
    using the centralized connection pool.
    """
    if not thread_id:
        return False
    try:
        with get_db_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
                cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
                cur.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
                logger.info(f"Purged all checkpoints for thread_id='{thread_id}' from PostgreSQL.")
                return True
    except Exception as e:
        logger.error(f"Failed to delete checkpoints for thread_id='{thread_id}': {e}", exc_info=True)
        return False
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