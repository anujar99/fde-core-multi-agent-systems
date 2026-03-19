<!--
SYNC IMPACT REPORT
==================
Version change  : N/A → 1.0.0 (initial ratification)
Modified        : none (first version)
Added sections  : Core Principles (I–V), Performance & LLM Efficiency,
                  Testing & Validation Standards, Governance
Removed sections: none
Templates checked:
  ✅ .specify/templates/plan-template.md  — Constitution Check gate aligns with all five principles
  ✅ .specify/templates/spec-template.md  — Edge Cases section aligns with Principle V; User Stories align with Principle III
  ✅ .specify/templates/tasks-template.md — Phase structure aligns with Principle II sequencing; test tasks align with Principle V
Deferred TODOs  : none
-->

# Beaver's Choice Paper Company Multi-Agent System Constitution

## Core Principles

### I. Agent Specialization

Each agent MUST have a single, well-defined responsibility. Tool sets are scoped exclusively
to that role — no agent may hold tools that belong to another agent's domain.
The system MUST contain no more than five agents in total.
Agents MUST NOT call each other directly; all inter-agent coordination is the sole
responsibility of the Orchestrator.

**Rationale**: Lessons 2–6 consistently demonstrated that focused agents with narrow tool
sets produce more reliable, debuggable outputs than generalist agents. Scope creep in tool
assignment is the leading cause of unpredictable LLM tool selection.

### II. Orchestrator-Driven Coordination

A single Orchestrator agent MUST receive every customer request and sequence sub-agent
calls in this order: Inventory Agent → Quote Agent → Ordering Agent.
No peer-to-peer agent communication is permitted.
The Orchestrator owns the final customer-facing response; sub-agents return structured
results to the Orchestrator only.

**Rationale**: The orchestrator pattern (Lessons 3–6) isolates routing logic, makes the
workflow auditable, and prevents cascading failures caused by uncontrolled agent chaining.

### III. Tool-First Design

All agent capabilities MUST be implemented as `@tool`-decorated functions.
Every tool MUST have a complete docstring specifying Args and Returns.
Tools MUST wrap the provided helper functions (`create_transaction`, `get_all_inventory`,
`get_stock_level`, `get_cash_balance`, `get_supplier_delivery_date`, `search_quote_history`)
rather than re-implementing equivalent logic.
No tool may perform direct SQL outside the provided helpers.

**Rationale**: Lessons 2–7 established that tool-decorated functions with clear contracts
are the fundamental unit of agent capability. Wrapping helpers enforces a single source
of truth for business logic and avoids divergent implementations.

### IV. Transaction Integrity

All inventory and financial state changes MUST be recorded via `create_transaction()`.
`get_cash_balance()` MUST be called and confirmed sufficient before any `stock_orders`
transaction is created.
Item names passed to any tool MUST exactly match entries in the `paper_supplies` catalog
or the `inventory` table — fuzzy or approximate names are not permitted in transactions.
All database queries MUST use `as_of_date` scoping to maintain temporal consistency.

**Rationale**: Lessons 5–6 showed that shared mutable state without explicit transaction
logging leads to inconsistent snapshots and untraceable bugs. The `as_of_date` pattern
is required by the provided helpers and MUST not be bypassed.

### V. Validated Text I/O

All agent inputs and outputs MUST be plain text strings — no structured objects may
cross agent boundaries.
Every customer-facing response MUST include all four of the following elements:
  1. An itemised quote with per-line unit price, quantity, and subtotal.
  2. The bulk discount tier applied (0 / 5 / 10 / 15 / 20 %) and total after discount.
  3. An estimated delivery date for each fulfilled line item.
  4. A list of any unfulfilled items and the reason (insufficient stock, unknown item, etc.).
All monetary amounts MUST be formatted in USD with two decimal places.
All dates MUST be formatted as YYYY-MM-DD.

**Rationale**: The project specification mandates text-based I/O. Standardised response
structure ensures customers always receive actionable information and makes agent output
mechanically testable via `run_test_scenarios()`.

## Performance & LLM Efficiency

- Every agent runner MUST enforce a maximum iteration cap (MUST NOT exceed 15 LLM calls
  per agent invocation) to prevent runaway loops.
- Agents MUST be given focused, fully-scoped task strings by the Orchestrator to minimise
  redundant LLM reasoning steps.
- Failed database operations MUST NOT be retried in a loop; the tool MUST return a
  structured error string and let the agent decide how to proceed.
- Bulk discount tiers MUST be computed deterministically in tool code, not delegated to
  LLM reasoning:

  | Total Units | Discount |
  |-------------|----------|
  | < 100       | 0%       |
  | ≥ 100       | 5%       |
  | ≥ 500       | 10%      |
  | ≥ 1,000     | 15%      |
  | ≥ 5,000     | 20%      |

## Testing & Validation Standards

- All agent code MUST pass `run_test_scenarios()` using the full `quote_requests_sample.csv`
  dataset without unhandled exceptions.
- The following edge cases MUST be handled gracefully (human-readable response, no raw
  exception propagation):
    - Requested item not present in the `inventory` table or `paper_supplies` list.
    - Requested quantity exceeds current stock and restock fails due to insufficient cash.
    - Cash balance is zero or negative at the time of an order.
    - Malformed or missing date in the customer request.
- State assertions MUST be verifiable after each test scenario: cash balance and inventory
  value reported by `generate_financial_report()` MUST reflect all transactions created
  during that scenario.
- `init_database(db_engine)` MUST be called once at the start of `run_test_scenarios()`
  to ensure a clean, reproducible database state for every test run.

## Governance

- This constitution supersedes all other development guidelines for this project.
- Amendments require: (1) a written rationale, (2) a version bump following semver rules
  (MAJOR for principle removal or redefinition; MINOR for new principle or section;
  PATCH for clarifications and wording), and (3) an updated Sync Impact Report.
- All implementation work MUST pass a Constitution Check against Principles I–V before
  any feature is considered complete.
- Complexity that violates a principle (e.g., direct agent-to-agent calls) MUST be
  explicitly justified in the plan's Complexity Tracking table and approved before
  implementation begins.
- Compliance is reviewed at each checkpoint defined in `tasks.md`.

**Version**: 1.0.0 | **Ratified**: 2026-03-20 | **Last Amended**: 2026-03-20
