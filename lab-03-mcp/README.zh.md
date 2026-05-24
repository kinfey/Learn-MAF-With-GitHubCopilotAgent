# Lab 3 — MCP：ZavaShop 库存服务

> 预计用时：60 分钟。**由 Copilot Coding Agent 驱动。**
>
> **学习目标**：通过把一个自制库存 MCP 服务器接入 Copilot 后端 Agent，践行 MAF 的 **Local MCP 工具 + 工具审批（HITL）**。Coding Agent 同时生成 MCP 服务器（Python `FastMCP` 或 .NET `ModelContextProtocol`）与 Agent 代码；权限策略由你决定。用 [`PROMPT.md`](PROMPT.md) 里的 `target_language` 选语言。

## ZavaShop 故事

Lab 2 的 Product Advisor 能介绍产品，但说不出 *现在还有没有货*。库存活在另一套系统里：ZavaShop 的五个仓库各自通过实时 API 暴露库存。

你将把那套 API 实现成一个 **Model Context Protocol（MCP）服务器** — 一个 Python `mcp` 服务，把库存和预留操作暴露为 MCP 工具 — 然后把它接进一个 `GitHubCopilotAgent`，让 LLM 直接调用库存操作。

## 本实验涉及的 Microsoft Agent Framework 概念

| 概念 | 在代码中的体现 | Microsoft Learn |
| --- | --- | --- |
| **Local MCP Tools** | 由你自己运行的 MCP 服务器。Python 走 FastMCP + Streamable HTTP；.NET 走 `Microsoft.NET.Sdk.Web` + `AddMcpServer().WithHttpTransport()`。Agent 使用 Python `default_options["mcp_servers"]` 或 .NET 编程式 `McpClient` + `await mcpClient.ListToolsAsync()`。 | [Tools Overview](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/)（Local MCP Tools） |
| **工具审批（Human-in-the-loop）** | 调用某些类型工具前会抛出权限请求。Python：由 `on_permission_request` 决定通过或拒绝，本实验只放行 `kind == "mcp"`。.NET：工具来自可信的本地 `McpClient`，审批隐式 — 如需显式 HITL，限制调用者能创建哪个 `McpClient`。 | [Tools Overview](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/)（Tool Approval） |
| **函数工具与 MCP 工具共存** | 同一个 Copilot 后端 Agent 保留 Lab 2 的函数工具，**同时** 增加 MCP 工具。.NET 中把 `AIFunctionFactory.Create(...)` 与 `mcpTools.Cast<AITool>()` 一同传给 `tools:` 参数。 | [Tools Overview](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/) |

## 运行本实验

1. 在你的 fork 里新开一个 Issue（或 `@copilot` 评论），粘贴 [`PROMPT.md`](PROMPT.md) 的全部内容。首行指派 custom agent；`target_language` 那行选 `python` / `csharp` / `both`。
2. Coding Agent 会：
   - 加载 [`zava-mcp-integrator`](../.github/agents/zava-mcp-integrator.md) profile（同时包含 Python 和 C# 两个节，只读匹配那一段）。
   - 只读 profile 指向的、与 `target_language` 匹配的 GitHub Copilot SDK + ZavaShop skill。
   - 生成服务与 Agent（Python 文件放 lab 根目录，C# 项目放 `csharp/`）以及 verify 脚本。
   - 开 PR。你 review，本地跑语言对应的 verify，合并。

| 层 | 角色 / API / 任务住哪里 |
| --- | --- |
| 角色（HOW） | [`.github/agents/zava-mcp-integrator.md`](../.github/agents/zava-mcp-integrator.md)（同时包含 Python 和 C# 两个节） |
| API 参考（Python） | [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) · 官方 `mcp` Python SDK |
| API 参考（C#） | [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) · `ModelContextProtocol` + `ModelContextProtocol.AspNetCore` |
| 任务（WHAT + 哪一栈） | [`PROMPT.md`](PROMPT.md) |

## 你会学到什么

- 用官方 `mcp` Python SDK 构建 Streamable HTTP MCP 服务器。
- 设计安全读写 JSON 状态的 MCP 工具。
- 通过 `default_options["mcp_servers"]` 把 MCP 服务器接入 `GitHubCopilotAgent`。
- 用 `on_permission_request` 处理 `mcp` 这类权限请求。

## Custom Agent + Skills（由 [`PROMPT.md`](PROMPT.md) 指定）

- **Custom agent**：[`zava-mcp-integrator`](../.github/agents/zava-mcp-integrator.md) — 角色 profile 包含 FastMCP + agent 接入的完整范本。
- **Agent 会读的 skill**：
  - [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) — 重点看 **MCP Servers (Local + Remote)** 和 **Lifecycle & Permissions** 两节。
  - [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) — 仓库代码、库存字典结构、错误字符串约定。

## 架构

```
┌────────────────────────┐         ┌──────────────────────────────────────┐
│ inventory_agent.py     │ MCP /   │ inventory_mcp_server.py              │
│ GitHubCopilotAgent     │ HTTP    │ FastMCP("zava-inventory")            │
│ + mcp_servers={        │ ─────►  │   @mcp.tool list_warehouses()        │
│   "zava-inventory":    │ ◄────── │   @mcp.tool check_stock(sku, wh)     │
│   {type:"http", url:…} │  SSE    │   @mcp.tool reserve_units(sku,wh,qty)│
│ }                      │         │   @mcp.tool restock(sku, wh, qty)    │
└────────────────────────┘         └──────────────────────────────────────┘
                                              │
                                              ▼
                                     data/zava_warehouses.json
                                     （加载到内存；变更不回写磁盘）
```

## 交付物

根据 `target_language`，Coding Agent 产出一棵或两棵：

### Python（`target_language: python`）

```
lab-03-mcp/
├── README.md
├── PROMPT.md
├── requirements.txt
├── inventory_mcp_server.py    ← MCP 服务器（Streamable HTTP，端口 5300）
├── inventory_agent.py         ← 消费 MCP 服务的 Agent
└── verify.py                  ← 启动服务、跑脚本化查询、断言、清理
```

### C# / .NET（`target_language: csharp`）

```
lab-03-mcp/
└── csharp/
    ├── InventoryServer/
    │   ├── InventoryServer.csproj   # Microsoft.NET.Sdk.Web，引 ModelContextProtocol + ModelContextProtocol.AspNetCore
    │   ├── Program.cs                # builder.Services.AddMcpServer().WithHttpTransport().WithTools<InventoryTools>(); app.MapMcp("/mcp")
    │   ├── InventoryTools.cs         # [McpServerToolType] 静态类 + [McpServerTool] 方法
    │   └── InventoryState.cs         # 启动时一次加载 data/zava_warehouses.json 进内存
    ├── InventoryAgent/
    │   ├── InventoryAgent.csproj    # Microsoft.NET.Sdk，引 GitHub.Copilot.SDK、Microsoft.Agents.AI.GitHub.Copilot、ModelContextProtocol
    │   └── Program.cs                # 启动服务进程（Process.Start）+ McpClient.CreateAsync + agent
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                # 启动服务子进程、跑三轮、substring 断言、清理
```

## .NET / C# 实现

Coding Agent 遵循 [`zava-mcp-integrator`](../.github/agents/zava-mcp-integrator.md) 中的范本。verify 与审核者应看到的关键片段：

**`InventoryServer/Program.cs`** — 在 `:5300/mcp` 上托管 MCP over HTTP：

```csharp
var builder = WebApplication.CreateBuilder(args);
builder.Services
    .AddSingleton<InventoryState>()                 // JSON 只加载一次
    .AddMcpServer()
    .WithHttpTransport()
    .WithTools<InventoryTools>();

var app = builder.Build();
app.MapMcp("/mcp");
app.Run("http://127.0.0.1:5300");
```

**`InventoryServer/InventoryTools.cs`** — 四个工具，签名与 Python 对齐：

```csharp
[McpServerToolType]
public static class InventoryTools
{
    [McpServerTool, Description("List ZavaShop warehouses.")]
    public static IReadOnlyList<Warehouse> ListWarehouses(InventoryState state) => state.Warehouses;

    [McpServerTool, Description("Check stock for a SKU; warehouseCode null returns all warehouses.")]
    public static object CheckStock(InventoryState state, string sku, string? warehouseCode = null)
        => state.CheckStock(sku, warehouseCode);

    [McpServerTool, Description("Reserve units; returns OUT_OF_STOCK: <sku>@<wh> when insufficient.")]
    public static object ReserveUnits(InventoryState state, string sku, string warehouseCode, int quantity)
        => state.Reserve(sku, warehouseCode, quantity);

    [McpServerTool, Description("Restock units; NOT_FOUND: <sku> for unknown SKUs.")]
    public static object Restock(InventoryState state, string sku, string warehouseCode, int quantity)
        => state.Restock(sku, warehouseCode, quantity);
}
```

**`InventoryAgent/Program.cs`** — 编程式连到服务器，把工具交给 Copilot 后端 Agent：

```csharp
await using McpClient mcpClient = await McpClient.CreateAsync(
    new HttpClientTransport(new() { Endpoint = new Uri("http://127.0.0.1:5300/mcp") }));

IList<McpClientTool> mcpTools = await mcpClient.ListToolsAsync();

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    name: "ZavaInventoryAgent",
    instructions: "You are ZavaShop's inventory agent. Use list_warehouses, check_stock, reserve_units, restock for live data. Never invent stock numbers.",
    tools: mcpTools.Cast<AITool>().ToArray());
```

**`Verify/Program.cs`** — 以子进程启服务并确定性清理：

```csharp
using var server = Process.Start(new ProcessStartInfo("dotnet", "run --project ../InventoryServer")
{
    RedirectStandardOutput = true,
    UseShellExecute = false,
});
await WaitForPort(5300);              // 轮询 TCP 的 helper
try { /* … 三轮对话 + substring 断言 … */ }
finally { server!.Kill(entireProcessTree: true); }
```

C# 路线与 Python 的重要验收差异：

- C# 服务是 `Verify` 启的 **独立进程**。它不允许把 `data/zava_warehouses.json` 回写磁盘 — `InventoryState` 在内存中维护 `Dictionary<(string sku, string wh), int>`。
- 审批隐式：Agent 只能看见你给定 URL 的 `McpClient` 提供的工具。C# 中没有 `on_permission_request` 回调；需要显式 HITL时，在创建哪个 `McpClient` 这一环控制。
- `ReserveUnits` 与 `Restock` 可返回与 Python 同型的值（`object`） — 强类型结果 record（例如 `record ReserveResult(int Reserved, int Remaining)`）或者字符串 `"OUT_OF_STOCK: <sku>@<wh>"` / `"NOT_FOUND: <sku>"`。

## 验收标准

1. `inventory_mcp_server.py` 使用 **FastMCP**（`from mcp.server.fastmcp import FastMCP`），并暴露四个工具：
   - `list_warehouses() -> list[dict]` — 每条包含 `code`、`name`、`region`、`currency`。
   - `check_stock(sku: str, warehouse_code: str | None = None) -> dict | str` — 返回 `{warehouse: units, ...}`（`warehouse_code` 为空则返回所有仓库）。未知 SKU 返回 `"NOT_FOUND: <sku>"`。
   - `reserve_units(sku: str, warehouse_code: str, quantity: int) -> dict | str` — 扣减库存；库存不足返回 `"OUT_OF_STOCK: <sku>@<warehouse>"`；成功返回 `{"reserved": qty, "remaining": new_count}`。
   - `restock(sku: str, warehouse_code: str, quantity: int) -> dict | str` — 增加库存；未知 SKU 返回 `"NOT_FOUND: <sku>"`。
2. 服务运行在 `http://127.0.0.1:5300/mcp`，传输方式为 Streamable HTTP。
3. 启动时从 `data/zava_warehouses.json` 加载库存。预留 / 补货只改 **内存** — **不能** 回写 JSON。
4. `inventory_agent.py` 构造 `GitHubCopilotAgent`，包含：
   - 复用 Lab 2 的 Product Advisor 工具（`from product_advisor import search_products, get_product_details` — 详见下方）。
   - `mcp_servers` 配置：`{"zava-inventory": {"type": "http", "url": "http://127.0.0.1:5300/mcp", "tools": ["*"]}}`。
   - 一个 `on_permission_request` 处理器，仅放行 `kind == "mcp"`，其余一律拒绝。
5. `verify.py`：
   - 把 MCP 服务作为子进程启动，等待 5300 端口监听。
   - 启动 Agent。
   - 跑三轮：
     1. *"我们有哪些仓库，分别在什么位置？"* — 回答必须提到 `WH-SEA`、`WH-LON`、`WH-SIN`、`WH-DXB`、`WH-GRU`。
     2. *"迪拜仓有多少 LIP-001？"* — 回答要含 `0`，且关联到 Dubai（Dubai 仓 LIP-001 库存为 0）。
     3. *"在西雅图仓预留 5 件 SKN-030。"* — 回答需报告成功，剩余库存 `115`（西雅图初始 120）。
   - 干净地结束子进程。

### 关于复用 Lab 2 代码

在 `inventory_agent.py` 顶部把 Lab 2 文件夹加入 `sys.path`：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab-02-single-agent"))
from product_advisor import search_products, get_product_details   # noqa: E402
```

这样保证 Lab 2 的交付物始终是这些工具的唯一权威来源。

## 运行

### Python

```bash
cd lab-03-mcp
uv pip install -r requirements.txt
python verify.py            # 启动服务 + Agent，自检，清理
```

如需交互式探索：

```bash
# 终端 1
python inventory_mcp_server.py
# 终端 2
python inventory_agent.py
```

### C# / .NET

```bash
cd lab-03-mcp/csharp
dotnet run --project Verify        # 启 InventoryServer、跑三轮、清理
```

如需交互式探索：

```bash
# 终端 1
cd lab-03-mcp/csharp
dotnet run --project InventoryServer
# 终端 2
cd lab-03-mcp/csharp
dotnet run --project InventoryAgent
```

## 常见错误

| 现象 | 原因 |
| --- | --- |
| 服务起来了但 Agent 说 "没有可用工具" | URL 或传输方式不对 — 必须是 `http://...:5300/mcp`，不是 `/sse` |
| `reserve_units` / `ReserveUnits` 把 JSON 改了 | 服务把 `data/zava_warehouses.json` 回写了 — 加载一次到内存，永远别写回 |
| 权限弹窗卡住工具调用（Python） | `on_permission_request` 没处理 `"mcp"` kind |
| `OUT_OF_STOCK` 触发条件不对 | 恰好把库存全预留要算成功，只有 *不够* 才返回该错误 |
| C#：`Verify` 在服务起动前退出 | 缺 `WaitForPort(5300)` helper — 发起 agent 调用前要轮询 TCP |
| C#：某轮出错后服务进程泄漏 | 未用 `finally { server.Kill(entireProcessTree: true); }` 包裹运行代码 |

Lab 3 绿了 → [Lab 4 — 多 Agent 工作流](../lab-04-multi-agent-workflow/README.zh.md)
