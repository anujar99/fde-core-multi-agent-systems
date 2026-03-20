# Feature Specification: Paper Supply Multi-Agent System

**Feature Branch**: `001-paper-supply-agents`
**Created**: 2026-03-20
**Status**: Draft
**Input**: Build a multi-agent system for paper supply quotes, inventory management, and sales transactions for Beaver's Choice Paper Company.

## User Scenarios & Testing

### User Story 1 - Receive an Accurate Quote for Paper Supplies (Priority: P1)

A customer (office manager, school principal, event planner, restaurant manager, etc.)
submits a plain-text request describing the paper products they need, the quantities,
and their required delivery date. The system responds with a complete, itemised price
quote that includes any applicable bulk discount and a realistic delivery estimate.

**Why this priority**: Quoting is the entry point for every sale. Without an accurate,
professional quote the business cannot convert enquiries into revenue. All other
stories depend on a quote being generated first.

**Independent Test**: Submit any one row from the sample request dataset. Verify the
response contains an itemised breakdown, a total amount, a discount line (even if 0%),
and a delivery date — without any unhandled error.

**Acceptance Scenarios**:

1. **Given** a customer submits a request for multiple paper products with quantities,
   **When** the system processes the request,
   **Then** the response includes each requested item with its unit price, quantity,
   subtotal, the bulk discount tier applied, and a grand total in USD.

2. **Given** the total quantity across all line items meets a bulk discount threshold
   (100, 500, 1,000, or 5,000 units),
   **When** the quote is generated,
   **Then** the correct discount percentage is applied and the pre- and post-discount
   totals are both shown.

3. **Given** a customer requests an item that does not exist in the product catalogue,
   **When** the system processes the request,
   **Then** the response clearly states the item cannot be supplied and quotes only
   the items that can be fulfilled.

---

### User Story 2 - Automatic Inventory Check and Restocking (Priority: P2)

Before a quote is issued, the system checks whether sufficient stock exists to fulfil
the order. If any item is below the minimum stock threshold, the system automatically
places a supplier restock order — provided the company has sufficient cash — so that
the inventory is replenished in time to fulfil customer demand.

**Why this priority**: A quote that cannot be backed by available stock misleads the
customer. Proactive restocking ensures the business can honour its commitments and
avoids lost sales due to stockouts.

**Independent Test**: Trigger a request for an item whose stock is known to be below
its minimum threshold. Verify that a restock transaction is recorded and the subsequent
stock level reflects the new units added.

**Acceptance Scenarios**:

1. **Given** a requested item has stock below its minimum level,
   **When** the inventory check runs,
   **Then** a restock order is placed with the supplier for enough units to cover the
   customer order plus a safety buffer, and the restock is recorded as a transaction.

2. **Given** the company cash balance is insufficient to cover a restock order,
   **When** a restock is needed,
   **Then** the system records no stock transaction, and the quote response notes
   that the item may have limited availability.

3. **Given** all requested items have sufficient stock,
   **When** the inventory check runs,
   **Then** no restock order is placed and the system proceeds directly to quoting.

---

### User Story 3 - Finalise a Sale and Record the Transaction (Priority: P3)

Once a quote is generated and inventory is confirmed available, the system finalises
the sale by recording each line item as a completed sales transaction. The customer
receives a sales confirmation that includes transaction references and estimated
delivery dates for each item.

**Why this priority**: Recording the sale closes the revenue loop — it updates cash
balance, reduces inventory, and provides an auditable record. Without this step the
business cannot track actual revenue or inventory consumption.

**Independent Test**: After a quote is issued for in-stock items, verify that one
sales transaction per line item is recorded in the transaction log, the cash balance
increases by the quoted total, and the inventory levels decrease accordingly.

**Acceptance Scenarios**:

1. **Given** a quoted item has sufficient stock and the sale is confirmed,
   **When** the sale is finalised,
   **Then** a sales transaction is recorded for that item with the correct quantity
   and price, and an estimated delivery date is returned.

2. **Given** one or more line items have insufficient stock at the time of finalisation,
   **When** the sale is processed,
   **Then** only the items with available stock are sold and recorded, and the response
   clearly identifies the unfulfilled items and the reason.

3. **Given** a sale is finalised for multiple line items,
   **When** all transactions are recorded,
   **Then** the company cash balance and inventory levels both reflect all completed
   transactions accurately.

---

### Edge Cases

- What happens when the request contains an item name that only partially matches
  the product catalogue (e.g. "A3 paper" vs "Matte paper")?
- How does the system respond when the request date is missing or unparseable?
- What happens when the company has zero cash and restocking is required?
- How does the system handle a request for a quantity of zero or a negative quantity?
- What happens when all items in a request are out of stock and cannot be restocked?

## Requirements

### Functional Requirements

- **FR-001**: The system MUST accept a plain-text customer request describing products,
  quantities, and a required delivery date, and return a plain-text response.
- **FR-002**: The system MUST generate an itemised quote for every recognisable product
  in the request, showing unit price, quantity, subtotal, discount tier, and grand total.
- **FR-003**: The system MUST apply tiered bulk discounts based on total order quantity:
  0% for fewer than 100 units, 5% at 100, 10% at 500, 15% at 1,000, and 20% at 5,000.
- **FR-004**: The system MUST check current stock levels for all requested items before
  issuing a quote.
- **FR-005**: The system MUST automatically place a supplier restock order for any item
  below its minimum stock threshold, provided sufficient cash is available.
- **FR-006**: The system MUST verify the company cash balance before placing any restock
  order and MUST NOT place an order that would result in a negative cash balance.
- **FR-007**: The system MUST record every completed sale as a transaction, updating
  both the cash balance and inventory levels.
- **FR-008**: The system MUST provide an estimated delivery date for each fulfilled
  line item based on the order quantity.
- **FR-009**: The system MUST clearly communicate any items that cannot be fulfilled,
  along with the reason (unknown item, insufficient stock, insufficient cash).
- **FR-010**: The system MUST use historical quote data to inform pricing decisions
  for similar order types and event contexts.

### Key Entities

- **Customer Request**: A plain-text message containing requested products, quantities,
  required delivery date, and contextual information (job role, event type, order size).
- **Quote**: An itemised price breakdown for a customer request, including per-line
  subtotals, bulk discount applied, grand total, and delivery estimates.
- **Inventory Item**: A paper product in the catalogue with a current stock level,
  minimum stock threshold, and unit price.
- **Transaction**: A record of a stock order (restock) or sale, capturing item name,
  quantity, total price, and date.
- **Cash Balance**: The company's available funds, derived from the running total of
  all sales minus all stock purchase costs.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every customer request in the test dataset receives a response containing
  all four mandatory elements: itemised quote, discount tier, delivery estimate, and
  unfulfilled item report (even if empty).
- **SC-002**: Bulk discount tiers are applied correctly in 100% of quotes where the
  total quantity meets a threshold.
- **SC-003**: The company cash balance and inventory value reported after each processed
  request accurately reflect all transactions created during that request.
- **SC-004**: No customer request results in an unhandled error or raw exception
  being surfaced in the response.
- **SC-005**: Restock orders are placed automatically for all items below minimum
  stock threshold whenever sufficient cash is available, with no manual intervention.
- **SC-006**: The end-to-end processing of all 19 sample requests completes without
  any request being silently skipped or returning an empty response.

## Assumptions

- A customer request that is processed by the system is treated as a confirmed order
  intent; the system will both quote and attempt to finalise the sale in one pass.
- Items requested that have no match in the product catalogue are excluded from the
  quote with an explanatory note; no partial-name fuzzy matching is required.
- The system processes one request at a time sequentially; concurrent requests are
  out of scope.
- Delivery date estimates are calculated from the request date, not a separate
  confirmed shipment date.
- The initial cash balance and starting inventory are seeded by the database
  initialisation process; the system does not manage initial setup.
