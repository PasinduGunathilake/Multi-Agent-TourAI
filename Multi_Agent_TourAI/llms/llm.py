import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from Multi_Agent_TourAI.utils import get_logger

load_dotenv()
logger = get_logger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your environmental variable file.")

####### LLM Configuration ########

"""
<<<<<<<<<<< HYBRID LLM Architecture (Task-Based Model Tiering + CROSS-PROVIDER FALLBACK ARCHITECTURE >>>>>>>>>>>>

This module implements an intelligent two-tier LLM routing strategy combined 
with cross-provider fallback to ensure high performance, cost efficiency, 
and zero downtime.

1. Task-Based Routing (Tiering):
   - Fast LLM (Lightweight / Low-Latency):
     * Target: Simple tasks such as city extraction, parameter parsing, 
       and quick agent decisions (e.g., Weather Agent, Flight Agent).
     * Primary: Groq 'openai/gpt-oss-20b' (Sub-second response ~0.5s).
     * Fallback: Google Gemini ('gemini-3.5-flash-lite').

   - Smart LLM (Heavy Reasoning / Synthesis):
     * Target: Complex creative tasks such as multi-day itinerary generation 
       and comprehensive travel report synthesis (e.g., Itinerary Agent, Final Agent).
     * Primary: Groq 'openai/gpt-oss-120b' (High-quality flagship reasoning).
     * Fallback 1: Google Gemini ('gemini-3.5-flash-lite' - Cross-provider safety).
     * Fallback 2: Groq 'openai/gpt-oss-20b' (Final resilient backup).

2. Key Benefits & Advantages:
   - High Availability (Zero Downtime): If Groq experiences rate limits (429) 
     or server outages (503), requests automatically failover to Google Gemini 
     without throwing errors or crashing the user session.
   - Latency Optimization: Simple sub-tasks do not waste 4-5 seconds on a large 
     120B model; they resolve in under 1 second using the 20B model.
   - Token & Quota Conservation: Prevents Output Tokens Per Minute (OTPM) rate 
     limit exhaustion on free tiers by reserving the large 120B model exclusively 
     for heavy generation workloads.
================================================================================
"""

## 1. Model Definitions

# Groq Models
groq_smart = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    max_tokens=3500,
    max_retries=1,
)
logger.info(f"Groq LLM initialized with model: '{groq_smart.model_name}'")

groq_fast = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY,
    max_tokens=800,
    max_retries=1,
)
logger.info(f"Groq LLM initialized with model: '{groq_fast.model_name}'")

# Fallback Gemini Model
gemini = None
if GEMINI_API_KEY:
    try:
        gemini = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=GEMINI_API_KEY,
            max_output_tokens=3500,
            temperature=0.3
        )
        logger.info("Gemini fallback model activated.")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini fallback: {e}")


## 2. Smart LLM (For Itinerary & Final Response)
# Flow: Groq 120B -> Gemini Flash -> Groq 20B
smart_fallbacks = []
if gemini:
    smart_fallbacks.append(gemini)
smart_fallbacks.append(groq_fast)

smart_llm = groq_smart.with_fallbacks(smart_fallbacks)


## 3. Fast LLM (For Entity Extraction & Simple Tool Decisions)
# Flow: Groq 20B -> Gemini Flash / Groq 120B
fast_fallbacks = []
if gemini:
    fast_fallbacks.append(gemini)
else:
    fast_fallbacks.append(groq_smart)

fast_llm = groq_fast.with_fallbacks(fast_fallbacks)

# Default export (backward compatibility with existing code)
llm = smart_llm
__all__ = ["llm", "smart_llm", "fast_llm"]
