---
description: "Task list for Paper Supply Multi-Agent System"
---

# Tasks: Paper Supply Multi-Agent System

**Input**: Design documents from `/specs/001-paper-supply-agents/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Note**: All implementation tasks target a single file: `project/project_starter.py`.
All code is added under the `# YOUR MULTI AGENT STARTS HERE` marker.
No new files are created except `requirements.txt` update.

---

## Phase 1: Setup

**Purpose**: Fix the pre-existing bug and wire in environment configuration
before any agent code is written.

- [ ] T001 Fix `init_database()` call on line 616 of `project/project_starter.py` — change to `init_database(db_engine)`
- [ ] T002 Add environment and model setup under `# YOUR MULTI AGENT STARTS HERE` in `project/project_starter.py`: `load_dotenv()`, instantiate `OpenAIServerModel` pointing to `https://openai.vocareum.com/v1` with `UDACITY_OPENAI_API_KEY`, set `MODEL = "gpt-4o-mini"`
- [ ] T003 Add `smolagents` to `project/requirements.txt`

---

## Phase 2: Foundational

**Purpose**: Implement all seven `@tool`-decorated functions that wrap the
provided helper functions. Every agent in every user story depends on these.
No agent can be built until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until all tools are complete.

- [ ] T004 [P] Implement `check_inventory(as_of_date)` tool wrapping `get_all_inventory()` in `project/project_starter.py` under `# Tools for inventory agent`
- [ ] T005 [P] Implement `check_item_stock(item_name, as_of_date)` tool wrapping `get_stock_level()` in `project/project_starter.py` under `# Tools for inventory agent`
- [ ] T006 Implement `restock_item(item_name, quantity, date)` tool wrapping `get_cash_balance()` + `create_transaction("stock_orders")` + `get_supplier_delivery_date()` in `project/project_starter.py` under `# Tools for inventory agent` — must verify cash before ordering
- [ ] T007 [P] Implement `get_historical_quotes(search_terms, limit)` tool wrapping `search_quote_history()` in `project/project_starter.py` under `# Tools for quoting agent`
- [ ] T008 Implement `calculate_quote(items_json, as_of_date)` tool in `project/project_starter.py` under `# Tools for quoting agent` — reads unit prices from `paper_supplies` list and `inventory` table, applies tiered bulk discounts deterministically (0/5/10/15/20%), returns itemised breakdown
- [ ] T009 [P] Implement `get_available_cash(as_of_date)` tool wrapping `get_cash_balance()` in `project/project_starter.py` under `# Tools for ordering agent`
- [ ] T010 Implement `complete_sale(item_name, quantity, total_price, date)` tool wrapping `get_stock_level()` + `create_transaction("sales")` + `get_supplier_delivery_date()` in `project/project_starter.py` under `# Tools for ordering agent` — must verify stock before recording sale

**Checkpoint**: All 7 tools written and callable independently. User story implementation can now begin.

---

## Phase 3: User Story 1 — Quote Generation (Priority: P1) 🎯 MVP

**Goal**: Orchestrator can receive a customer request and return an itemised
price quote with bulk discount and delivery estimate.

**Independent Test**: Submit one row from `quote_requests_sample.csv` directly
to the Orchestrator. Response must contain item list, per-line subtotals,
discount tier, grand total, and at least one delivery date.

- [ ] T011 [US1] Instantiate `quote_agent` as a `ToolCallingAgent` with tools `[get_historical_quotes, calculate_quote]`, `max_steps=15`, and a system prompt that embeds the full `paper_supplies` catalog for item name mapping in `project/project_starter.py`
- [ ] T012 [US1] Define `call_quote_agent(task)` as a `@tool`-decorated wrapper that calls `quote_agent.run(task)` in `project/project_starter.py`
- [ ] T013 [US1] Instantiate `orchestrator` as a `ToolCallingAgent` with tools `[call_quote_agent]`, `max_steps=15`, and a system prompt instructing it to delegate quoting and compose a final customer response in `project/project_starter.py`
- [ ] T014 [US1] Wire `orchestrator.run(request_with_date)` into `run_test_scenarios()` replacing the commented-out `response = call_your_multi_agent_system(request_with_date)` line in `project/project_starter.py`

**Checkpoint**: `run_test_scenarios()` runs without exceptions and all 19 responses contain a quote breakdown.

---

## Phase 4: User Story 2 — Inventory Check & Restock (Priority: P2)

**Goal**: Before quoting, the system checks stock for all requested items and
automatically restocks any item below its minimum threshold.

**Independent Test**: Trigger a request for an item known to be below minimum
stock. Verify a `stock_orders` transaction is recorded and the inventory value
in the financial report increases after the request.

- [ ] T015 [US2] Instantiate `inventory_agent` as a `ToolCallingAgent` with tools `[check_inventory, check_item_stock, restock_item]`, `max_steps=15`, and a system prompt that embeds the `paper_supplies` catalog and instructs it to restock items below minimum threshold in `project/project_starter.py`
- [ ] T016 [US2] Define `call_inventory_agent(task)` as a `@tool`-decorated wrapper that calls `inventory_agent.run(task)` in `project/project_starter.py`
- [ ] T017 [US2] Add `call_inventory_agent` to the Orchestrator's tool list and update the Orchestrator system prompt to sequence: Inventory Agent first, then Quote Agent in `project/project_starter.py`

**Checkpoint**: Inventory transactions appear in `test_results.csv` for requests where stock was insufficient. Cash balance decreases when restocks occur.

---

## Phase 5: User Story 3 — Finalise Sale (Priority: P3)

**Goal**: After quoting, the system records each line item as a completed sales
transaction, updating cash balance and inventory levels.

**Independent Test**: After processing one request end-to-end, verify that
`sales` transactions exist in the database for each fulfilled item, the cash
balance has increased, and inventory levels have decreased accordingly.

- [ ] T018 [US3] Instantiate `ordering_agent` as a `ToolCallingAgent` with tools `[get_available_cash, complete_sale]`, `max_steps=15`, and a system prompt instructing it to verify cash then record each line item as a sale in `project/project_starter.py`
- [ ] T019 [US3] Define `call_ordering_agent(task)` as a `@tool`-decorated wrapper that calls `ordering_agent.run(task)` in `project/project_starter.py`
- [ ] T020 [US3] Add `call_ordering_agent` to the Orchestrator's tool list and update the Orchestrator system prompt to sequence: Inventory → Quote → Ordering, and require the final response to include all four mandatory elements (itemised quote, discount, delivery dates, unfulfilled items) in `project/project_starter.py`

**Checkpoint**: All three user stories functional. `test_results.csv` shows changing cash and inventory values across requests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate end-to-end correctness, harden edge cases, and ensure
the submission meets all constitution and project requirements.

- [ ] T021 Review all agent system prompts to confirm every customer response will contain all four mandatory elements — itemised quote, bulk discount tier, delivery estimate, unfulfilled items — as required by Constitution Principle V in `project/project_starter.py`
- [ ] T022 Run `run_test_scenarios()` end-to-end and verify: `test_results.csv` has 19 non-empty rows, no raw exceptions in output, cash and inventory values change between requests
- [ ] T023 [P] Verify edge case handling in tool code: unknown item names return a graceful error string, `complete_sale` rejects sales with insufficient stock, `restock_item` rejects orders with insufficient cash in `project/project_starter.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **blocks all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational — no dependency on US2 or US3
- **User Story 2 (Phase 4)**: Depends on Foundational — no dependency on US1 or US3
- **User Story 3 (Phase 5)**: Depends on Foundational — integrates with US1 and US2 output but independently testable
- **Polish (Phase 6)**: Depends on all user stories being complete

### Parallel Opportunities Within Phases

```bash
# Phase 2 — these tools touch independent sections of the file:
T004  # check_inventory
T005  # check_item_stock
T007  # get_historical_quotes
T009  # get_available_cash

# T006, T008, T010 must be sequential (cash/stock validation logic is interdependent)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational tools (T004–T010)
3. Complete Phase 3: Quote Agent + Orchestrator (T011–T014)
4. **STOP and VALIDATE**: Run `run_test_scenarios()` — all 19 requests return a quote
5. Proceed to US2 and US3 only after MVP passes

### Incremental Delivery

1. Setup + Foundational → all tools in place
2. Add US1 (Quote) → Orchestrator returns quotes → **MVP**
3. Add US2 (Inventory) → Orchestrator checks and restocks stock before quoting
4. Add US3 (Ordering) → Orchestrator records sales after quoting
5. Polish → harden edge cases, validate full run

---

## Notes

- All tasks target `project/project_starter.py` — no new source files
- `[P]` tasks within Phase 2 can be written in parallel (they are independent tool functions)
- smolagents `@tool` decorator requires a docstring — every tool must have one
- Agent instantiation (T011, T015, T018) must happen at module level or inside a factory function called from `run_test_scenarios()`, not inside the tool wrappers
- The `paper_supplies` list is defined at the top of `project_starter.py` — reference it directly in tool and agent code; do not duplicate it
