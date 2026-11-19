import os
from urllib.parse import urlparse
import psycopg
import certifi
from dotenv import load_dotenv
from psycopg.rows import dict_row
from langgraph.store.postgres import PostgresStore
from Multi_Agent_TourAI.database.connection import get_connection_pool, get_db_connection
from Multi_Agent_TourAI.memory.checkpointer import get_databaseUrl
from Multi_Agent_TourAI.utils import get_logger, log_execution

# Initialize logger for Long-Term Memory
logger = get_logger(__name__)
load_dotenv()

# Environment & SSL Certificate Setup (Windows SSL Fix)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Long-Term Memory (Cross-Session User Store)
@log_execution
def get_store(run_setup: bool = False) -> PostgresStore:
    """
    Initializes PostgresStore for LangGraph Long-Term Memory using the centralized connection pool.
    
    Provides:
      - Permanent storage for user preferences and custom travel profiles.
      - Cross-thread retrieval using namespaces like ("users", user_id).
      - Concurrent multi-user safe memory access via pooled connections.

    When run_setup=True (used strictly by migrations/admin scripts), runs store.setup().
    In normal runtime, operates with DML permissions only without attempting DDL schema alterations.
    """
    pool = get_connection_pool()
    store = PostgresStore(pool)
    if run_setup:
        store.setup()
        logger.info("Long-Term Store DDL setup verified via admin context.")
    else:
        logger.info("Long-Term Store initialized with connection pool.")

    return store
__all__ = ["get_store"]


# Unlike Checkpointer (which is short-term and tied strictly to one 'thread_id'):
#
# 1. Cross-Session & Cross-Thread Scope:
#    - Stored under hierarchical namespaces: (namespace, key) -> e.g., ("users", user_id), "preferences".
#    - Accessible across any conversation or session started by this user.
#
# 2. Permanent User Profiles & Facts:
#    - Stores user travel preferences (e.g., favorite airlines, budget level, dietary needs).
#    - Remembers past trip history and past recommendations.
#
# 3. Persistent Knowledge Base:
#    - Persisted into PostgreSQL 'store' table so preferences are retained indefinitely.