# Quickstart: Paper Supply Multi-Agent System

**Feature**: 001-paper-supply-agents
**Date**: 2026-03-20

## Prerequisites

1. Python 3.8+ installed
2. Working directory: `project/` (all CSV files must be present)
3. `.env` file in `project/` containing:
   ```
   UDACITY_OPENAI_API_KEY=your_key_here
   ```
4. Dependencies installed:
   ```
   pip install -r requirements.txt
   pip install smolagents
   ```

## Running the System

```bash
cd project/
python project_starter.py
```

This runs `run_test_scenarios()` which:
1. Calls `init_database(db_engine)` to seed a fresh SQLite database
2. Loads all 19 requests from `quote_requests_sample.csv`
3. Passes each request to the Orchestrator agent
4. Prints per-request cash balance, inventory value, and agent response
5. Saves all results to `test_results.csv`
6. Prints a final financial report

## Expected Output Per Request

```
=== Request N ===
Context: [job] organizing [event]
Request Date: YYYY-MM-DD
Cash Balance: $XXXXX.XX
Inventory Value: $XXXXX.XX
Response: Thank you for your order...
  - [Item]: [qty] x $[unit] = $[subtotal]
  - ...
  Discount applied: X% (total qty: N units)
  Grand total: $XXXXX.XX
  Estimated delivery: YYYY-MM-DD
Updated Cash: $XXXXX.XX
Updated Inventory: $XXXXX.XX
```

## Verifying Correctness

After running, check `test_results.csv` for:
- All 19 rows populated (no blank responses)
- `cash_balance` changes between requests (sales are being recorded)
- `inventory_value` changes between requests (stock is being consumed and restocked)

Final report should show non-zero cash and inventory values.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `TypeError: init_database()` | Bug in starter code | Ensure call is `init_database(db_engine)` |
| `UDACITY_OPENAI_API_KEY` not found | Missing `.env` file | Create `.env` with the key |
| Empty responses | Agent max_steps hit | Check agent system prompt is focused |
| Wrong item names in transactions | Catalog mismatch | Ensure catalog is in agent system prompt |
