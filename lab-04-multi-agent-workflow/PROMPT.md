# Lab 4 — Task Prompt

> **Paste the content of this file into a GitHub Issue (or `@copilot` comment) in your fork to start the Coding Agent.**

## Assignment

Assign this task to the **`zava-workflow-architect`** custom agent.

> @copilot assign zava-workflow-architect to this task

The agent profile lives at [`.github/agents/zava-workflow-architect.md`](../.github/agents/zava-workflow-architect.md). It already knows the executor / builder / handoff patterns for **both Python and C#** and which skills to read. **Do not repeat that here.**

## Language Directive

```
target_language: both
```

Allowed values: `python`, `csharp`, `both`. The agent reads only the matching workflow skill (`agent-framework-workflows-py` or `agent-framework-workflows-csharp`) plus the matching Copilot SDK skill, and scaffolds only the matching files. When `both`, deliver Python at the lab root *and* C# under `csharp/`.

## Goal

Deliver **two** MAF Workflows for ZavaShop:

- **Retail workflow** — Sequential with a conditional handoff to a backorder branch.
- **Supply-chain workflow** — Concurrent fan-out over five SKUs converging into a sequential PO chain.

## Deliverables

### Python (`target_language: python` or `both`) — inside `lab-04-multi-agent-workflow/`

- `requirements.txt`.
- `retail_workflow.py` — exports `build_retail_workflow() -> Workflow`.
- `supply_chain_workflow.py` — exports `build_supply_chain_workflow() -> Workflow`.
- `verify.py` — runs both workflows, asserts every criterion, exits 0 on full pass.

### C# / .NET (`target_language: csharp` or `both`) — inside `lab-04-multi-agent-workflow/csharp/`

- `Workflows/Workflows.csproj` — `Microsoft.NET.Sdk`, `net10.0`, `Nullable=enable`, refs (all `--prerelease`): `Microsoft.Agents.AI.Workflows`, `Microsoft.Agents.AI`, `Microsoft.Agents.AI.GitHub.Copilot`, `GitHub.Copilot.SDK`.
- `Workflows/RetailWorkflow.cs` — `public static Workflow BuildRetailWorkflow(AIAgent advisor, AIAgent inventory)`.
- `Workflows/SupplyChainWorkflow.cs` — `public static Workflow BuildSupplyChainWorkflow()`.
- `Workflows/RetailExecutors/` — `ProductAdvisorExecutor.cs`, `InventoryCheckerExecutor.cs`, `OrderProcessor.cs`, `ShipmentTrigger.cs`, `BackorderHandler.cs`.
- `Workflows/SupplyChainExecutors/` — `WeeklyTrigger.cs`, `DemandForecaster.cs`, `SupplierSelector.cs`, `PurchaseOrderAgent.cs`, `LogisticsCoordinator.cs`, `InventoryUpdater.cs`.
- `Verify/Verify.csproj` — refs `../Workflows/Workflows.csproj`.
- `Verify/Program.cs` — runs both workflows via `InProcessExecution.RunStreamingAsync` + `WatchStreamAsync()`, asserts every criterion, exits 0 on full pass with final line `[OK] Lab 4 complete.`.

## Required executor IDs (exact strings)

| Workflow | Python (`snake_case`) | C# (`PascalCase` passed to `Executor<TIn,TOut>(...)` base ctor) |
| --- | --- | --- |
| Retail | `product_advisor`, `inventory_checker`, `order_processor`, `shipment_trigger`, `backorder_handler` | `ProductAdvisor`, `InventoryChecker`, `OrderProcessor`, `ShipmentTrigger`, `BackorderHandler` |
| Supply chain | `weekly_trigger`, `demand_forecaster`, `supplier_selector`, `purchase_order_agent`, `logistics_coordinator`, `inventory_updater` | `WeeklyTrigger`, `DemandForecaster`, `SupplierSelector`, `PurchaseOrderAgent`, `LogisticsCoordinator`, `InventoryUpdater` |

## Deterministic recipes (use these — no LLM calls for forecasts/POs)

| Field | Python | C# |
| --- | --- | --- |
| `predicted_units_next_week` | `hash(sku) % 100 + 50` | `Math.Abs(sku.GetHashCode()) % 100 + 50` |
| `order_id` | `f"ORD-{9000 + counter:04d}"`, counter starts at 1 | `$"ORD-{Interlocked.Increment(ref s_counter)}"` with `static int s_counter = 9000` |
| `tracking_number` | `f"ZS-{secrets.token_hex(4).upper()}"` | `$"ZS-{Convert.ToHexString(RandomNumberGenerator.GetBytes(4))}"` |
| `po_id` | `f"PO-X{1234 + counter}"`, counter starts at 0 | `$"PO-X{Interlocked.Increment(ref s_poCounter) + 1233}"` with `static int s_poCounter = 0` |
| `eta_days` | `7 + hash(po_id) % 7` | `7 + Math.Abs(poId.GetHashCode()) % 7` |

## Acceptance criteria

### Retail workflow (both languages)

1. Accepts an input record with `customer_id`, `sku`, `quantity`, `preferred_warehouse` (Python: dict; C#: `record CustomerOrder(string CustomerId, string Sku, int Quantity, string PreferredWarehouse)`).
2. Happy path → final output has `order_id`, `state == "RESERVED"`, `tracking_number`, `warehouse` (Python dict; C#: `OrderRecord` with `State == "RESERVED"`).
3. Insufficient-stock path → conditional handoff to `backorder_handler` / `BackorderHandler` and final output has `state == "BACKORDERED"` plus `expected_restock_days > 0`.
4. `order_id` matches `^ORD-9\d{3}$`; `tracking_number` matches `^ZS-[0-9A-F]{8}$`.

### Supply-chain workflow (both languages)

5. Python: `ConcurrentBuilder` (or fan-out edges). C#: `WorkflowBuilder.AddFanOutEdge(trigger, forecaster, partitions: new[] { "LIP-001", "LIP-002", "SKN-030", "FRG-009", "TOL-003" })` + `AddFanInBarrierEdge(forecaster, supplier)`. Each SKU runs `demand_forecaster` / `DemandForecaster` exactly once.
6. `supplier_selector` / `SupplierSelector` uses a static table inside the file (no JSON load).
7. Final output: Python dict `{"updated": [...], "total_units": int}`; C# `record InventorySummary(IReadOnlyList<SkuUpdate> Updated, int TotalUnits)`. One entry per SKU and `TotalUnits > 0`.

### Both languages

8. Every workflow surfaces its result via `ctx.yield_output(...)` (Python) or `await context.YieldOutputAsync(...)` (C#) — never `print` / `Console.WriteLine` in business logic. The C# builder must end with `.WithOutputFrom(...)` so `StreamingRun` emits `OutputEvent<T>`.
9. Both workflows are importable / referenceable: Python `from retail_workflow import build_retail_workflow` from outside the folder; C# the `Workflows.csproj` is consumable by Lab 5 via `ProjectReference`.
10. `verify.py` / `Verify/Program.cs` asserts:
    - Retail happy: `{"sku": "LIP-001", "quantity": 2, "preferred_warehouse": "WH-SEA"}` → `state == "RESERVED"`.
    - Retail backorder: `{"sku": "LIP-001", "quantity": 5, "preferred_warehouse": "WH-DXB"}` → `state == "BACKORDERED"`.
    - Supply chain: 5 POs total, each input SKU represented exactly once.
    - Final line: `[OK] Lab 4 complete.`

## Verification commands

### Python

```bash
cd lab-04-multi-agent-workflow
uv pip install -r requirements.txt
python verify.py
```

### C# / .NET

```bash
cd lab-04-multi-agent-workflow/csharp
dotnet run --project Verify
```

## PR checklist (paste into the PR body)

- [ ] `target_language` directive present and obeyed.
- [ ] Executor IDs match the table above exactly (snake_case for Python, PascalCase for C#).
- [ ] Deterministic recipes used (no LLM in forecasts / PO generation).
- [ ] Both factories importable / referenceable from outside the lab folder.
- [ ] C# builder ends with `.WithOutputFrom(...)` so `WatchStreamAsync()` emits `OutputEvent<T>`.
- [ ] C# uses `AddFanOutEdge` + `AddFanInBarrierEdge` (not `AddEdge`) for the supply-chain fan-out.
- [ ] Each acceptance criterion mapped to a line in `verify.py` and/or `Verify/Program.cs`.
- [ ] No edits outside `lab-04-multi-agent-workflow/`.
