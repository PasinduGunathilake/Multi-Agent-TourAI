<div align="center">

# Multi-Agent-TourAI

**Intelligent AI Travel Planning System powered by LangGraph Multi-Agent Orchestration, Parallel Fan-Out Execution, Human-in-the-Loop Review, and Dual-Layer PostgreSQL Persistent Memory**

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2.2-orange?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-1.3.2-yellow?style=for-the-badge)](https://www.langchain.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com)
[![LangSmith](https://img.shields.io/badge/LangSmith-Observability-6B4FBB?style=for-the-badge)](https://smith.langchain.com)
[![Groq](https://img.shields.io/badge/Groq-120B_+_20B-F55036?style=for-the-badge)](https://console.groq.com)
[![MCP](https://img.shields.io/badge/MCP-4_Integrations-blueviolet?style=for-the-badge)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## Executive Summary & System Overview

**Multi-Agent-TourAI** is an enterprise-grade, full-stack AI travel planning system that orchestrates **8 specialized AI agents** using LangGraph's `StateGraph` to produce complete, personalized travel plans. Instead of a single monolithic LLM call, the system decomposes every travel request into parallel, independent specialist tasks -- real-time flight search, hotel discovery, live weather forecasting, geospatial attraction mapping, and day-by-day itinerary drafting -- all coordinated through a dynamic intent-aware supervisor routing engine.

Once the draft itinerary is produced, the workflow **pauses** via LangGraph's `interrupt()`, presenting the plan to the human traveler for review before final synthesis. Every session's state and conversation history is durably persisted in **PostgreSQL**, enabling fault recovery, workflow resumption after server restarts, and full cross-session user memory.

The backend exposes a **FastAPI v2 streaming SSE API**. The frontend is a modern **Next.js 15** application with real-time per-agent trace visualization, a living architecture pipeline diagram, and rich structured travel result cards (flights, hotels, weather, maps).

---

## Key System Features

- **Intent-Aware Supervisor Routing:** Classifies every user message into `new_plan`, `specific_query`, or `follow_up` intents to selectively invoke only the required agents -- from full parallel fan-out (~21s) to zero-tool memory responses (~1-2s).
- **Parallel Fan-Out Architecture (4 Agents Simultaneously):** Flight, Hotel, Weather, and Maps agents execute concurrently using LangGraph's conditional edge fan-out. Total latency equals the slowest single agent, not their cumulative sum, yielding a ~38-40% wall-clock reduction versus sequential execution.
- **Model-Based Input Guardrail:** A fast, lightweight `gpt-oss-20b` guard runs first to classify requests as travel-related or harmful. Off-topic and adversarial prompts are blocked in ~0.5s before triggering any expensive LLM or external API call.
- **Human-in-the-Loop (HITL) Review:** Execution pauses via `interrupt()` after draft itinerary generation. The traveler inspects the plan, approves it, or submits custom revision feedback. State is checkpointed to PostgreSQL and survives server restarts indefinitely.
- **Dual-Layer Persistent Memory:** `PostgresSaver` (short-term per-thread conversation and agent output caching) combined with `PostgresStore` (long-term cross-session user preference profiles) for complete stateful, personalized conversations.
- **Hybrid LLM Tiering with Cross-Provider Fallback:** `gpt-oss-20b` (Groq) for fast entity extraction and classification; `gpt-oss-120b` (Groq) with automatic Gemini and 20B fallback for heavy synthesis, ensuring zero-downtime resilience against rate limits and outages.
- **4 MCP Tool Integrations:** AviationStack, Tavily, OpenWeatherMap, and Geoapify exposed as LangChain-native tools via `langchain-mcp-adapters`, providing structured real-world data to every specialist agent.
- **Full LangSmith Observability:** Distributed tracing across every LLM call, tool invocation, and graph node -- with per-run token counts, latencies, cost attribution, and error rate monitoring.

---

## Modular System Architecture

The production system is built as a clean, decoupled Python package (`Multi_Agent_TourAI`) separating guardrail validation, supervisor routing, parallel specialist tool execution, HITL checkpointing, and final synthesis:

```
Multi-Agent-TourAI/
|
+-- Multi_Agent_TourAI/                    # Core Python package
|   +-- agents/                            # All specialist agent nodes
|   |   +-- supervisor_agent.py            # Intent classification + dynamic routing
|   |   +-- flight_agent.py               # AviationStack MCP: flights, routes, schedules
|   |   +-- hotel_agent.py                # Tavily MCP: hotel discovery & web search
|   |   +-- weather_agent.py              # OpenWeather MCP: current + 5-day forecast
|   |   +-- maps_agent.py                 # Geoapify MCP: POI, dining, geocoding, routes
|   |   +-- itinerary_agent.py            # Day-by-day plan synthesis (fan-in barrier)
|   |   +-- approval_agent.py             # HITL interrupt() handler
|   |   +-- final_agent.py                # Final response synthesis (GPT-120B + fallback)
|   |
|   +-- graph/
|   |   +-- state.py                      # TravelState TypedDict (shared state schema)
|   |   +-- workflow.py                   # LangGraph StateGraph definition & edge routing
|   |
|   +-- mcp/                              # MCP server client integrations
|   |   +-- aviationstack_mcp.py          # AviationStack Remote MCP client
|   |   +-- tavily_mcp.py                 # Tavily Remote MCP client
|   |   +-- weather_mcp.py                # OpenWeather FastMCP client
|   |   +-- geoapify_mcp.py               # Geoapify Remote MCP client (HTTP JSON-RPC)
|   |
|   +-- memory/
|   |   +-- checkpointer.py               # PostgresSaver (short-term session memory)
|   |   +-- store.py                      # PostgresStore (long-term user profile memory)
|   |
|   +-- guardrails/
|   |   +-- inputguardrail.py             # Model-based safety filter node
|   |
|   +-- llms/
|   |   +-- llm.py                        # Hybrid LLM factory (tiering + fallback chain)
|   |
|   +-- config/
|   |   +-- prompts.py                    # All system + user prompt templates
|   |
|   +-- utils/
|       +-- logger.py                     # Centralized dual-handler logger
|
+-- frontend/                             # Next.js 15 frontend application
|   +-- app/                              # App Router pages
|   +-- components/                       # React components
|   |   +-- AgentWorkflowVisualizer/      # Live real-time agent execution graph
|   |   +-- ReasoningTrace/               # Per-agent LLM reasoning trace viewer
|   |   +-- TravelResultsView/            # Flights, hotels, weather, maps result cards
|   |   +-- AgentTurnContainer/           # Individual agent turn display
|   |   +-- ArchitecturePipeline/         # Static pipeline architecture diagram
|   |   +-- MetricsBar/                   # LangSmith-backed performance metrics bar
|   |   +-- ChatInput/                    # Chat input with HITL approval controls
|   +-- package.json
|
+-- app.py                                # FastAPI v2 app -- all REST + SSE endpoints
+-- backend.py                            # Backend entry point helpers
+-- entrypoint.py                         # CLI entrypoint
+-- requirements.txt                      # Python dependencies
+-- setup.py                              # Editable package registration
+-- .env                                  # Environment variables (not committed)
+-- LICENSE                               # MIT License
+-- README.md                             # Project documentation
```

---

## Detailed Component Code Audit

### 1. LangGraph StateGraph & Execution Flow (`Multi_Agent_TourAI/graph/`)

**`state.py` (`TravelState` TypedDict):**

Defines the single shared state dictionary passed between all 8 agent nodes:

| Field | Type | Purpose |
| :--- | :--- | :--- |
| `messages` | `Annotated[list[AnyMessage], operator.add]` | Append-only conversation history across all turns |
| `user_query` | `str` | Raw user travel request |
| `flight_results` | `str` | Output from Flight Agent (AviationStack MCP) |
| `hotel_results` | `str` | Output from Hotel Agent (Tavily MCP) |
| `weather_results` | `str` | Output from Weather Agent (OpenWeather MCP) |
| `maps_results` | `str` | Output from Maps Agent (Geoapify MCP) |
| `itinerary` | `str` | Draft day-by-day plan from Itinerary Agent |
| `llm_calls` | `Annotated[int, operator.add]` | Auto-summed LLM call counter across all nodes |
| `guardrail_allowed` | `bool` | Safety gate flag set by Input Guardrail |
| `guardrail_reason` | `str` | Rejection explanation if blocked |
| `intent` | `str` | Supervisor decision: `new_plan`, `specific_query`, or `follow_up` |
| `selected_agents` | `list[str]` | Supervisor-selected agent subset for `specific_query` |
| `supervisor_reasoning` | `str` | Supervisor's chain-of-thought routing rationale |
| `approved` | `bool` | Human HITL approval flag |
| `human_feedback` | `str` | User's optional revision feedback text |
| `final_response` | `str` | Polished final output from Final Agent |

`messages` and `llm_calls` use `operator.add` as their reducer so that parallel fan-out branches can safely write to the same fields simultaneously without overwriting each other -- a critical correctness requirement for concurrent graph execution.

**`workflow.py` (`StateGraph` Definition & Routing Logic):**

```
                    [START]
                       |
                       v
              [ input_guardrail ]   <-- gpt-oss-20b, ~0.5s
                       |
         [blocked]     |     [allowed]
            v                      v
  [guardrail_blocked]         [supervisor]   <-- gpt-oss-20b, ~0.3s
                                   |
                  (1) new_plan      |  (2) specific_query    (3) follow_up
                       v                       v                   |
           [PARALLEL FAN-OUT]        [single agent]                |
             flight_agent              (selected)                  |
             hotel_agent                   |                       |
             weather_agent                 |                       |
             maps_agent                    |                       |
                       |                   |                       |
                       v                   |                       |
            [itinerary_agent] <------------+                       |
                       |                                          |
                       v                                          |
            [human_approval]   <-- LangGraph interrupt() HITL     |
                       |                                          |
                       v                                          v
                          [ final_agent ]   <-- gpt-oss-120b + Gemini fallback
                                  |
                               [END]
```

- **`route_after_guardrail()`:** Reads `guardrail_allowed` from state. Routes to `supervisor` on pass, `guardrail_blocked` terminal node on fail.
- **`route_from_supervisor()`:** Reads `intent` and `selected_agents`. Returns list `["flight_agent", "hotel_agent", "weather_agent", "maps_agent"]` for `new_plan` (fan-out), a single-element list for `specific_query`, or `["final_agent"]` for `follow_up`.
- **`route_after_tool()`:** Reads `intent`. Routes to `itinerary_agent` for `new_plan` or directly to `final_agent` for `specific_query`.

**Parallel Latency Engineering:**

| Execution Mode | Strategy | Total Latency |
| :--- | :--- | :--- |
| Sequential (baseline) | Flight -> Hotel -> Weather -> Maps | ~34s |
| **Parallel Fan-Out (production)** | **All 4 run concurrently** | **~21s** |
| Specific Query | Single specialist agent only | ~4-6s |
| Follow-Up | Zero tools, PostgreSQL memory only | ~1-2s |

LangGraph's fan-in barrier at `itinerary_agent` waits for all parallel branches to complete before proceeding, ensuring the Itinerary Agent always receives the full data set from all four specialists.

---

### 2. Agent Nodes (`Multi_Agent_TourAI/agents/`)

**`supervisor_agent.py` (`supervisor_agent` Function):**
- Inspects `user_query`, `has_itinerary` (bool from existing state), and `history_len` (conversation turn count).
- Invokes `fast_llm` (`gpt-oss-20b`) with `SUPERVISOR_SYSTEM_PROMPT` and a formatted `USER_CONTEXT_PROMPT`.
- Parses the model's strict JSON response via `_extract_json()` (finds first `{...}` block in raw output, robust against extra text wrappers).
- Returns `intent` (one of: `new_plan`, `specific_query`, `follow_up`), `selected_agents` (list of agent names for `specific_query`), and `supervisor_reasoning`.
- **Deterministic Fallback:** If JSON parsing fails, falls back to `follow_up` if an itinerary exists (memory-based answer) or `new_plan` if no prior itinerary is found. This prevents any supervisor model failure from crashing the pipeline.

**`flight_agent.py` (`flight_agent` Function):**
- Calls the AviationStack MCP server via `asyncio.run()` for 5 sequential async tool invocations: `list_airports`, `list_airlines`, `list_routes`, `future_flights_arrival_departure_schedule`, `list_taxes`.
- Truncates each MCP response to 3,000 characters before injecting into `FLIGHT_PROMPT_TEMPLATE` to prevent Groq TPM (Tokens Per Minute) rate limit exhaustion.
- Invokes `fast_llm` to synthesize structured flight recommendation text from all five data sources.
- Fails gracefully: returns `"Flight information unavailable: {error}"` without crashing the workflow if AviationStack is unreachable.

**`hotel_agent.py` (`hotel_agent` Function):**
- Calls the Tavily Remote MCP server to execute travel-focused live web searches for hotel options at the destination.
- Returns structured hotel recommendation text synthesized via `fast_llm`.

**`weather_agent.py` (`weather_agent` Function):**
- Uses `extract_destination()` helper: invokes `fast_llm` with `DESTINATION_EXTRACTOR_PROMPT_TEMPLATE` to isolate the city name from the full user query (e.g., `"Plan a 5-day trip to Dubai from Sri Lanka"` -> `"Dubai"`).
- Executes **two async MCP calls** in sequence: `weather_mcp_search(city)` (current conditions: temperature, humidity, description) and `forecast_mcp_search(city)` (5-day, 3-hourly forecast data).
- Concatenates both results into a single `weather_data` string for downstream agent consumption.
- Fails gracefully with `"Weather data unavailable for {city}: {error}"` on any MCP error.

**`maps_agent.py` (`maps_agent` Function):**
- Extracts destination city using the shared `extract_destination()` helper (LLM-based NER).
- **3-Case Intent Detection via Keyword Matching:**
  1. **Route/Distance Query:** Detected via keywords (`"how far"`, `"distance between"`, `"route from"`, `"drive from"`, `"travel from"`, `"to get to"`). Invokes `fast_llm` with a strict `"ORIGIN | DESTINATION"` extraction prompt. Appends city context to disambiguate geocoding (e.g., `"Colosseum, Rome"` instead of just `"Colosseum"`). Detects travel mode (`drive`, `walk`, `transit`) from query keywords and calls `geoapify_mcp_calculate_route(origin, dest, mode)`.
  2. **Food/Dining Query:** Detected via keywords (`"cafe"`, `"coffee"`, `"restaurant"`, `"food"`, `"dining"`, `"eat"`). Calls `geoapify_mcp_search_places(city, category="catering.cafe/restaurant", limit=5)`.
  3. **Default - Tourist Attractions:** Falls through to `geoapify_mcp_search_places(city, category="tourism.sights", limit=5)` for all itinerary-focused requests.

**`itinerary_agent.py` (`itinerary_agent` Function):**
- Acts as the **fan-in barrier** -- only executes after all 4 parallel agents have completed and written their results to `TravelState`.
- Invokes `smart_llm` (`gpt-oss-120b`) with all four tool outputs (`flight_results`, `hotel_results`, `weather_results`, `maps_results`) to synthesize a coherent, geographically organized, day-by-day travel plan.

**`approval_agent.py` (`human_approval_agent` Function):**
- Calls LangGraph's `interrupt()` primitive directly. **Must never be wrapped in `try/except`** -- LangGraph uses the resulting `GraphInterrupt` exception internally to serialize and pause the graph state in PostgreSQL.
- The `interrupt()` payload includes the `draft_itinerary`, `approval_request`, `selected_agents`, `supervisor_reasoning`, and the expected response schema `{"approved": bool, "feedback": str}`.
- On `Command(resume=...)`, reads `approved` (bool) and `feedback` (str) from the resume payload and writes them to `TravelState` for the Final Agent.

**`final_agent.py` (`final_response_agent` Function):**
- Implements **3-case intent branching** for universal response synthesis:
  1. **`follow_up`:** Assembles all prior context (existing itinerary, flight/hotel/weather/maps results) into a system instruction. Keeps only the last 3 messages from conversation history (`all_messages[-3:]`) to prevent prompt bloat and Groq TPM exhaustion. Deduplicates the current user query if it is already the last message. Invokes `smart_llm` to answer directly from PostgreSQL checkpoint memory.
  2. **`specific_query`:** Formats only the data from the selected specialist agent, explicitly instructing the model to omit empty sections for unused services.
  3. **`new_plan`:** Reads HITL `approved` flag and `human_feedback`. Constructs `review_instruction` dynamically: if approved, preserves draft itinerary decisions; if not, instructs the model to incorporate user's revision feedback. Invokes `smart_llm` (`gpt-oss-120b`) to produce the richly formatted final 7-section comprehensive travel response.

---

### 3. Hybrid LLM Factory & Cross-Provider Fallback (`Multi_Agent_TourAI/llms/llm.py`)

The module implements a two-tier LLM routing strategy with automatic cross-provider failover for zero-downtime resilience:

**Tier 1 -- Fast LLM (`fast_llm`):**
- **Primary:** `groq/openai/gpt-oss-20b` (800 max tokens, ~0.5s)
- **Fallback:** `gemini-3.5-flash-lite` (via `langchain_google_genai`)
- **Used by:** Input Guardrail, Supervisor, Flight/Hotel/Weather/Maps agents (entity extraction and tool synthesis)

**Tier 2 -- Smart LLM (`smart_llm`):**
- **Primary:** `groq/openai/gpt-oss-120b` (3500 max tokens, ~3-5s)
- **Fallback 1:** `gemini-3.5-flash-lite` (cross-provider safety net)
- **Fallback 2:** `groq/openai/gpt-oss-20b` (final resilient backup)
- **Used by:** Itinerary Agent, Final Agent (complex multi-section synthesis)

Fallback chains are built via LangChain's `.with_fallbacks([...])`. If Groq returns a `429 Rate Limit` or `503 Service Unavailable`, the chain automatically retries against Gemini without surfacing any error to the user session.

| Design Decision | Engineering Rationale |
| :--- | :--- |
| `fast_llm` for extraction tasks | Simple NER/classification does not require 120B parameters; 20B resolves in <1s |
| `smart_llm` for synthesis tasks | Multi-day itinerary generation requires flagship reasoning quality |
| Cross-provider Gemini fallback | Protects against Groq free-tier rate limit exhaustion during parallel fan-out bursts |
| `max_retries=1` per model | Prevents silent retry loops from stacking latency during cascading failures |

---

### 4. MCP Tool Integrations (`Multi_Agent_TourAI/mcp/`)

All four external APIs are exposed as LangChain-native tool objects via `langchain-mcp-adapters`, enabling seamless integration into agent `invoke()` calls.

**`aviationstack_mcp.py` (AviationStack Remote MCP):**
- Connects to the AviationStack MCP server via `langchain-mcp-adapters`.
- Exposes tools: `list_airports`, `list_airlines`, `list_routes`, `future_flights_arrival_departure_schedule`, `list_taxes`.
- Called via `asyncio.run()` in the synchronous `flight_agent` node to bridge the async MCP protocol into LangGraph's synchronous node execution model.

**`tavily_mcp.py` (Tavily Remote MCP):**
- Connects to the Tavily MCP server for travel-focused live web search.
- Provides hotel listings, travel guides, accommodation reviews, and destination content.

**`weather_mcp.py` (OpenWeather FastMCP):**
- Implements a local FastMCP server wrapping the OpenWeatherMap REST API.
- Exposes `weather_mcp_search(city)` (current conditions) and `forecast_mcp_search(city)` (5-day, 3-hourly forecast).

**`geoapify_mcp.py` (Geoapify Remote MCP -- HTTP JSON-RPC):**
- Connects to Geoapify's official Remote MCP server at `https://api.geoapify.com/v1/mcp` via HTTP JSON-RPC transport using `MultiServerMCPClient`.
- **Tool Caching:** `init_geoapify_tools()` lazy-initializes and caches all tool objects in `_geoapify_tools` dictionary on first call to avoid repeated MCP handshakes on every request.
- `_parse_mcp_response()`: Handles MCP text content block format (`[{"text": "..."}]`) by extracting and JSON-deserializing the inner text payload.
- `geoapify_mcp_search_places(city, category, limit)`: Geocodes city name to coordinates via Geoapify, then searches for places by category (`tourism.sights`, `catering.restaurant`, `catering.cafe`).
- `geoapify_mcp_calculate_route(origin, dest, mode)`: Geocodes both endpoints and computes driving/walking/transit routes with distance and duration.
- SSL certificates configured via `certifi` for Windows compatibility (`os.environ["SSL_CERT_FILE"]`, `REQUESTS_CA_BUNDLE`).

---

### 5. Dual-Layer Persistent Memory (`Multi_Agent_TourAI/memory/`)

**`checkpointer.py` (`PostgresSaver` -- Short-Term Session Memory):**
- Establishes a synchronous `psycopg` connection to Supabase PostgreSQL with `sslmode=require` automatically appended to the connection URL if not already present.
- Calls `checkpointer.setup()` on startup to ensure LangGraph's checkpoint schema tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) are provisioned.
- **Three key capabilities:**
  1. **Thread-Level Conversation Memory:** Saves the entire `TravelState` (all agent outputs, messages, HITL state) per `thread_id`. Subsequent turns in the same session inherit the full prior context.
  2. **Intermediate Output Caching:** When `flight_agent` completes, its `flight_results` are checkpointed. If a downstream agent fails, the workflow resumes from the last checkpoint without re-running earlier expensive API calls -- saving significant LLM tokens and external API credits.
  3. **Durable HITL State Persistence:** When `interrupt()` pauses execution, the full graph state is serialized to PostgreSQL. The workflow survives server restarts and can be resumed via `Command(resume=...)` days later using the same `thread_id`.
- `delete_thread_checkpoints(thread_id)`: Purges all three checkpoint tables for a given `thread_id` for session cleanup or reset.

**`store.py` (`PostgresStore` -- Long-Term User Profile Memory):**
- Maintains persistent cross-session user preference profiles keyed by `user_id` (separate from `thread_id`).
- Stores travel history, preferred destinations, budget ranges, and accommodation preferences across multiple independent sessions.

---

### 6. Model-Based Input Guardrail (`Multi_Agent_TourAI/guardrails/inputguardrail.py`)

**`input_guardrail()` Function:**
- Invokes `fast_llm` (`gpt-oss-20b`) with `Guardrail_PROMPT_TEMPLATE` containing the user query. System prompt explicitly instructs: `"Return strict JSON only"`.
- Parses the model's strict JSON response `{"allowed": bool, "reason": str}` via `_extract_json()`.
- **Fail-Open Strategy:** If JSON parsing fails (malformed model output), defaults `allowed = True`. A guardrail implementation bug can never permanently block all valid user queries.
- On block: writes `guardrail_allowed = False`, `guardrail_reason`, and an `AIMessage` with the refusal text to `TravelState`. Routes to `guardrail_blocked` terminal node, exiting before any tool agent or external API is invoked -- saving the full cost of a parallel fan-out run.
- **`guardrail_blocked()` Node:** Reads `guardrail_reason` from state and returns a final `AIMessage` to terminate the graph cleanly.

---

### 7. FastAPI Backend Server (`app.py`)

The FastAPI v2 server exposes all REST and SSE endpoints with full Pydantic request/response validation and structured logging:

**Primary REST Endpoints:**

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Health check -- returns service name and status |
| `/api/plan` | `POST` | Runs the full multi-agent workflow; returns result or HITL interrupt payload |
| `/api/plan/resume` | `POST` | Resumes a paused HITL workflow with `Command(resume=...)` |
| `/api/history/{thread_id}` | `GET` | Fetches full conversation state from PostgreSQL checkpoint |
| `/api/stream/plan` | `POST` | SSE streaming: yields agent update events as graph executes |
| `/api/stream/resume` | `POST` | SSE streaming resume with real-time token delivery |
| `/api/delete/{thread_id}` | `DELETE` | Purges all PostgreSQL checkpoints for a thread |

**SSE Streaming Architecture:**
- Uses `nest_asyncio.apply()` to resolve nested event loop conflicts between FastAPI's async runtime and LangGraph's synchronous `travel_graph.invoke()` which internally calls `asyncio.run()` inside MCP clients.
- `StreamingResponse` with `media_type="text/event-stream"` yields structured JSON events per agent completion.
- CORS middleware configured for `http://localhost:3000` (Next.js dev server).

---

## LangSmith Observability & Telemetry

Multi-Agent-TourAI ships with **full distributed tracing** via LangSmith, providing visibility into every agent node, LLM invocation, and MCP tool call across the entire graph execution.

### What is Traced

| Telemetry Signal | Detail |
| :--- | :--- |
| **End-to-End Run Traces** | Full hierarchical execution tree per user query |
| **LLM Calls** | Prompt tokens, completion tokens, latency per model invocation |
| **MCP Tool Calls** | Tool name, input arguments, raw output, invocation latency |
| **Agent Node Timing** | Per-node wall-clock time (guardrail, supervisor, each parallel agent, final) |
| **Error Rates** | Failed nodes, tool timeouts, model errors |
| **Cost Attribution** | Per-run and aggregate estimated token cost |

### Run Naming Convention

| Run Name | Intent | Typical Trace |
| :--- | :--- | :--- |
| `New Travel Plan` | `new_plan` | Guardrail -> Supervisor -> 4 Parallel Agents -> Itinerary -> HITL -> Final |
| `Specific Query` | `specific_query` | Guardrail -> Supervisor -> Single Agent -> Final |
| `Follow-Up` | `follow_up` | Guardrail -> Supervisor -> Final (zero tools) |

### Observed Baseline Metrics

| Metric | Observed Value |
| :--- | :--- |
| Error Rate | ~0% |
| New Plan End-to-End Latency | ~21s (parallel) |
| Specific Query Latency | ~4-6s |
| Follow-Up Latency | ~1-2s |
| Guardrail Latency | ~0.5s |
| Supervisor Latency | ~0.3s |
| Prompt Token Compression | ~85% reduction vs. naive full-context prompting |

### Viewing Traces

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Select project: **`Multi-Agent-TourAI`**
3. Click any run to expand the full hierarchical trace tree
4. Drill into any agent node to inspect exact prompt/response payloads and token counts

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
| :--- | :--- | :--- |
| Python | 3.11 | Core runtime |
| LangGraph | 1.2.2 | Multi-agent StateGraph orchestration |
| LangChain | 1.3.2 | LLM abstraction, tool interfaces, message types |
| LangChain-Groq | 1.1.3 | Groq-hosted model inference (gpt-oss-20b / 120b) |
| LangChain-Google-GenAI | 4.4.2 | Gemini model cross-provider fallback |
| langchain-mcp-adapters | 0.3.0 | MCP tool integration into LangChain agents |
| mcp | 1.28.1 | Model Context Protocol base library |
| FastAPI | 0.136 | REST + SSE streaming API server |
| Uvicorn | 0.48 | ASGI production server |
| psycopg (binary) | 3.3.4 | PostgreSQL synchronous driver |
| psycopg_pool | 3.3.1 | PostgreSQL connection pooling |
| langgraph-checkpoint-postgres | 3.1.0 | LangGraph PostgresSaver checkpointer |
| nest_asyncio | 1.6.0 | Nested event loop compatibility for FastAPI + asyncio.run() |
| python-dotenv | 1.2.2 | Environment variable loading from .env |
| LangSmith | -- | Distributed tracing and observability |

### Frontend

| Technology | Purpose |
| :--- | :--- |
| Next.js 15 | React framework, App Router, SSR |
| TypeScript | Type-safe component development |
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Component library |
| EventSource API | SSE streaming from FastAPI backend |

---

## Installation & Setup Guide

### Prerequisites

- Python 3.11
- Conda (recommended) or venv
- Node.js 18+ and npm
- PostgreSQL database (e.g., [Supabase](https://supabase.com) free tier)
- API keys for all external services

### 1. Clone the Repository

```bash
git clone https://github.com/PasinduGunathilake/Multi-Agent-TourAI.git
cd Multi-Agent-TourAI
```

### 2. Create & Activate Python Environment

```bash
# Create conda environment
conda create -p tourvenv python=3.11 -y

# Activate (Windows)
conda activate "D:\path\to\Multi-Agent-TourAI\tourvenv"

# Activate (Linux/macOS)
conda activate ./tourvenv
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The `-e .` at the bottom of `requirements.txt` installs the package in editable mode so all internal imports (`from Multi_Agent_TourAI.agents...`) resolve correctly.

### 4. Set Up PostgreSQL (Supabase Cloud)

1. Create a free PostgreSQL instance at [supabase.com](https://supabase.com)
2. Copy the **External Database URL** (format: `postgresql://user:pass@host/dbname`)
3. Add it to `.env` as `DATABASE_URL`
4. LangGraph will auto-provision its checkpoint schema tables on first run via `checkpointer.setup()`

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# -- LLM Providers -----------------------------------------------
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_google_gemini_api_key

# -- Database ----------------------------------------------------
DATABASE_URL=postgresql://user:password@host/dbname

# -- External MCP APIs -------------------------------------------
AVIATIONSTACK_API_KEY=your_aviationstack_key
TAVILY_API_KEY=your_tavily_key
OPENWEATHER_API_KEY=your_openweather_key
GEOAPIFY_API_KEY=your_geoapify_key

# -- LangSmith Observability -------------------------------------
LANGCHAIN_TRACING_V2=true
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=Multi-Agent-TourAI
```

### API Key Sources

| Service | Free Tier | Sign Up |
| :--- | :--- | :--- |
| Groq (LLMs) | Yes -- generous free tier | https://console.groq.com |
| Google Gemini | Yes | https://aistudio.google.com |
| AviationStack | Yes -- 500 req/month | https://aviationstack.com |
| Tavily Search | Yes | https://tavily.com |
| OpenWeatherMap | Yes -- 1,000 req/day | https://openweathermap.org/api |
| Geoapify | Yes -- 3,000 req/day | https://geoapify.com |
| LangSmith | Yes | https://smith.langchain.com |

---

## Running the Application

### Start the Backend (FastAPI)

```bash
# From project root with tourvenv active
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

API server: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

### Start the Frontend (Next.js)

```bash
cd frontend
npm run dev
```

Frontend: `http://localhost:3000`

---

## Enterprise Security & System Resilience

1. **Environment Variable Secret Isolation (`.env` + `python-dotenv`):** All API keys, database credentials, and LangSmith tokens are decoupled from source code and excluded from version control via `.gitignore`.

2. **Fail-Open Guardrail Strategy:** If the guardrail model returns malformed JSON, the system defaults to `allowed = True`. A guardrail implementation bug can never permanently block all user queries.

3. **Deterministic Supervisor Fallback:** If the supervisor's JSON response cannot be parsed, routing falls back deterministically based on state (existing itinerary -> `follow_up`; no itinerary -> `new_plan`), preventing any supervisor model error from crashing the graph.

4. **Per-Agent Error Isolation Boundaries:** Every specialist agent (`flight_agent`, `weather_agent`, `maps_agent`) wraps MCP calls in `try/except` and returns a descriptive fallback string. A single failing external API never crashes the full workflow.

5. **Durable HITL Checkpoint Persistence:** HITL interrupt state is serialized to PostgreSQL. If the server crashes while awaiting human review, the session is fully recoverable via the same `thread_id` after restart -- no data loss, no duplicate API costs.

6. **Cross-Provider LLM Failover:** Groq rate limits (free-tier 429s during parallel fan-out bursts) are automatically absorbed by the Gemini fallback chain without surfacing errors to the user session.

7. **SSL Certificate Pinning (Windows Compatibility):** `certifi` CA bundle is explicitly registered via `os.environ["SSL_CERT_FILE"]` and `REQUESTS_CA_BUNDLE` across all MCP clients and the PostgreSQL checkpointer to prevent TLS verification failures on Windows.

---

## Author

### Pasindu Gunathilake

- **Education:** BSc. Computer Science Undergraduate, University of Jaffna, Sri Lanka
- **Email:** [pasindugunatilake144@gmail.com](mailto:pasindugunatilake144@gmail.com)
- **Portfolio:** [https://pasindugunathilake.github.io/Portfolio-PG](https://pasindugunathilake.github.io/Portfolio-PG)
- **Focus Areas:** AI/ML Systems, Multi-Agent Architectures, LLM Engineering, Full-Stack Development

---

## License

This project is developed for educational, research, and open-source demonstration purposes under the **MIT License**. See [LICENSE](LICENSE) for details.
