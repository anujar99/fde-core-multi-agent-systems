# Agent Interface Contracts

**Feature**: 001-paper-supply-agents
**Date**: 2026-03-20

All agents communicate exclusively via plain-text strings.
No structured objects cross agent boundaries.

---

## Orchestrator Agent

**Entry point** — called once per customer request from `run_test_scenarios()`.

```
Input:  str  — plain-text customer request including "(Date of request: YYYY-MM-DD)"
Output: str  — plain-text response to the customer
```

**Response MUST contain**:
1. Itemised quote: each line item with quantity, unit price, subtotal
2. Bulk discount tier applied and grand total
3. Estimated delivery date per fulfilled item
4. List of any unfulfilled items and reason (if applicable)

---

## Inventory Agent Tool (called by Orchestrator)

```
Input:  str  — task description including item names, quantities needed, and date
Output: str  — inventory status report listing each item, current stock,
               and any restock actions taken
```

### Tools exposed by Inventory Agent

| Tool | Input | Output |
|---|---|---|
| `check_inventory(as_of_date)` | date string | JSON: dict of item_name → stock count |
| `check_item_stock(item_name, as_of_date)` | item name + date | JSON: stock level, min level, needs_reorder flag |
| `restock_item(item_name, quantity, date)` | item name + qty + date | JSON: success flag, qty ordered, cost, delivery date |

---

## Quote Agent Tool (called by Orchestrator)

```
Input:  str  — task description including items, quantities, customer context, and date
Output: str  — professional quote with itemised breakdown and discount explanation
```

### Tools exposed by Quote Agent

| Tool | Input | Output |
|---|---|---|
| `get_historical_quotes(search_terms, limit)` | comma-separated keywords | JSON: list of matching historical quotes |
| `calculate_quote(items_json, as_of_date)` | JSON array of {item_name, quantity} + date | JSON: line items, subtotal, discount %, total |

---

## Ordering Agent Tool (called by Orchestrator)

```
Input:  str  — task description including items to sell, quantities, prices, and date
Output: str  — sales confirmation with transaction IDs and delivery dates
```

### Tools exposed by Ordering Agent

| Tool | Input | Output |
|---|---|---|
| `get_available_cash(as_of_date)` | date string | JSON: cash balance in USD |
| `complete_sale(item_name, quantity, total_price, date)` | item + qty + price + date | JSON: success flag, transaction ID, delivery date |

---

## Bulk Discount Tiers (deterministic, computed in `calculate_quote`)

| Total Order Quantity | Discount Applied |
|---|---|
| < 100 units | 0% |
| 100 – 499 units | 5% |
| 500 – 999 units | 10% |
| 1,000 – 4,999 units | 15% |
| 5,000+ units | 20% |

---

## Supplier Delivery Lead Times (from `get_supplier_delivery_date`)

| Quantity | Lead Time |
|---|---|
| ≤ 10 units | Same day |
| 11 – 100 units | 1 day |
| 101 – 1,000 units | 4 days |
| > 1,000 units | 7 days |
