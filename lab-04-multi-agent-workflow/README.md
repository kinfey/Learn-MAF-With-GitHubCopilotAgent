# Lab 4 — Multi-Agent Workflows: Retail & Supply Chain

> Estimated time: 90 minutes. **Driven by Copilot Coding Agent.**
>
> **Learning goal**: practice MAF's **Workflows** — executors, edges, and the Sequential / Concurrent / Handoff orchestration patterns — by modeling ZavaShop's retail and supply-chain processes. Lab 2 / 3 agents plug in as nodes via the GitHub Copilot SDK; the Coding Agent assembles the graph while you review the topology. Pick your language with `target_language` in [`PROMPT.md`](PROMPT.md): Python uses `@executor` + `WorkflowBuilder`; C# uses `Executor<TIn,TOut>` + `WorkflowBuilder` + `StreamingRun` from `Microsoft.Agents.AI.Workflows`.

## ZavaShop Story

Two ZavaShop teams need orchestration:

- **Retail Ops** — When a customer places an order, four things must happen in order: identify the product, verify stock, create the order record, and trigger a shipment. Each step has its own specialist agent.
- **Supply Chain** — Every Monday morning, the supply-chain team needs a forecast → purchase-order → logistics flow that runs across five SKUs in parallel, then converges to update inventory.

You will model both as **Microsoft Agent Framework Workflows**: a graph of executors (or agents) with explicit edges and orchestration patterns.

## Microsoft Agent Framework concepts in this lab

This lab is where the workshop crosses from **agents** (LLM-driven, dynamic) into **workflows** (graph-based, explicit).

| Concept | What it means in code | Microsoft Learn |
| --- | --- | --- |
| **Workflow vs Agent** | A workflow is a *graph* of executors with explicit edges — you control the order, not the LLM. Agents from Labs 2–3 can plug in as nodes. | [Workflows overview](https://learn.microsoft.com/en-us/agent-framework/workflows/) |
| **Executors** | The processing units of the graph. Python: `@executor`-decorated function or an `Agent` acting as one. C#: a `class : Executor<TIn, TOut>("PascalCase")` subclass overriding `HandleAsync(input, IWorkflowContext ctx)` and calling `await ctx.YieldOutputAsync(...)`. | [Executors](https://learn.microsoft.com/en-us/agent-framework/workflows/executors) |
| **Edges & conditional routing** | Edges connect executors; conditions on edges branch the graph. Python: `.add_edge(a, b, condition=...)`. C#: `.AddEdge(a, b, condition: ctx => ...)`. | [Edges](https://learn.microsoft.com/en-us/agent-framework/workflows/edges) |
| **`WorkflowBuilder` & supersteps** | Python: `WorkflowBuilder(start_executor=...).add_edge(...).build()`. C#: `new WorkflowBuilder(start).AddEdge(...).WithOutputFrom(...).Build()`. Execution proceeds in **supersteps** (parallel-safe slices) with type-validated routing. | [Workflow Builder & Execution](https://learn.microsoft.com/en-us/agent-framework/workflows/workflows) |
| **Sequential / Concurrent / Handoff** | Three built-in patterns. Python: `SequentialBuilder` / `ConcurrentBuilder` / handoff via conditional edges. C#: `WorkflowBuilder.AddEdge` (sequential), `AddFanOutEdge` + `AddFanInBarrierEdge` (concurrent), conditional `AddEdge` (handoff). All three appear here. | [Workflows overview](https://learn.microsoft.com/en-us/agent-framework/workflows/) |
| **Agent-as-Executor** | Wrap a Lab 2 / 3 agent as a workflow node. Python: `agent` plugs in directly. C#: subclass `Executor<TIn, TOut>` that calls `await agent.RunAsync(input, session)` inside `HandleAsync`. | [Workflows overview](https://learn.microsoft.com/en-us/agent-framework/workflows/) |
| **Streaming the run** | Python: iterate `WorkflowRunResult`. C#: `await using StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, input)` + `await foreach (var evt in run.WatchStreamAsync())`. | [Workflow Builder & Execution](https://learn.microsoft.com/en-us/agent-framework/workflows/workflows) |

## Run This Lab

1. Open an issue (or `@copilot` comment) in your fork with the contents of [`PROMPT.md`](PROMPT.md). The first line assigns the custom agent; `target_language` selects `python`, `csharp`, or `both`.
2. The Coding Agent will:
   - Load the [`zava-workflow-architect`](../.github/agents/zava-workflow-architect.md) profile (contains canonical patterns for both languages; reads only the matching one).
   - Read the matching workflows skill (`agent-framework-workflows-py` or `agent-framework-workflows-csharp`) end-to-end plus a small slice of the matching Copilot SDK skill.
   - Scaffold the language-appropriate files (Python `.py` at the lab root, C# projects under `csharp/`).
   - Open a PR. You review, run the language-matching verify, merge.

| Layer | Where the role / API / task lives |
| --- | --- |
| Role (HOW) | [`.github/agents/zava-workflow-architect.md`](../.github/agents/zava-workflow-architect.md) (Python + C# canonical patterns) |
| API reference (Python) | [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md), [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) |
| API reference (C#) | [`agent-framework-workflows-csharp`](../.github/skills/agent-framework-workflows-csharp/SKILL.md), [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) |
| Task (WHAT + which language) | [`PROMPT.md`](PROMPT.md) |

## What You Will Learn

- Building Workflows with `WorkflowBuilder` and `@executor` decorators.
- The Sequential, Concurrent, and Handoff orchestration builders.
- Passing typed state through `WorkflowContext`.
- Mixing **agents-as-executors** (Lab 2 / 3 reused) with plain function executors.
- Emitting outputs with `ctx.yield_output(...)` and reading them from `WorkflowRunResult`.

## Custom Agent + Skills (set by [`PROMPT.md`](PROMPT.md))

- **Custom agent**: [`zava-workflow-architect`](../.github/agents/zava-workflow-architect.md) — the role profile encodes executor / builder / handoff patterns.
- **Skills the agent will read**:
  - [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md) — every section.
  - [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) — only the **Agent-as-Executor** subsection.
  - [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) — role names, order lifecycle, data file schemas.

## Architecture

### Retail Workflow (Sequential + Handoff on failure)

```
CustomerOrder ──► ProductAdvisor ──► InventoryChecker ──► OrderProcessor ──► ShipmentTrigger ──► Output(receipt)
                                          │
                                          ▼ (on OUT_OF_STOCK)
                                   BackorderHandler ──► Output(backorder_notice)
```

- Each named role is an **executor**. `ProductAdvisor` and `InventoryChecker` may be `GitHubCopilotAgent`-based; `OrderProcessor`, `ShipmentTrigger`, `BackorderHandler` are plain `@executor` functions that mutate a dict.
- Use a **conditional handoff** when stock is insufficient.

### Supply-Chain Workflow (Concurrent fan-out, then converge)

```
                ┌── DemandForecaster(LIP-001) ──┐
                ├── DemandForecaster(LIP-002) ──┤
WeeklyTrigger ──┼── DemandForecaster(SKN-030) ──┼──► SupplierSelector ──► PurchaseOrderAgent ──► LogisticsCoordinator ──► InventoryUpdater ──► Output
                ├── DemandForecaster(FRG-009) ──┤
                └── DemandForecaster(TOL-003) ──┘
                          (fan-out, ConcurrentBuilder)
```

- The five `DemandForecaster` invocations run **concurrently**.
- Results are aggregated, then handed sequentially to the downstream chain.

## Deliverable

### Python (`target_language: python`)

```
lab-04-multi-agent-workflow/
├── README.md
├── PROMPT.md
├── requirements.txt
├── retail_workflow.py
├── supply_chain_workflow.py
└── verify.py
```

### C# / .NET (`target_language: csharp`)

```
lab-04-multi-agent-workflow/
└── csharp/
    ├── Workflows/
    │   ├── Workflows.csproj          # Microsoft.NET.Sdk, refs Microsoft.Agents.AI.Workflows, Microsoft.Agents.AI.GitHub.Copilot
    │   ├── RetailWorkflow.cs         # BuildRetailWorkflow() returns Workflow<TIn>
    │   ├── SupplyChainWorkflow.cs    # BuildSupplyChainWorkflow() returns Workflow<TIn>
    │   ├── RetailExecutors/          # ProductAdvisorExecutor.cs, InventoryCheckerExecutor.cs, OrderProcessor.cs, ShipmentTrigger.cs, BackorderHandler.cs
    │   └── SupplyChainExecutors/     # DemandForecaster.cs, SupplierSelector.cs, PurchaseOrderAgent.cs, LogisticsCoordinator.cs, InventoryUpdater.cs
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                # InProcessExecution.RunStreamingAsync + run.WatchStreamAsync() + asserts
```

## .NET / C# Implementation

Follow the canonical patterns in [`zava-workflow-architect`](../.github/agents/zava-workflow-architect.md). Key shapes:

**Executors** (PascalCase IDs; the constructor passes the ID to the base):

```csharp
public sealed class OrderProcessor() : Executor<StockedOrder, OrderRecord>("OrderProcessor")
{
    private static int s_counter = 9000;

    public override async ValueTask HandleAsync(StockedOrder input, IWorkflowContext context)
    {
        OrderRecord record = new(
            OrderId: $"ORD-{Interlocked.Increment(ref s_counter)}",
            Sku: input.Sku,
            Quantity: input.Quantity,
            Warehouse: input.Warehouse,
            State: "RESERVED");
        await context.YieldOutputAsync(record);
    }
}
```

**Retail workflow** (sequential + conditional handoff on `OUT_OF_STOCK`):

```csharp
var advisor    = new ProductAdvisorExecutor(copilotAgent);   // agent-as-executor
var inventory  = new InventoryCheckerExecutor(copilotAgent);
var processor  = new OrderProcessor();
var shipment   = new ShipmentTrigger();
var backorder  = new BackorderHandler();

Workflow workflow = new WorkflowBuilder(advisor)
    .AddEdge(advisor, inventory)
    .AddEdge(inventory, processor,  condition: r => r.InStock)
    .AddEdge(inventory, backorder,  condition: r => !r.InStock)
    .AddEdge(processor, shipment)
    .WithOutputFrom(shipment, backorder)
    .Build();
```

**Supply-chain workflow** (fan-out across 5 SKUs, fan-in barrier, then sequential tail):

```csharp
var trigger    = new WeeklyTrigger();
var forecaster = new DemandForecaster();
var supplier   = new SupplierSelector();
var po         = new PurchaseOrderAgent();
var logistics  = new LogisticsCoordinator();
var updater    = new InventoryUpdater();

Workflow workflow = new WorkflowBuilder(trigger)
    .AddFanOutEdge(trigger, forecaster, partitions: new[] { "LIP-001", "LIP-002", "SKN-030", "FRG-009", "TOL-003" })
    .AddFanInBarrierEdge(forecaster, supplier)
    .AddEdge(supplier, po)
    .AddEdge(po, logistics)
    .AddEdge(logistics, updater)
    .WithOutputFrom(updater)
    .Build();
```

**Running and asserting** (`Verify/Program.cs`):

```csharp
await using StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, customerOrder);
await foreach (WorkflowEvent evt in run.WatchStreamAsync())
{
    if (evt is OutputEvent<OrderRecord> output)
    {
        Assert.Equal("RESERVED", output.Value.State);
        return 0;
    }
}
```

## Acceptance Criteria

### Retail Workflow

1. `retail_workflow.py` exposes `build_retail_workflow() -> Workflow`.
2. Executors are named exactly: `product_advisor`, `inventory_checker`, `order_processor`, `shipment_trigger`, `backorder_handler` (lowercase IDs with underscores; role names in comments match `zavashop-context`).
3. The workflow accepts an input dict:
   ```python
   {"customer_id": "CUST-501", "sku": "LIP-001", "quantity": 2, "preferred_warehouse": "WH-SEA"}
   ```
4. Happy path produces a final output dict with keys: `order_id`, `state` (`"RESERVED"`), `tracking_number`, `warehouse`.
5. When stock is insufficient, the handoff path runs `backorder_handler` and the final output has `state == "BACKORDERED"` and `expected_restock_days` (any int > 0 is acceptable).
6. `OrderProcessor` produces order IDs of the form `ORD-9XXX` (in-process counter starting at `ORD-9001`).
7. `ShipmentTrigger` produces tracking numbers of the form `ZS-<8 hex chars>`.

### Supply-Chain Workflow

1. `supply_chain_workflow.py` exposes `build_supply_chain_workflow() -> Workflow`.
2. Uses `ConcurrentBuilder` (or equivalent fan-out edges) to run `demand_forecaster` for **each** of `["LIP-001", "LIP-002", "SKN-030", "FRG-009", "TOL-003"]` in parallel.
3. `demand_forecaster(sku)` returns `{"sku": sku, "predicted_units_next_week": int}` — deterministic for testing (use `hash(sku) % 100 + 50`, no LLM call needed).
4. `supplier_selector` chooses one supplier per SKU (use a static lookup table inside the file; no need to load JSON for this).
5. `purchase_order_agent` emits structured POs of the form `{"po_id": "PO-X1234", "sku": ..., "units": ..., "supplier": ...}` — `po_id` increments deterministically.
6. `logistics_coordinator` returns `{"po_id": ..., "eta_days": int}` (use `7 + hash(po_id) % 7`).
7. `inventory_updater` returns a final aggregated dict `{"updated": [{"sku": ..., "added_units": ...}, ...], "total_units": int}`.

### Both Workflows

8. Each workflow uses `ctx.yield_output(...)` to surface its final result; no `print` in business logic.
9. Each workflow is built once at module level via the `build_*_workflow()` factory.
10. `verify.py` runs both workflows and asserts:
    - Retail happy path: input `{"sku": "LIP-001", "quantity": 2, "preferred_warehouse": "WH-SEA"}` → `state == "RESERVED"`.
    - Retail backorder path: input `{"sku": "LIP-001", "quantity": 5, "preferred_warehouse": "WH-DXB"}` → `state == "BACKORDERED"` (Dubai has 0 LIP-001).
    - Supply chain: produces 5 POs total, each SKU represented exactly once, `total_units > 0`.

## Run It

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

## Common Mistakes

| Symptom | Cause |
| --- | --- |
| Retail handoff never fires | Conditional edge predicate is checked against the wrong context field |
| Supply chain runs serially | Python: used `SequentialBuilder` instead of `ConcurrentBuilder`. C#: used `AddEdge` instead of `AddFanOutEdge` / `AddFanInBarrierEdge` |
| Final output missing | Python: forgot `ctx.yield_output(...)`. C#: forgot `await context.YieldOutputAsync(...)` and/or `.WithOutputFrom(...)` |
| Order IDs repeat across runs | Counter declared inside the executor function/method — promote to module scope (Python) or `static int s_counter` with `Interlocked.Increment` (C#) |
| Lab 3's MCP server is required | It is not — Lab 4 reads stock directly from `data/zava_warehouses.json`. Reusing Lab 3's MCP is allowed but optional |
| C#: executor never runs | Executor ID collision — every `Executor<TIn,TOut>("...")` constructor argument must be unique in the graph |
| C#: `WatchStreamAsync()` never emits an `OutputEvent` | Forgot `.WithOutputFrom(terminal)` on the builder |

Done? → [Lab 5 — AGUI](../lab-05-agui/README.md)
