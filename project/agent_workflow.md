## Simplified Overview

```mermaid
flowchart TD
    USER([Customer Request]) --> ORCH[Orchestrator Agent]
    ORCH --> INV[Inventory Agent]
    ORCH --> QUOTE[Quote Agent]
    ORCH --> ORDERS[Ordering Agent]
    ORCH --> RESP([Customer Response])
    INV <--> DB[(SQLite Database)]
    QUOTE <--> DB
    ORDERS <--> DB

    style ORCH   fill:#4a90d9,color:#fff,stroke:#2c5f8a
    style INV    fill:#27ae60,color:#fff,stroke:#1a7a42
    style QUOTE  fill:#e67e22,color:#fff,stroke:#b35c0f
    style ORDERS fill:#8e44ad,color:#fff,stroke:#5e2d72
    style DB     fill:#ecf0f1,color:#333,stroke:#bdc3c7
```

## Detailed Diagram

```mermaid
flowchart TD
    USER([Customer Request]) --> ORCH

    subgraph ORCH["🎯 Orchestrator Agent\n(Operations Director)"]
        O1[Parse request\nitems · quantities · date]
    end

    ORCH -->|"1 · Check & restock inventory"| INV
    ORCH -->|"2 · Generate price quote"| QUOTE
    ORCH -->|"3 · Finalize sale"| ORDERS
    ORCH --> RESP([Customer Response])

    subgraph INV["📦 Inventory Agent"]
        direction TB
        I1["check_inventory(as_of_date)\n→ get_all_inventory()"]
        I2["check_item_stock(item_name, as_of_date)\n→ get_stock_level()"]
        I3["restock_item(item_name, qty, date)\n→ get_cash_balance()\n→ create_transaction('stock_orders')\n→ get_supplier_delivery_date()"]
    end

    subgraph QUOTE["💰 Quote Agent"]
        direction TB
        Q1["get_historical_quotes(search_terms, limit)\n→ search_quote_history()"]
        Q2["calculate_quote(items, date)\n→ paper_supplies pricing\n→ get_stock_level()\n→ bulk discount logic"]
    end

    subgraph ORDERS["🧾 Ordering Agent"]
        direction TB
        S1["get_available_cash(date)\n→ get_cash_balance()"]
        S2["complete_sale(item_name, qty, price, date)\n→ get_stock_level()\n→ create_transaction('sales')\n→ get_supplier_delivery_date()"]
        S3["get_financial_summary(date)\n→ generate_financial_report()"]
    end

    subgraph DB["🗄️ SQLite Database (munder_difflin.db)"]
        T1[(inventory)]
        T2[(transactions)]
        T3[(quotes)]
        T4[(quote_requests)]
    end

    INV <--> DB
    QUOTE <--> DB
    ORDERS <--> DB

    style ORCH   fill:#4a90d9,color:#fff,stroke:#2c5f8a
    style INV    fill:#27ae60,color:#fff,stroke:#1a7a42
    style QUOTE  fill:#e67e22,color:#fff,stroke:#b35c0f
    style ORDERS fill:#8e44ad,color:#fff,stroke:#5e2d72
    style DB     fill:#ecf0f1,color:#333,stroke:#bdc3c7
```

## Agent Roles

| Agent | Role | Key Responsibility |
|---|---|---|
| **Orchestrator** | Operations Director | Routes requests; sequences Inventory → Quote → Ordering calls |
| **Inventory** | Stock Manager | Verifies availability; auto-restocks via `create_transaction('stock_orders')` when needed |
| **Quote** | Pricing Specialist | Pulls historical quotes via `search_quote_history()`; applies tiered bulk discounts |
| **Ordering** | Transaction Manager | Confirms cash via `get_cash_balance()`; records sales via `create_transaction('sales')` |

## Request Flow

```
Customer Request
    │
    ▼
Orchestrator: parse items + quantities + date
    │
    ├─1─▶ Inventory Agent
    │       ├─ check_inventory(date)          → get_all_inventory()
    │       ├─ check_item_stock(item, date)   → get_stock_level()
    │       └─ restock_item(item, qty, date)  → get_cash_balance()
    │                                         → create_transaction('stock_orders')
    │                                         → get_supplier_delivery_date()
    │
    ├─2─▶ Quote Agent
    │       ├─ get_historical_quotes(terms)   → search_quote_history()
    │       └─ calculate_quote(items, date)   → paper_supplies pricing
    │                                         → get_stock_level()
    │                                         → bulk discount tiers
    │
    ├─3─▶ Ordering Agent
    │       ├─ get_available_cash(date)       → get_cash_balance()
    │       ├─ complete_sale(item, qty, price, date)
    │       │                                 → get_stock_level()
    │       │                                 → create_transaction('sales')
    │       │                                 → get_supplier_delivery_date()
    │       └─ get_financial_summary(date)    → generate_financial_report()
    │
    └─▶ Final response to customer
            (quote breakdown + delivery dates + any unfulfilled items)
```

## Bulk Discount Tiers

| Total Units | Discount |
|---|---|
| < 100 | 0% |
| ≥ 100 | 5% |
| ≥ 500 | 10% |
| ≥ 1,000 | 15% |
| ≥ 5,000 | 20% |
