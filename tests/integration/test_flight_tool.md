# Integration Test Documentation: `test_flight_tool.py`

This document details the integration test suite for [`Multi_Agent_TourAI.tools.flight_tool`](file:///d:/DEPARTMENT%20OF%20COMPUTER%20SCIENCE/Computer%20Science/AI%20ML/AI_ML_DL/Gen%20AI%20Projects/Agent%20Systems/Multi-Agent-TourAI/Multi_Agent_TourAI/tools/flight_tool.py).

---

## Test Objectives
Verify that the `flight_search` tool can successfully communicate with the **AviationStack REST API**, send HTTP requests with proper parameters, handle network timeouts, and return formatted flight information.

---

## Prerequisites
Ensure `AVIATIONSTACK_API_KEY` is defined in `.env`:
```env
AVIATIONSTACK_API_KEY=your_key_here
```

---

## Test Cases Breakdown

### 1. `test_flight_search_structured()`
* **Objective:** Tests flight searching using structured keyword arguments (`destination="Dubai", limit=2`).
* **Execution:**
  1. Resolves `"Dubai"` to IATA code `"DXB"`.
  2. Resolves default origin to `"CMB"`.
  3. Dispatches HTTP GET request to `http://api.aviationstack.com/v1/flights` with `params={"dep_iata": "CMB", "arr_iata": "DXB", "limit": 2}`.
* **Assertions:**
  * Returns a valid non-empty string.
  * Ensures no unhandled exceptions are raised.

---

### 2. `test_flight_search_natural_query()`
* **Objective:** Tests flight searching using free-form natural language query strings.
* **Execution:**
  1. Calls `parse_route("Plan a 7 days Japan trip from SriLanka")`.
  2. Extracts `dep_iata = "CMB"` and `arr_iata = "HND"`.
  3. Sends request to AviationStack API for the route `CMB -> HND`.
* **Assertions:**
  * Returns a formatted Markdown string with flight status or informative message.

---

## How to Run
```powershell
python tests/integration/test_flight_tool.py
```
