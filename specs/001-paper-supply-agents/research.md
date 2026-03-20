# Research: Paper Supply Multi-Agent System

**Feature**: 001-paper-supply-agents
**Date**: 2026-03-20

## Decision 1: Agent Framework

**Decision**: smolagents with `ToolCallingAgent` and `OpenAIServerModel`

**Rationale**: smolagents v1.24.0 is already installed in the environment and is the
framework used consistently across all 7 course lessons. It provides the `@tool`
decorator, `ToolCallingAgent`, and `OpenAIServerModel` — exactly the pattern
demonstrated in lessons 2–6. The project's `requirements.txt` already includes the
`openai` SDK which smolagents uses under the hood.

**Alternatives considered**:
- *pydantic-ai*: Valid option but not used in the course; would require additional installation and a steeper learning curve relative to available examples.
- *Direct OpenAI function calling*: Would work with existing `openai` SDK but bypasses the `@tool` decorator pattern established in the course, making the code less consistent with lesson patterns.

---

## Decision 2: Item Name Mapping Strategy

**Decision**: Pass the full `paper_supplies` catalog list as context in the Inventory
and Quote agent system prompts so the LLM can map fuzzy customer request names to
exact catalog names before calling any tool.

**Rationale**: Customer requests use natural language descriptions ("heavy cardstock",
"A3 glossy paper") that may not exactly match catalog names ("Cardstock", "Glossy paper").
Rather than building a separate fuzzy-matching tool, embedding the catalog in the
system prompt leverages the LLM's natural language understanding at zero extra tool cost.

**Alternatives considered**:
- *Fuzzy string matching tool (e.g. difflib)*: Deterministic but brittle for semantic differences (e.g. "poster board" vs "Large poster paper (24x36 inches)").
- *Separate catalogue-lookup tool*: Adds an extra LLM round-trip for every item; the catalog is small enough (42 items) to fit comfortably in the system prompt.

---

## Decision 3: Orchestrator Sub-Agent Calling Pattern

**Decision**: Wrap each sub-agent's `.run()` call inside a `@tool`-decorated function
on the Orchestrator agent, so the Orchestrator can delegate via tool calls.

**Rationale**: This is the pattern demonstrated in lesson 6 (Italian Pasta Factory),
where the orchestrator called specialist agents as tools. It keeps the Orchestrator
within the standard `ToolCallingAgent` loop and avoids any custom routing logic.

**Alternatives considered**:
- *Hardcoded sequential calls in Python*: Simpler but removes the Orchestrator's ability to reason about which agents to call and in what order based on request content.
- *Shared message queue*: Overkill for a single-threaded single-file script.

---

## Decision 4: Bug Fix — `init_database()` Call

**Decision**: Fix `run_test_scenarios()` to call `init_database(db_engine)` instead
of `init_database()`.

**Rationale**: The starter code calls `init_database()` with no arguments, but the
function signature requires `db_engine` as its first positional argument. This causes
a `TypeError` at runtime before any agent code executes. The fix is a one-line change.

**Alternatives considered**: None — this is a straightforward bug fix with no alternatives.

---

## Decision 5: Model Selection

**Decision**: `gpt-4o-mini` via the Udacity OpenAI-compatible proxy at `https://openai.vocareum.com/v1`

**Rationale**: This is the model used in all course lesson demos and is the only
model guaranteed to be available on the Udacity platform. The API key is read from
`UDACITY_OPENAI_API_KEY` in the `.env` file as per the project README.

**Alternatives considered**: None — constrained by the platform.
