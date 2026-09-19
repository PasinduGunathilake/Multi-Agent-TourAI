# Integration Test Documentation: `test_tavily_tool.py`

This document details the integration test suite for [`Multi_Agent_TourAI.tools.tavily_tool`](file:///d:/DEPARTMENT%20OF%20COMPUTER%20SCIENCE/Computer%20Science/AI%20ML/AI_ML_DL/Gen%20AI%20Projects/Agent%20Systems/Multi-Agent-TourAI/Multi_Agent_TourAI/tools/tavily_tool.py).

---

## Test Objectives
Verify that the `tavily_search` tool can interact with the **Tavily AI Search API**, perform live web queries for attractions, hotels, and travel recommendations, and truncate results appropriately for AI Agent consumption.

---

## Prerequisites
Ensure `TAVILY_API_KEY` is defined in `.env`:
```env
TAVILY_API_KEY=tvly-your_key_here
```

---

## Test Cases Breakdown

### 1. `test_tavily_search()`
* **Objective:** Verifies that a natural language travel query returns top search snippets formatted in Markdown.
* **Sample Query:** `"Top attractions and hotels in Colombo Sri Lanka"`
* **Verification Points:**
  1. **API Call:** Dispatches a query request with `max_results=5`.
  2. **Metadata Filtering:** Checks that `title`, `url`, and `content` are extracted for each result.
  3. **Snippet Truncation:** Ensures snippets longer than 300 characters are trimmed cleanly at the last whole word with an appended `...` to avoid token bloating.
  4. **Output Format:** Validates that numbered Markdown list items (`1. **Title** ...`) are generated.

---

## How to Run
```powershell
pytest tests/integration/test_tavily_tool.py -s
```
or
```powershell
python tests/integration/test_tavily_tool.py
```
