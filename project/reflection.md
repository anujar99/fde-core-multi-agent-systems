# Reflective Report: Beaver's Choice Paper Company Multi-Agent System

**Author:** Anuja
**Date:** 2026-03-20
**System:** Paper Supply Quote, Inventory, and Sales Multi-Agent System

---

## 1. Agent Workflow Architecture

### Overview

The system is built around four agents implemented with the smolagents `ToolCallingAgent` framework: an **Orchestrator**, an **Inventory Agent**, a **Quote Agent**, and an **Ordering Agent**. All agents communicate exclusively through plain-text strings, keeping the interface clean and LLM-friendly.

The full architecture is illustrated in `agent_workflow.md`, which contains both a simplified overview diagram and a detailed diagram mapping each tool to the helper functions it uses.

### Agent Roles

**Orchestrator (Operations Director)**
The Orchestrator is the single entry point for every customer request. It receives a plain-text request with a date stamp, sequences calls to the three worker agents in a fixed order, and composes the final customer-facing response. It does not access the database directly — all state changes flow through the worker agents. The fixed sequence (Inventory → Quote → Ordering) ensures stock is verified before quoting, and quoting is complete before any sale is recorded.

**Inventory Agent (Stock Manager)**
The Inventory Agent is responsible for all stock-related decisions. It uses `check_inventory` to get a snapshot of all stock levels, `check_item_stock` to inspect a specific item including its minimum threshold, and `restock_item` to place a supplier order when stock falls below that threshold. The `restock_item` tool verifies available cash before committing a stock order transaction, preventing the company from over-spending.

**Quote Agent (Pricing Specialist)**
The Quote Agent handles pricing. It calls `get_historical_quotes` to retrieve comparable past orders for context, then calls `calculate_quote` to produce a deterministic, itemised breakdown. The discount tier logic is implemented directly in `calculate_quote` — not delegated to the LLM — so discounts are always applied correctly regardless of model behaviour. The full product catalog is embedded in the Quote Agent's system prompt so it can map natural-language item descriptions (e.g., "heavy cardstock") to exact catalog names.

**Ordering Agent (Transaction Manager)**
The Ordering Agent finalises sales. It calls `get_available_cash` to confirm the company has funds, `complete_sale` for each fulfilled line item (which verifies stock, records the transaction, and calculates a delivery date), and `get_financial_summary` to produce an updated financial position after processing.

### Architectural Decisions

**Why four agents rather than one?**
Separating inventory, quoting, and ordering into distinct agents reflects the separation of concerns principle and mirrors how a real paper supply business would divide responsibilities. Each agent's LLM context is focused on a narrow domain, which reduces the risk of the model making off-topic decisions (e.g., the Quote Agent has no authority to modify stock).

**Why smolagents `ToolCallingAgent`?**
smolagents provides a lightweight, production-oriented framework with a clean `@tool` decorator pattern, native OpenAI-compatible model support, and a `ToolCallingAgent` that handles the tool-call loop automatically. This minimised boilerplate and kept all agent logic inside the single required file.

**Why embed the catalog in agent system prompts?**
Customer requests use natural language ("glossy A4 paper", "heavy cardstock") while the database requires exact catalog names ("Glossy paper", "Cardstock"). Embedding the full catalog in the Inventory and Quote agent prompts gives the LLM the reference it needs to resolve names without requiring a separate lookup step. A substring-matching resolver (`_resolve_item_name`) was also added in code as a safety net for cases where the LLM passes a descriptive rather than exact name to a tool.

**Why a fixed Inventory → Quote → Ordering sequence?**
Stock must be verified (and restocked if needed) before pricing, because the Quote Agent uses current stock levels when determining availability. Sales must be recorded after quoting, not before, so the quote price is always known before the transaction is committed.

---

## 2. Evaluation Results

The system was evaluated against all 20 requests in `quote_requests_sample.csv`. Results are documented in `test_results.csv`.

### Summary Statistics

| Metric | Result |
|---|---|
| Total requests processed | 20 / 20 |
| Requests with at least one fulfilled item | 16 |
| Requests with all items fulfilled | ~8 |
| Requests with partial or full non-fulfilment | ~12 |
| Cash balance changes (increases or decreases) | 14 |
| Starting cash balance | $45,059.70 |
| Ending cash balance | $44,716.15 |
| Starting inventory value | $4,940.30 |
| Ending inventory value | $4,944.85 |

### Strengths

**1. Correct bulk discount application**
The tiered discount logic in `calculate_quote` fired correctly across all requests. Request 3 (10,000 sheets of A4 paper + 500 sheets copy paper = 10,500 units) correctly applied a 20% discount. Request 17 (5,000 total units) correctly applied 20%. The discount tier is always reported in the customer response with the quantity that triggered it, satisfying the transparency requirement.

**2. Robust item name resolution**
Customer requests used a wide variety of descriptions ("recycled cardstock", "A4 glossy paper", "colored construction paper"). The combination of the catalog in the agent system prompt and the `_resolve_item_name` substring resolver meant the majority of these mapped correctly to catalog names in the database. For example, request 1 correctly resolved all three items and completed all three sale transactions.

**3. Cash and inventory track correctly across requests**
Cash and inventory values move in the expected directions: sales increase cash (request 1 cash rose from $45,059 to $45,109), restocks decrease cash and increase inventory (request 3 cash fell by ~$1,000 while inventory rose by ~$1,000). The database state carries over correctly between requests.

**4. Partial fulfilment handled gracefully**
When an order includes both in-stock and out-of-stock items, the system fulfils what it can and clearly reports what it cannot. Request 19 fulfilled 1,000 sheets of Cardstock while correctly reporting A4 Glossy Paper and A3 Matte Paper as unavailable. This is the correct behaviour — not treating partial availability as a full failure.

**5. All 4 mandatory response elements present in fulfilled requests**
For requests where items were available, the orchestrator consistently returned: itemised line items with unit prices and subtotals, the discount tier applied, estimated delivery dates, and an unfulfilled items section (or "None" where not applicable).

### Areas for Improvement

**1. Non-catalog item handling**
Some requests asked for items genuinely outside the catalog (e.g., "balloons", "streamers", "tickets", "flyers"). The system correctly reported these as unavailable, but in some cases the response lacked the full quote breakdown for the items that were available. Requests 2 and 20 were the most affected. The root cause is that the inventory agent cannot find these items and reports no stock, and the ordering agent then fails all sales.

**2. Date propagation inconsistency**
In a small number of cases (notably request 20), the inventory agent used an incorrect date (2023-10-27 instead of 2025-04-17) when querying the database. This caused the inventory query to return empty results and cash to read as $0.00, blocking all restocks. The orchestrator passed "Delivery date: 2025-05-15" rather than "Request date: 2025-04-17" to the inventory agent, and the LLM misread it. This is a prompt engineering issue in how the orchestrator frames its sub-agent calls.

---

## 3. Suggestions for Further Improvement

### Suggestion 1: Structured inter-agent payloads

Currently, agents communicate via plain-text strings, which means the orchestrator's LLM must parse the quote agent's output to extract item names and prices for the ordering agent. This re-parsing step introduces inconsistencies — in some requests the ordering agent received "flyers" or "heavy cardstock (white)" instead of the exact catalog names "Flyers" or "Cardstock", causing sale transactions to fail.

A targeted improvement would be to have the `calculate_quote` tool return — and the quote agent pass forward — a structured JSON payload (e.g., `[{"item_name": "Glossy paper", "quantity": 200, "unit_price": 0.20, "subtotal": 40.00}]`) that the orchestrator explicitly extracts and passes verbatim to the ordering agent. This would eliminate the LLM re-interpretation step for item names entirely, making sale recording deterministic rather than dependent on the model's text extraction quality.

### Suggestion 2: Catalog-aware item mapping tool

Rather than relying on the LLM to resolve customer descriptions to catalog names using only its training knowledge and the embedded catalog text, a dedicated `resolve_catalog_item(description)` tool could be added. This tool would use fuzzy string matching (e.g., the `difflib` or `rapidfuzz` library) against the `paper_supplies` list to return the best-matching catalog name along with a confidence score.

This would make item resolution deterministic and auditable, give agents a reliable fallback when descriptions are ambiguous, and produce better-reasoned responses for non-catalog items ("The closest item we carry to 'balloons' is 'Crepe paper' — would you like a quote for that instead?"). It would also reduce the size needed in system prompts, since the catalog lookup would be a tool call rather than embedded text.

### Suggestion 3 (bonus): Proactive restock threshold management

Currently, the inventory agent only restocks when the current stock for a specifically requested item drops below its minimum threshold. A smarter inventory agent could also run a periodic sweep of all catalog items (using `check_inventory`) at the start of each request cycle and proactively restock any item approaching its threshold — not just the items in the current request. This would prevent the scenario where a later request fails due to depletion caused by earlier requests that consumed most of the remaining stock.

---

## 4. Conclusion

The multi-agent system successfully processes all 20 test requests, applies deterministic bulk discount pricing, tracks cash and inventory state across requests, and handles partial fulfilment gracefully. The architecture — a sequential Orchestrator coordinating three specialised worker agents — maps cleanly onto the business domain and keeps each agent's decision scope narrow and auditable. The primary areas for improvement are in making inter-agent data passing more structured to reduce LLM re-interpretation errors, and in improving catalog item resolution for requests that use non-standard product descriptions.
