# Data Model: Paper Supply Multi-Agent System

**Feature**: 001-paper-supply-agents
**Date**: 2026-03-20

All entities are persisted in `munder_difflin.db` (SQLite). The database is
initialised once per test run by `init_database(db_engine)`.

---

## Entities

### InventoryItem

Represents a paper product available in the catalogue and currently tracked in stock.

| Field | Type | Description |
|---|---|---|
| item_name | TEXT (PK) | Exact product name from the `paper_supplies` catalog |
| category | TEXT | Product category: `paper`, `product`, `large_format`, `specialty` |
| unit_price | REAL | Price per unit in USD |
| current_stock | INTEGER | Units in stock (derived from transactions, not stored directly) |
| min_stock_level | INTEGER | Threshold below which a restock order is triggered |

**Notes**:
- `current_stock` is always computed via `get_stock_level()` or `get_all_inventory()` from the `transactions` table — it is never read directly from an `inventory` column at query time.
- Only ~40% of the 42 catalog items are seeded into inventory (seed=137); the rest are catalogue-only.

---

### Transaction

An immutable record of either a stock purchase (restock) or a sale.

| Field | Type | Description |
|---|---|---|
| id | INTEGER (PK, auto) | Auto-incremented row ID |
| item_name | TEXT | Catalog item name; NULL for the opening cash seed record |
| transaction_type | TEXT | Either `stock_orders` (restock) or `sales` |
| units | INTEGER | Quantity involved; NULL for the opening cash seed record |
| price | REAL | Total monetary value of the transaction in USD |
| transaction_date | TEXT | ISO 8601 date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) |

**State transitions**:
- A `stock_orders` transaction increases effective stock for `item_name`.
- A `sales` transaction decreases effective stock for `item_name` and increases cash balance.
- Cash balance = SUM(sales.price) - SUM(stock_orders.price) up to `as_of_date`.

**Validation rules**:
- `transaction_type` MUST be one of `stock_orders` or `sales`.
- A `sales` transaction MUST NOT be created if `get_stock_level()` returns less than the requested units.
- A `stock_orders` transaction MUST NOT be created if `get_cash_balance()` is less than the total cost.

---

### Quote (historical reference)

A record of a previously generated quote, used by the Quote Agent to calibrate pricing.

| Field | Type | Description |
|---|---|---|
| request_id | INTEGER (PK) | Links to the corresponding QuoteRequest |
| total_amount | REAL | Total quoted amount in USD |
| quote_explanation | TEXT | Natural language explanation of the pricing |
| order_date | TEXT | ISO 8601 date the quote was generated |
| job_type | TEXT | Role of the customer (e.g. `event manager`, `school teacher`) |
| order_size | TEXT | Size classification: `small`, `medium`, `large` |
| event_type | TEXT | Context of the order (e.g. `ceremony`, `party`, `exhibition`) |

---

### QuoteRequest (historical reference)

The original customer request text paired with each historical Quote.

| Field | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-incremented row ID |
| response | TEXT | Original customer request text |

---

## Relationships

```
QuoteRequest (1) ──── (1) Quote
     id         request_id

InventoryItem (1) ──── (N) Transaction
   item_name              item_name
```

---

## Derived Values

| Value | Derived From | Function |
|---|---|---|
| Current stock for an item | Transactions up to `as_of_date` | `get_stock_level(item_name, date)` |
| Full inventory snapshot | All transactions up to `as_of_date` | `get_all_inventory(date)` |
| Cash balance | Sales minus stock_orders up to `as_of_date` | `get_cash_balance(date)` |
| Supplier delivery date | Request date + quantity-based lead time | `get_supplier_delivery_date(date, qty)` |
