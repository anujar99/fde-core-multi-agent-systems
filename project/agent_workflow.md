## Simplified Overview

```mermaid
flowchart TD
    USER([Customer Request]) --> ORCH[Orchestrator Agent]
    ORCH --> INV[Inventory Agent]
    ORCH --> QUOTE[Quote Agent]
    ORCH --> SALES[Sales Agent]
    ORCH --> RESP([Customer Response])
    INV <--> DB[(SQLite Database)]
    QUOTE <--> DB
    SALES <--> DB

    style ORCH  fill:#4a90d9,color:#fff,stroke:#2c5f8a
    style INV   fill:#27ae60,color:#fff,stroke:#1a7a42
    style QUOTE fill:#e67e22,color:#fff,stroke:#b35c0f
    style SALES fill:#8e44ad,color:#fff,stroke:#5e2d72
    style DB    fill:#ecf0f1,color:#333,stroke:#bdc3c7
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
    ORCH -->|"3 · Finalize sale"| SALES
    ORCH --> RESP([Customer Response])

    subgraph INV["📦 Inventory Agent"]
        direction TB
        I1["get_catalog()"]
        I2["get_all_inventory(date)"]
        I3["check_item_stock(item, date)"]
        I4["reorder_item(item, qty, date)"]
    end

    subgraph QUOTE["💰 Quote Agent"]
        direction TB
        Q1["get_catalog()"]
        Q2["search_quote_history(terms)"]
        Q3["calculate_quote(items_json, date)"]
        Q4["get_item_price(item)"]
    end

    subgraph SALES["🧾 Sales Agent"]
        direction TB
        S1["get_cash_balance(date)"]
        S2["finalize_sale(item, qty, price, date)"]
    end

    subgraph DB["🗄️ SQLite Database (munder_difflin.db)"]
        T1[(inventory)]
        T2[(transactions)]
        T3[(quotes)]
        T4[(quote_requests)]
    end

    INV <--> DB
    QUOTE <--> DB
    SALES <--> DB

    style ORCH  fill:#4a90d9,color:#fff,stroke:#2c5f8a
    style INV   fill:#27ae60,color:#fff,stroke:#1a7a42
    style QUOTE fill:#e67e22,color:#fff,stroke:#b35c0f
    style SALES fill:#8e44ad,color:#fff,stroke:#5e2d72
    style DB    fill:#ecf0f1,color:#333,stroke:#bdc3c7
```

## Agent Roles

| Agent | Role | Key Responsibility |
|---|---|---|
| **Orchestrator** | Operations Director | Routes requests; sequences Inventory → Quote → Sales calls |
| **Inventory** | Stock Manager | Verifies availability; auto-restocks when below `min_stock_level` |
| **Quote** | Pricing Specialist | Pulls historical quotes; applies tiered bulk discounts (5/10/15/20%) |
| **Sales** | Transaction Manager | Records sales in `transactions` table; provides delivery ETAs |

## Request Flow

```
Customer Request
    │
    ▼
Orchestrator: parse items + quantities + date
    │
    ├─1─▶ Inventory Agent
    │       ├─ get_catalog()               ← find exact item names
    │       ├─ get_all_inventory(date)     ← see what's in stock
    │       ├─ check_item_stock(item,date) ← verify per-item levels
    │       └─ reorder_item(...)           ← restock if below minimum
    │
    ├─2─▶ Quote Agent
    │       ├─ search_quote_history(terms) ← calibrate from past quotes
    │       ├─ get_item_price(item)        ← look up unit prices
    │       └─ calculate_quote(items,date) ← apply bulk discounts
    │
    ├─3─▶ Sales Agent
    │       ├─ get_cash_balance(date)      ← verify company has capacity
    │       └─ finalize_sale(×N items)     ← record each line as transaction
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
