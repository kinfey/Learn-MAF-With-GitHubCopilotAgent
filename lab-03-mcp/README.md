# Lab 3 — MCP: ZavaShop Inventory Service

> Estimated time: 60 minutes. **Driven by Copilot Coding Agent.**
>
> **Learning goal**: practice MAF's **local MCP tools + tool approval (HITL)** by wiring a custom inventory MCP server into a Copilot-backed agent. The Coding Agent generates both the MCP server (Python `FastMCP` or .NET `ModelContextProtocol`) and the agent code; you decide the permission policy. Pick your language with `target_language` in [`PROMPT.md`](PROMPT.md).

## ZavaShop Story

The Product Advisor from Lab 2 can describe products, but it can't say whether they are *in stock right now*. Inventory lives in a separate system: ZavaShop's five warehouses each expose stock via a real-time API.

You will build that API as a **Model Context Protocol (MCP) server** — a `mcp` Python service that exposes stock and reservation operations as MCP tools — then plug it into a `GitHubCopilotAgent` so the LLM can call inventory operations directly.
## Microsoft Agent Framework concepts in this lab

| Concept | What it means in code | Microsoft Learn |
| --- | --- | --- |
| **Local MCP Tools** | Tools served by an MCP server you run yourself. Python uses `FastMCP` over Streamable HTTP; .NET uses `Microsoft.NET.Sdk.Web` + `AddMcpServer().WithHttpTransport()`. The agent consumes them via Python `default_options["mcp_servers"]` or .NET programmatic `McpClient` + `await mcpClient.ListToolsAsync()`. | [Tools Overview](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) (Local MCP Tools row) |
| **Tool Approval (Human-in-the-loop)** | The agent surfaces a permission request **before** invoking certain tool kinds. Python: an `on_permission_request` handler approves or denies; this lab only approves `kind == "mcp"`. .NET: tools come from a trusted local `McpClient`, so approval is implicit — callers gate access by which server URL they wire in. | [Tools Overview](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) (Tool Approval) |
| **Function + MCP tools on one agent** | The same Copilot-backed agent keeps Lab 2's function tools **and** adds MCP tools — proving they coexist and the LLM picks freely between them. In .NET pass both `AIFunctionFactory.Create(...)` and `mcpTools.Cast<AITool>()` into the same `tools:` array. | [Tools Overview](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) |
## Run This Lab

1. Open an issue (or `@copilot` comment) in your fork with the contents of [`PROMPT.md`](PROMPT.md). The first line assigns the custom agent; the `target_language` line picks `python`, `csharp`, or `both`.
2. The Coding Agent will:
   - Load the [`zava-mcp-integrator`](../.github/agents/zava-mcp-integrator.md) profile (it contains canonical patterns for **both** languages; only the matching section is read).
   - Read only the GitHub Copilot SDK + ZavaShop skills the profile points at, filtered by `target_language`.
   - Scaffold the server and agent (Python files at the lab root or C# projects under `csharp/`), plus the verify script.
   - Open a PR. You review, run the language-appropriate verify, merge.

| Layer | Where the role / API / task lives |
| --- | --- |
| Role (HOW) | [`.github/agents/zava-mcp-integrator.md`](../.github/agents/zava-mcp-integrator.md) (both Python and C# sections) |
| API reference (Python) | [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) · official `mcp` Python SDK |
| API reference (C#) | [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) · `ModelContextProtocol` + `ModelContextProtocol.AspNetCore` |
| Task (WHAT + which language) | [`PROMPT.md`](PROMPT.md) |

## What You Will Learn

- Building a Streamable HTTP MCP server with the official `mcp` Python SDK.
- Designing MCP tools that read & mutate JSON state safely.
- Wiring an MCP server into `GitHubCopilotAgent` via `default_options["mcp_servers"]`.
- Handling the `mcp` permission kind via `on_permission_request`.

## Custom Agent + Skills (set by [`PROMPT.md`](PROMPT.md))

- **Custom agent**: [`zava-mcp-integrator`](../.github/agents/zava-mcp-integrator.md) — the role profile encodes the FastMCP + agent wiring pattern.
- **Skills the agent will read**:
  - [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) — sections **MCP Servers (Local + Remote)** and **Lifecycle & Permissions**.
  - [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) — warehouse codes, stock dict shape, error-string convention.

## Architecture

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
                                     (loaded into memory; mutations
                                      persisted on shutdown to a copy)
```

## Deliverable

Depending on `target_language` the Coding Agent produces one or both of:

### Python (`target_language: python`)

```
lab-03-mcp/
├── README.md
├── PROMPT.md
├── requirements.txt
├── inventory_mcp_server.py    ← MCP server (Streamable HTTP, port 5300)
├── inventory_agent.py         ← Agent that consumes the MCP server
└── verify.py                  ← Boots server, runs scripted queries, asserts
```

### C# / .NET (`target_language: csharp`)

```
lab-03-mcp/
└── csharp/
    ├── InventoryServer/
    │   ├── InventoryServer.csproj   # Microsoft.NET.Sdk.Web, refs ModelContextProtocol + ModelContextProtocol.AspNetCore
    │   ├── Program.cs                # builder.Services.AddMcpServer().WithHttpTransport().WithTools<InventoryTools>(); app.MapMcp("/mcp")
    │   ├── InventoryTools.cs         # [McpServerToolType] static class with [McpServerTool] methods
    │   └── InventoryState.cs         # loads data/zava_warehouses.json into memory once
    ├── InventoryAgent/
    │   ├── InventoryAgent.csproj    # Microsoft.NET.Sdk, refs GitHub.Copilot.SDK, Microsoft.Agents.AI.GitHub.Copilot, ModelContextProtocol
    │   └── Program.cs                # spawns server (Process.Start) + McpClient.CreateAsync + agent
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                # boots server subprocess, runs three turns, asserts substrings, tears down
```

## .NET / C# Implementation

The Coding Agent follows the canonical pattern in [`zava-mcp-integrator`](../.github/agents/zava-mcp-integrator.md). Key snippets the verify script and reviewers should expect to see:

**`InventoryServer/Program.cs`** — hosts MCP over HTTP at `:5300/mcp`:

```csharp
var builder = WebApplication.CreateBuilder(args);
builder.Services
    .AddSingleton<InventoryState>()                 // loads JSON once
    .AddMcpServer()
    .WithHttpTransport()
    .WithTools<InventoryTools>();

var app = builder.Build();
app.MapMcp("/mcp");
app.Run("http://127.0.0.1:5300");
```

**`InventoryServer/InventoryTools.cs`** — four tools mirroring the Python signatures:

```csharp
[McpServerToolType]
public static class InventoryTools
{
    [McpServerTool, Description("List ZavaShop warehouses.")]
    public static IReadOnlyList<Warehouse> ListWarehouses(InventoryState state) => state.Warehouses;

    [McpServerTool, Description("Check stock for a SKU; warehouseCode null returns all warehouses.")]
    public static object CheckStock(InventoryState state,
        [Description("Product SKU")] string sku,
        [Description("Warehouse code (optional)")] string? warehouseCode = null) => state.CheckStock(sku, warehouseCode);

    [McpServerTool, Description("Reserve units from a warehouse. Returns OUT_OF_STOCK: <sku>@<wh> when insufficient.")]
    public static object ReserveUnits(InventoryState state, string sku, string warehouseCode, int quantity)
        => state.Reserve(sku, warehouseCode, quantity);

    [McpServerTool, Description("Restock units into a warehouse. NOT_FOUND: <sku> for unknown SKUs.")]
    public static object Restock(InventoryState state, string sku, string warehouseCode, int quantity)
        => state.Restock(sku, warehouseCode, quantity);
}
```

**`InventoryAgent/Program.cs`** — connects to the server programmatically, surfaces tools to the Copilot-backed agent:

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

**`Verify/Program.cs`** — boots the server as a subprocess and tears it down deterministically:

```csharp
using var server = Process.Start(new ProcessStartInfo("dotnet", "run --project ../InventoryServer")
{
    RedirectStandardOutput = true,
    UseShellExecute = false,
});
await WaitForPort(5300);              // helper that polls TCP
try { /* ... three agent turns + substring asserts ... */ }
finally { server!.Kill(entireProcessTree: true); }
```

Key acceptance differences vs. Python:

- The C# server is a **separate process** spawned by `Verify`. It does **not** mutate `data/zava_warehouses.json` on disk — `InventoryState` keeps a `Dictionary<(string sku, string wh), int>` in memory.
- Approval is implicit: the agent only sees tools whose URL you wired in. There is no `on_permission_request` callback in C#; if you need explicit HITL, gate which `McpClient` you create.
- The `ReserveUnits` and `Restock` C# methods may return the same kinds of values as Python (`object` typed) — a strongly-typed result record (e.g. `record ReserveResult(int Reserved, int Remaining)`) or the string `"OUT_OF_STOCK: <sku>@<wh>"` / `"NOT_FOUND: <sku>"`.

## Acceptance Criteria

1. `inventory_mcp_server.py` uses **FastMCP** (`from mcp.server.fastmcp import FastMCP`) and exposes four tools:
   - `list_warehouses() -> list[dict]` — each item has `code`, `name`, `region`, `currency`.
   - `check_stock(sku: str, warehouse_code: str | None = None) -> dict | str` — returns `{warehouse: units, ...}` (all warehouses if `warehouse_code` is None). On unknown SKU returns `"NOT_FOUND: <sku>"`.
   - `reserve_units(sku: str, warehouse_code: str, quantity: int) -> dict | str` — decrements stock; on under-stock returns `"OUT_OF_STOCK: <sku>@<warehouse>"`; on success returns `{"reserved": qty, "remaining": new_count}`.
   - `restock(sku: str, warehouse_code: str, quantity: int) -> dict | str` — increments stock; on unknown SKU returns `"NOT_FOUND: <sku>"`.
2. The server runs at `http://127.0.0.1:5300/mcp` over Streamable HTTP transport.
3. Stock state is loaded from `data/zava_warehouses.json` at startup. Reservations/restocks mutate **in-memory only** — do **not** overwrite the JSON file on disk.
4. `inventory_agent.py` builds a `GitHubCopilotAgent` with:
   - The Product Advisor tools from Lab 2 reused (`from product_advisor import search_products, get_product_details` — see note below).
   - An `mcp_servers` entry: `{"zava-inventory": {"type": "http", "url": "http://127.0.0.1:5300/mcp", "tools": ["*"]}}`.
   - An `on_permission_request` handler that approves only `kind == "mcp"` and denies everything else.
5. `verify.py`:
   - Starts the MCP server in a background subprocess and waits for it to listen on port 5300.
   - Boots the agent.
   - Runs three turns:
     1. *"Which warehouses do we have, and where is each located?"* — answer must mention `WH-SEA`, `WH-LON`, `WH-SIN`, `WH-DXB`, `WH-GRU`.
     2. *"How many LIP-001 do we have in Dubai?"* — answer must include `0` and reference Dubai (Dubai has 0 LIP-001).
     3. *"Reserve 5 units of SKN-030 in Seattle."* — answer must report success and a remaining count of `115` (Seattle starts at 120).
   - Tears down the subprocess cleanly.

### Note on importing Lab 2 code

Add Lab 2's folder to `sys.path` at the top of `inventory_agent.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab-02-single-agent"))
from product_advisor import search_products, get_product_details   # noqa: E402
```

This keeps the Lab 2 deliverable as the canonical source of truth for those tools.

## Run It

### Python

```bash
cd lab-03-mcp
uv pip install -r requirements.txt
python verify.py            # boots server + agent, asserts, tears down
```

For interactive exploration:

```bash
# Terminal 1
python inventory_mcp_server.py
# Terminal 2
python inventory_agent.py
```

### C# / .NET

```bash
cd lab-03-mcp/csharp
dotnet run --project Verify        # spawns InventoryServer, runs three turns, tears down
```

For interactive exploration:

```bash
# Terminal 1
cd lab-03-mcp/csharp
dotnet run --project InventoryServer
# Terminal 2
cd lab-03-mcp/csharp
dotnet run --project InventoryAgent
```

## Common Mistakes

| Symptom | Cause |
| --- | --- |
| Server starts but agent says "no tools available" | Wrong URL or transport — must be `http://...:5300/mcp`, not `/sse` |
| `reserve_units` / `ReserveUnits` mutates the JSON file on disk | Server is rewriting `data/zava_warehouses.json` — load once into memory and never write back |
| Permission prompt blocks tool calls (Python) | `on_permission_request` not handling `"mcp"` kind |
| `OUT_OF_STOCK` not returned correctly | Reserving exact stock should succeed; only insufficient stock returns the error |
| C#: `Verify` exits before server is ready | Missing `WaitForPort(5300)` helper — poll TCP before issuing agent turns |
| C#: server process leaks after a failed turn | `finally { server.Kill(entireProcessTree: true); }` not wrapped around the run |

When Lab 3 is green → [Lab 4 — Multi-Agent Workflows](../lab-04-multi-agent-workflow/README.md)
