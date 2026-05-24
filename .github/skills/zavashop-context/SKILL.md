---
name: zavashop-context
description: ZavaShop domain knowledge — product catalog schema, SKU format, warehouse codes, order lifecycle states, supply-chain entities, and locations of the workshop's sample data files. Use whenever a task references ZavaShop, Zava products, Zava warehouses, Zava orders, retail or supply-chain scenarios in this workshop.
license: MIT
metadata:
  author: ZavaShop Workshop
  version: "1.0.0"
---

# ZavaShop Domain Skill

ZavaShop is the fictional retailer used throughout this workshop. This skill defines the domain vocabulary, data shapes, and where to find the sample data.

## Company at a Glance

- **Industry**: Beauty, skincare, and lifestyle products.
- **Footprint**: 5 distribution warehouses (Seattle, Singapore, London, Dubai, São Paulo).
- **Channels**: Online retail (zavashop.com), 80+ physical pop-up stores.
- **Two operational halves**:
  - **Retail** — customer-facing: catalog, search, orders, returns.
  - **Supply Chain** — internal: demand forecast, supplier POs, logistics, warehouse rebalancing.

## SKU Format

`<CAT>-<NNN>` — three-letter category code, hyphen, three-digit serial.

| Category code | Meaning |
| --- | --- |
| `LIP` | Lipstick |
| `FND` | Foundation |
| `SKN` | Skincare |
| `FRG` | Fragrance |
| `TOL` | Tools (brushes, mirrors) |

Examples: `LIP-001`, `FND-014`, `SKN-027`.

## Warehouse Codes

| Code | Name | Region | Currency |
| --- | --- | --- | --- |
| `WH-SEA` | Seattle DC | North America | USD |
| `WH-SIN` | Singapore DC | APAC | SGD |
| `WH-LON` | London DC | EMEA | GBP |
| `WH-DXB` | Dubai DC | MEA | AED |
| `WH-GRU` | São Paulo DC | LATAM | BRL |

Stock is region-specific; a SKU may be in `WH-SEA` but out of stock in `WH-LON`.

## Order Lifecycle

Orders move through these states (case-sensitive on the wire):

```
DRAFT → PLACED → RESERVED → SHIPPED → DELIVERED
                       ↓
                     CANCELED
```

- `RESERVED` means the inventory hold succeeded.
- `CANCELED` is terminal and may happen from `PLACED` or `RESERVED` (stock is released).
- Returns generate a new order with state `RETURNED` (out of scope for the workshop).

## Sample Data Files

All workshop tools must read from these files — **do not invent SKUs or stock numbers**.

| Path | Contents |
| --- | --- |
| `data/zava_catalog.json` | `{"products": [{"sku", "name", "category", "price_usd", "description", "tags"}]}` |
| `data/zava_warehouses.json` | `{"warehouses": [{"code", "name", "region", "currency", "stock": {SKU: units}}]}` |
| `data/zava_orders.sample.json` | `{"orders": [{"order_id", "customer_id", "state", "lines": [...], "warehouse"}]}` |

Read them with a tiny helper at the top of any tool file:

```python
from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def load_catalog() -> dict:
    return json.loads((DATA_DIR / "zava_catalog.json").read_text())

def load_warehouses() -> dict:
    return json.loads((DATA_DIR / "zava_warehouses.json").read_text())
```

Adjust `parents[N]` so the path resolves to the workshop's `data/` regardless of which lab folder calls it.

## Domain-Specific Roles (used in multi-agent labs)

Use these role names verbatim when naming agents/executors in Lab 4:

**Retail workflow**
- `ProductAdvisor` — answers product questions, recommends SKUs.
- `InventoryChecker` — verifies stock per warehouse.
- `OrderProcessor` — creates the order, transitions state `PLACED → RESERVED`.
- `ShipmentTrigger` — books an outbound shipment.

**Supply-chain workflow**
- `DemandForecaster` — predicts next-week demand per SKU.
- `SupplierSelector` — picks a supplier from `data/zava_suppliers.json` (if present).
- `PurchaseOrderAgent` — emits a structured PO.
- `LogisticsCoordinator` — schedules inbound transport.
- `InventoryUpdater` — increments warehouse stock once received.

## Currency & Pricing

- Catalog prices are in USD (`price_usd`).
- Per-warehouse prices are derived: multiply by a static factor in `data/zava_fx.json` if you need a regional price. Default factor 1.0 for `WH-SEA`.
- Never claim a price the catalog does not list.

## Style Rules for Generated Code

- Functions that look up products/warehouses are named `get_<noun>` (e.g. `get_product`, `get_warehouse_stock`).
- Functions that mutate (orders, stock) are named `<verb>_<noun>` (e.g. `place_order`, `reserve_units`).
- Error returns are strings of the form `"NOT_FOUND: <sku>"`, `"OUT_OF_STOCK: <sku>@<warehouse>"`. Tools never raise to the LLM — they return a structured failure string.

## Things That Are NOT ZavaShop

- Real Zava Inc. or any actual retailer — this is a teaching scenario.
- Any payment / PII processing — assume that's handled outside the agent boundary.
- Live external APIs — every "external" service in the workshop is a JSON file or a local MCP server.
