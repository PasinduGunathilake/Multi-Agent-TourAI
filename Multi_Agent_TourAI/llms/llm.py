import os
from typing import Optional, Tuple
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from Multi_Agent_TourAI.utils import get_logger

load_dotenv()
logger = get_logger(__name__)

# Verified default model identifiers based on current Groq & Google Gemini availability
DEFAULT_GROQ_SMART_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_FAST_MODEL = "llama-3.1-8b-instant"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


def get_groq_smart_model() -> str:
    """Returns the configured Groq smart model identifier."""
    model = os.getenv("GROQ_SMART_MODEL", DEFAULT_GROQ_SMART_MODEL).strip()
    if not model:
        raise ValueError("GROQ_SMART_MODEL configuration cannot be empty.")
    return model


def get_groq_fast_model() -> str:
    """Returns the configured Groq fast model identifier."""
    model = os.getenv("GROQ_FAST_MODEL", DEFAULT_GROQ_FAST_MODEL).strip()
    if not model:
        raise ValueError("GROQ_FAST_MODEL configuration cannot be empty.")
    return model


def get_gemini_model() -> str:
    """Returns the configured Google Gemini fallback model identifier."""
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
    if not model:
        raise ValueError("GEMINI_MODEL configuration cannot be empty.")
    return model


def get_groq_api_key() -> str:
    """Validates and retrieves the Groq API key."""
    key = os.getenv("GROQ_API_KEY")
    if not key or not key.strip():
        raise ValueError("GROQ_API_KEY is missing. Please add it to your environment variables.")
    return key.strip()


def get_gemini_api_key() -> Optional[str]:
    """Retrieves optional Google Gemini API key if present."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_API_KEY")
    return key.strip() if key and key.strip() else None


def initialize_llms(
    groq_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    groq_smart_model: Optional[str] = None,
    groq_fast_model: Optional[str] = None,
    gemini_model: Optional[str] = None,
):
    """
    Initializes Groq and Gemini models with task-based tiering and explicit cross-provider fallbacks.
    """
    api_key = groq_api_key or get_groq_api_key()
    smart_model_name = groq_smart_model or get_groq_smart_model()
    fast_model_name = groq_fast_model or get_groq_fast_model()
    gemini_model_name = gemini_model or get_gemini_model()
    gemini_key = gemini_api_key if gemini_api_key is not None else get_gemini_api_key()

    groq_smart_instance = ChatGroq(
        model=smart_model_name,
        api_key=api_key,
        max_tokens=3500,
        max_retries=1,
    )
    logger.info(f"Groq Smart LLM initialized with model: '{smart_model_name}'")

    groq_fast_instance = ChatGroq(
        model=fast_model_name,
        api_key=api_key,
        max_tokens=800,
        max_retries=1,
    )
    logger.info(f"Groq Fast LLM initialized with model: '{fast_model_name}'")

    gemini_instance = None
    if gemini_key:
        try:
            gemini_instance = ChatGoogleGenerativeAI(
                model=gemini_model_name,
                google_api_key=gemini_key,
                max_output_tokens=3500,
                temperature=0.3
            )
            logger.info(f"Gemini fallback model activated with model: '{gemini_model_name}'")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini fallback: {e}")

    # Smart LLM (For Itinerary & Final Response): Groq Smart -> Gemini -> Groq Fast
    smart_fallbacks = []
    if gemini_instance:
        smart_fallbacks.append(gemini_instance)
    smart_fallbacks.append(groq_fast_instance)
    smart_llm_chain = groq_smart_instance.with_fallbacks(smart_fallbacks)

    # Fast LLM (For Entity Extraction & Tool Decisions): Groq Fast -> Gemini / Groq Smart
    fast_fallbacks = []
    if gemini_instance:
        fast_fallbacks.append(gemini_instance)
    else:
        fast_fallbacks.append(groq_smart_instance)
    fast_llm_chain = groq_fast_instance.with_fallbacks(fast_fallbacks)

    return groq_smart_instance, groq_fast_instance, gemini_instance, smart_llm_chain, fast_llm_chain


# Module-level singletons for application runtime
GROQ_API_KEY = get_groq_api_key()
GEMINI_API_KEY = get_gemini_api_key()

groq_smart, groq_fast, gemini, smart_llm, fast_llm = initialize_llms()

# Default export (backward compatibility)
llm = smart_llm

__all__ = [
    "llm",
    "smart_llm",
    "fast_llm",
    "groq_smart",
    "groq_fast",
    "gemini",
    "DEFAULT_GROQ_SMART_MODEL",
    "DEFAULT_GROQ_FAST_MODEL",
    "DEFAULT_GEMINI_MODEL",
    "get_groq_smart_model",
    "get_groq_fast_model",
    "get_gemini_model",
    "initialize_llms",
]
