# Implementation Plan: Paper Supply Multi-Agent System

**Branch**: `001-paper-supply-agents` | **Date**: 2026-03-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-paper-supply-agents/spec.md`

## Summary

Build a 4-agent orchestrated system inside a single Python file (`project_starter.py`)
that processes plain-text paper supply requests end-to-end: checking and restocking
inventory, generating itemised bulk-discounted quotes, and finalising sales transactions
against a SQLite database — all verified by the existing `run_test_scenarios()` harness.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: smolagents 1.24.0 (`ToolCallingAgent`, `OpenAIServerModel`, `@tool`), openai 1.76.0, SQLAlchemy 2.0.40, pandas 2.2.3, python-dotenv 1.1.0
**Storage**: SQLite (`munder_difflin.db`) via SQLAlchemy engine; all access through provided helper functions
**Testing**: `run_test_scenarios()` in `project_starter.py` using `quote_requests_sample.csv` (19 requests)
**Target Platform**: Linux, single-file script executed from `project/` directory
**Project Type**: Single Python file (all agent logic appended to `project_starter.py`)
**Performance Goals**: All 19 sample requests processed without timeout; no unhandled exceptions
**Constraints**: Max 5 agents total; single Python file output; text I/O only; max 15 LLM iterations per agent invocation; smolagents `ToolCallingAgent` pattern throughout
**Scale/Scope**: 19 test requests, 42-item product catalogue, 4 agents, ~16 items seeded in inventory at runtime

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status |
|---|---|---|
| I. Agent Specialization | Max 5 agents; each with single role and scoped tool set; no direct agent-to-agent calls | ✅ 4 agents, each has distinct tools |
| II. Orchestrator-Driven Coordination | Orchestrator sequences Inventory then Quote then Ordering; owns final response | ✅ Orchestrator delegates via sub-agent tool wrappers |
| III. Tool-First Design | All capabilities as @tool functions wrapping provided helpers; no raw SQL | ✅ All 7 tools wrap helper functions |
| IV. Transaction Integrity | create_transaction() for all state changes; cash check before stock orders; as_of_date scoping | ✅ enforced in restock_item and complete_sale tools |
| V. Validated Text I/O | Plain text I/O; responses include itemised quote + discount + delivery + unfulfilled items | ✅ enforced in agent system prompts and response format |
| Performance | Max 15 iterations per agent; deterministic discount tiers in tool code | ✅ max_steps=15 on all agents; discount logic in calculate_quote tool |
| Testing | Must pass run_test_scenarios(); init_database(db_engine) called once | ✅ bug fix included; all edge cases handled in tools |

**Gate result**: All principles satisfied. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-paper-supply-agents/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── agent-interface.md   # Phase 1 output
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code

```text
project/
├── project_starter.py   # Single submission file — all agent code appended below
│                        # "YOUR MULTI AGENT STARTS HERE" marker
├── munder_difflin.db    # Generated at runtime by init_database()
├── quote_requests.csv
├── quote_requests_sample.csv
├── quotes.csv
└── requirements.txt
```

**Structure Decision**: Single-file pattern required by project spec. All agent code
is added to `project_starter.py` under the existing `# YOUR MULTI AGENT STARTS HERE`
marker. No new files are created.

## Complexity Tracking

No constitution violations. No complexity justification required.
