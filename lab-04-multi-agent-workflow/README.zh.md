# Lab 4 — 多 Agent 工作流：零售 & 供应链

> 预计用时：90 分钟。**由 Copilot Coding Agent 驱动。**>
> **学习目标**：通过建模 ZavaShop 的零售与供应链流程，践行 MAF 的 **Workflows** — executors、edges，以及 Sequential / Concurrent / Handoff 编排模式。Lab 2 / 3 的 Agent 通过 GitHub Copilot SDK 作为节点接入；Coding Agent 拼装图结构，你负责评审拓扑。用 [`PROMPT.md`](PROMPT.md) 里的 `target_language` 选语言：Python 走 `@executor` + `WorkflowBuilder`；C# 走 `Microsoft.Agents.AI.Workflows` 的 `Executor<TIn,TOut>` + `WorkflowBuilder` + `StreamingRun`。
## ZavaShop 故事

ZavaShop 有两支团队需要工作流编排：

- **零售运营（Retail Ops）** — 顾客下单后，必须按顺序做四件事：识别商品、核实库存、生成订单记录、触发发货。每一步都有自己的专长 Agent。
- **供应链（Supply Chain）** — 每周一早上，供应链团队需要一个 预测 → 采购单 → 物流 的流程，对 5 个 SKU 并行运行，再汇总更新库存。

你将用 **Microsoft Agent Framework Workflow** 建模两者：一张由 executor（或 Agent）与显式边构成的图，配上明确的编排模式。

## 本实验涉及的 Microsoft Agent Framework 概念

本实验是本工作坊从 **agents**（LLM 驱动、动态）跨入 **workflows**（图驱动、显式）的交汇点。

| 概念 | 在代码中的体现 | Microsoft Learn |
| --- | --- | --- |
| **Workflow vs Agent** | Workflow 是带显式边的 executor *图*——由你控制执行顺序，不是 LLM。Lab 2–3 的 Agent 可以作为节点接入。 | [Workflows overview](https://learn.microsoft.com/zh-cn/agent-framework/workflows/) |
| **执行器（Executors）** | 图的处理单元。Python：`@executor` 装饰的函数或充当 executor 的 `Agent`。C#：`class : Executor<TIn,TOut>("PascalCase")` 子类，覆盖 `HandleAsync(input, IWorkflowContext ctx)` 并调 `await ctx.YieldOutputAsync(...)`。 | [Executors](https://learn.microsoft.com/zh-cn/agent-framework/workflows/executors) |
| **边与条件路由** | 边连接执行器；边上的条件实现分支。Python：`.add_edge(a, b, condition=...)`。C#：`.AddEdge(a, b, condition: ctx => ...)`。 | [Edges](https://learn.microsoft.com/zh-cn/agent-framework/workflows/edges) |
| **`WorkflowBuilder` 与 superstep** | Python：`WorkflowBuilder(start_executor=...).add_edge(...).build()`。C#：`new WorkflowBuilder(start).AddEdge(...).WithOutputFrom(...).Build()`。运行时以 **superstep**（并行安全切片）推进，带类型验证的消息路由。 | [Workflow Builder & Execution](https://learn.microsoft.com/zh-cn/agent-framework/workflows/workflows) |
| **Sequential / Concurrent / Handoff** | 三种内置模式。Python：`SequentialBuilder` / `ConcurrentBuilder` / 条件边 handoff。C#：`WorkflowBuilder.AddEdge`（顺序）、`AddFanOutEdge` + `AddFanInBarrierEdge`（并发）、条件 `AddEdge`（handoff）。本实验三者都用到。 | [Workflows overview](https://learn.microsoft.com/zh-cn/agent-framework/workflows/) |
| **Agent-as-Executor** | 把 Lab 2 / 3 的 Agent 包装为工作流节点。Python：`agent` 直接接入。C#：子类 `Executor<TIn,TOut>` 在 `HandleAsync` 里调 `await agent.RunAsync(input, session)`。 | [Workflows overview](https://learn.microsoft.com/zh-cn/agent-framework/workflows/) |
| **流式运行** | Python：遍历 `WorkflowRunResult`。C#：`await using StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, input)` + `await foreach (var evt in run.WatchStreamAsync())`。 | [Workflow Builder & Execution](https://learn.microsoft.com/zh-cn/agent-framework/workflows/workflows) |

## 运行本实验

1. 在你的 fork 里新开一个 Issue（或 `@copilot` 评论），粘贴 [`PROMPT.md`](PROMPT.md) 的全部内容。首行指派 custom agent；`target_language` 那行选 `python` / `csharp` / `both`。
2. Coding Agent 会：
   - 加载 [`zava-workflow-architect`](../.github/agents/zava-workflow-architect.md) profile（同时包含 Python 和 C# 两套范本）。
   - 完整读与 `target_language` 匹配的 workflow skill，加一小块 Copilot SDK skill。
   - 生成语言对应的文件（Python `.py` 放 lab 根目录，C# 项目放 `csharp/`）。
   - 开 PR。你 review，本地跑语言对应的 verify，合并。

| 层 | 角色 / API / 任务住哪里 |
| --- | --- |
| 角色（HOW） | [`.github/agents/zava-workflow-architect.md`](../.github/agents/zava-workflow-architect.md)（Python + C# 范本代码） |
| API 参考（Python） | [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md)、[`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) |
| API 参考（C#） | [`agent-framework-workflows-csharp`](../.github/skills/agent-framework-workflows-csharp/SKILL.md)、[`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) |
| 任务（WHAT + 哪一栈） | [`PROMPT.md`](PROMPT.md) |

## 你会学到什么

- 用 `WorkflowBuilder` 和 `@executor` 装饰器构建 Workflow。
- Sequential、Concurrent、Handoff 三种编排 builder。
- 通过 `WorkflowContext` 传递带类型的状态。
- 把 **Agent-as-executor**（复用 Lab 2 / 3）和普通函数 executor 混着用。
- 用 `ctx.yield_output(...)` 输出结果，再从 `WorkflowRunResult` 取回来。

## Custom Agent + Skills（由 [`PROMPT.md`](PROMPT.md) 指定）

- **Custom agent**：[`zava-workflow-architect`](../.github/agents/zava-workflow-architect.md) — 角色 profile 包含 executor / builder / handoff 的范本代码。
- **Agent 会读的 skill**：
  - [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md) — 每一节都要看。
  - [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) — 只看 **Agent-as-Executor** 一节。
  - [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) — 角色名、订单生命周期、样本数据位置。

## 架构

### 零售工作流（顺序 + 失败时 Handoff）

```
CustomerOrder ──► ProductAdvisor ──► InventoryChecker ──► OrderProcessor ──► ShipmentTrigger ──► Output(receipt)
                                          │
                                          ▼ （遇到 OUT_OF_STOCK）
                                   BackorderHandler ──► Output(backorder_notice)
```

- 每个命名角色都是一个 **executor**。`ProductAdvisor` 和 `InventoryChecker` 可以基于 `GitHubCopilotAgent`；`OrderProcessor`、`ShipmentTrigger`、`BackorderHandler` 是改 dict 的普通 `@executor` 函数。
- 库存不足时走 **条件 handoff**。

### 供应链工作流（并行扇出，再汇聚）

```
                ┌── DemandForecaster(LIP-001) ──┐
                ├── DemandForecaster(LIP-002) ──┤
WeeklyTrigger ──┼── DemandForecaster(SKN-030) ──┼──► SupplierSelector ──► PurchaseOrderAgent ──► LogisticsCoordinator ──► InventoryUpdater ──► Output
                ├── DemandForecaster(FRG-009) ──┤
                └── DemandForecaster(TOL-003) ──┘
                          （扇出，ConcurrentBuilder）
```

- 五个 `DemandForecaster` 调用 **并发** 执行。
- 结果聚合后按顺序交给下游链路。

## 交付物

### Python（`target_language: python`）

```
lab-04-multi-agent-workflow/
├── README.md
├── PROMPT.md
├── requirements.txt
├── retail_workflow.py
├── supply_chain_workflow.py
└── verify.py
```

### C# / .NET（`target_language: csharp`）

```
lab-04-multi-agent-workflow/
└── csharp/
    ├── Workflows/
    │   ├── Workflows.csproj          # Microsoft.NET.Sdk，引 Microsoft.Agents.AI.Workflows、Microsoft.Agents.AI.GitHub.Copilot
    │   ├── RetailWorkflow.cs         # BuildRetailWorkflow() 返回 Workflow<TIn>
    │   ├── SupplyChainWorkflow.cs    # BuildSupplyChainWorkflow() 返回 Workflow<TIn>
    │   ├── RetailExecutors/          # ProductAdvisorExecutor.cs、InventoryCheckerExecutor.cs、OrderProcessor.cs、ShipmentTrigger.cs、BackorderHandler.cs
    │   └── SupplyChainExecutors/     # DemandForecaster.cs、SupplierSelector.cs、PurchaseOrderAgent.cs、LogisticsCoordinator.cs、InventoryUpdater.cs
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                # InProcessExecution.RunStreamingAsync + run.WatchStreamAsync() + 断言
```

## .NET / C# 实现

遵循 [`zava-workflow-architect`](../.github/agents/zava-workflow-architect.md) 中的范本。关键形状：

**执行器**（PascalCase ID，构造函数把 ID 传给基类）：

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

**零售工作流**（顺序 + `OUT_OF_STOCK` 条件 handoff）：

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

**供应链工作流**（对 5 个 SKU 扇出、扇入 barrier、再顺序尾巴）：

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

**运行与断言**（`Verify/Program.cs`）：

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

## 验收标准

### 零售工作流

1. `retail_workflow.py` 暴露 `build_retail_workflow() -> Workflow`。
2. Executor 名字（id）必须是：`product_advisor`、`inventory_checker`、`order_processor`、`shipment_trigger`、`backorder_handler`（小写下划线；注释里写出对应 `zavashop-context` 中的角色名）。
3. 工作流接受输入字典：
   ```python
   {"customer_id": "CUST-501", "sku": "LIP-001", "quantity": 2, "preferred_warehouse": "WH-SEA"}
   ```
4. 正常路径产出 dict，包含键：`order_id`、`state`（`"RESERVED"`）、`tracking_number`、`warehouse`。
5. 库存不足时走 handoff 跑 `backorder_handler`，最终输出 `state == "BACKORDERED"` 且 `expected_restock_days` 为任意正整数。
6. `OrderProcessor` 产生形如 `ORD-9XXX` 的订单号（进程内计数器从 `ORD-9001` 起）。
7. `ShipmentTrigger` 产生形如 `ZS-<8 位十六进制>` 的运单号。

### 供应链工作流

1. `supply_chain_workflow.py` 暴露 `build_supply_chain_workflow() -> Workflow`。
2. 用 `ConcurrentBuilder`（或等价扇出边）对 `["LIP-001", "LIP-002", "SKN-030", "FRG-009", "TOL-003"]` 中 **每个** SKU 并行运行 `demand_forecaster`。
3. `demand_forecaster(sku)` 返回 `{"sku": sku, "predicted_units_next_week": int}` — 为了测试稳定，直接用 `hash(sku) % 100 + 50`，不需要 LLM 调用。
4. `supplier_selector` 给每个 SKU 选一个供应商（文件内静态查表即可，不用读 JSON）。
5. `purchase_order_agent` 发出形如 `{"po_id": "PO-X1234", "sku": ..., "units": ..., "supplier": ...}` 的 PO，`po_id` 确定性递增。
6. `logistics_coordinator` 返回 `{"po_id": ..., "eta_days": int}`（用 `7 + hash(po_id) % 7`）。
7. `inventory_updater` 返回最终聚合结果 `{"updated": [{"sku": ..., "added_units": ...}, ...], "total_units": int}`。

### 两条工作流共同要求

8. 每个工作流必须通过 `ctx.yield_output(...)` 输出最终结果；业务逻辑里不允许 `print`。
9. 每个工作流通过 `build_*_workflow()` 工厂在模块层构造一次。
10. `verify.py` 跑两条工作流并断言：
    - 零售正常路径：输入 `{"sku": "LIP-001", "quantity": 2, "preferred_warehouse": "WH-SEA"}` → `state == "RESERVED"`。
    - 零售缺货路径：输入 `{"sku": "LIP-001", "quantity": 5, "preferred_warehouse": "WH-DXB"}` → `state == "BACKORDERED"`（迪拜 LIP-001 库存为 0）。
    - 供应链：总共产出 5 张 PO，每个 SKU 恰好出现一次，`total_units > 0`。

## 运行

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

## 常见错误

| 现象 | 原因 |
| --- | --- |
| 零售 handoff 不触发 | 条件边判断的字段不对 |
| 供应链变成串行 | Python：用了 `SequentialBuilder`；C#：用了 `AddEdge` 而不是 `AddFanOutEdge` / `AddFanInBarrierEdge` |
| 最终结果缺失 | Python：忘了 `ctx.yield_output(...)`。C#：忘了 `await context.YieldOutputAsync(...)` 或 builder 上的 `.WithOutputFrom(...)` |
| 订单号跨 run 重复 | 计数器定义在 executor 函数/方法内 — 提到模块层（Python）或用 `static int s_counter` + `Interlocked.Increment`（C#） |
| 以为 Lab 3 MCP 必跑 | 不是的 — Lab 4 直接读 `data/zava_warehouses.json`。复用 Lab 3 MCP 可选 |
| C#：某个 executor 不触发 | Executor ID 冲突 — 图中每个 `Executor<TIn,TOut>("...")` 传的名必须唯一 |
| C#：`WatchStreamAsync()` 从不出 `OutputEvent` | builder 上忘了 `.WithOutputFrom(terminal)` |

完成了？→ [Lab 5 — AGUI](../lab-05-agui/README.zh.md)
