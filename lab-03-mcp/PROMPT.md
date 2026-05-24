# Lab 3 — Task Prompt

> **Paste the content of this file into a GitHub Issue (or `@copilot` comment) in your fork to start the Coding Agent.**

## Assignment

Assign this task to the **`zava-mcp-integrator`** custom agent.

> @copilot assign zava-mcp-integrator to this task

The agent profile lives at [`.github/agents/zava-mcp-integrator.md`](../.github/agents/zava-mcp-integrator.md). It already knows the canonical wiring pattern (Python `FastMCP` and .NET `ModelContextProtocol` side by side) and which skills to read. **Do not repeat that here.**

## Language Directive

```
target_language: both
```

Valid values: `python`, `csharp`, or `both`. Edit before pasting.

- `python` → only the Python deliverables; only `-py` skills read.
- `csharp` → only the C# deliverables; only `-csharp` skills read.
- `both` → both deliverable trees; both verify scripts must pass.

## Goal

Build the **ZavaShop Inventory MCP service** and the agent that consumes it. The agent must also reuse Lab 2's product tools (no copy-paste). Same external behaviour in both languages.

## Deliverables

### Python (`target_language: python` or `both`) — inside `lab-03-mcp/`

- `requirements.txt` — must include `mcp` (the official Python SDK).
- `inventory_mcp_server.py` — `FastMCP` server, Streamable HTTP at `http://127.0.0.1:5300/mcp`.
- `inventory_agent.py` — `GitHubCopilotAgent` wired with `mcp_servers` + `on_permission_request` that approves only `kind == "mcp"`. Imports Lab 2's tools via `sys.path`.
- `verify.py` — spawns the server subprocess, runs three turns, tears down in `finally:`.

### C# / .NET (`target_language: csharp` or `both`) — inside `lab-03-mcp/csharp/`

- `InventoryServer/InventoryServer.csproj` — `Microsoft.NET.Sdk.Web`, refs `ModelContextProtocol` + `ModelContextProtocol.AspNetCore` (`--prerelease`).
- `InventoryServer/Program.cs` — `builder.Services.AddMcpServer().WithHttpTransport().WithTools<InventoryTools>()`; `app.MapMcp("/mcp")`; runs on `http://127.0.0.1:5300`.
- `InventoryServer/InventoryTools.cs` — `[McpServerToolType]` static class with four `[McpServerTool]` methods (signatures below).
- `InventoryServer/InventoryState.cs` — loads `data/zava_warehouses.json` once into in-memory dictionaries.
- `InventoryAgent/InventoryAgent.csproj` — `Microsoft.NET.Sdk`, refs `Microsoft.Agents.AI`, `Microsoft.Agents.AI.GitHub.Copilot`, `ModelContextProtocol`, `Microsoft.Extensions.AI` (all `--prerelease`). `GitHub.Copilot.SDK` flows in transitively — do not add it directly.
- `InventoryAgent/Program.cs` — programmatic MCP client + the `SessionConfig` overload of `AsAIAgent` (the Copilot SDK throws if `OnPermissionRequest` is unset at session creation, even when tools come solely from MCP):
  ```csharp
  await using McpClient mcpClient = await McpClient.CreateAsync(
      new HttpClientTransport(new() { Endpoint = new Uri("http://127.0.0.1:5300/mcp"), Name = "zava-inventory" }));
  IList<McpClientTool> mcpTools = await mcpClient.ListToolsAsync();

  await using CopilotClient copilotClient = new(new CopilotClientOptions { CliPath = cliPath });
  await copilotClient.StartAsync();

  SessionConfig sessionConfig = new()
  {
      OnPermissionRequest = PermissionHandler.ApproveAll,     // mandatory — SDK throws otherwise
      Model = Environment.GetEnvironmentVariable("GITHUB_COPILOT_MODEL"),
      SystemMessage = new SystemMessageConfig { Mode = SystemMessageMode.Append, Content = Instructions },
      Tools =
      [
          .. mcpTools.Cast<AIFunction>(),                     // McpClientTool : AIFunction
          AIFunctionFactory.Create(CatalogTools.SearchProducts),
          AIFunctionFactory.Create(CatalogTools.GetProductDetails),
          AIFunctionFactory.Create(CatalogTools.RecommendAlternatives),
      ],
  };
  AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true,
      id: "inventory-agent", name: "InventoryAgent", description: Instructions);
  ```
- `Verify/Verify.csproj` + `Verify/Program.cs` — `Process.Start("dotnet", "run --project <abs-path-to-InventoryServer> --no-build")` (resolve the absolute path by walking up from `AppContext.BaseDirectory`), polls TCP port 5300, runs three turns in one `AgentSession`, asserts substrings, kills server in `finally`. Final line: `[OK] Lab 3 complete.`

## MCP tool signatures (exactly these)

Python:

```python
@mcp.tool()
def list_warehouses() -> list[dict]: ...   # each item: code, name, region, currency

@mcp.tool()
def check_stock(sku: str, warehouse_code: str | None = None) -> dict | str:
    """All warehouses if warehouse_code is None. "NOT_FOUND: <sku>" on unknown SKU."""

@mcp.tool()
def reserve_units(sku: str, warehouse_code: str, quantity: int) -> dict | str:
    """{"reserved": qty, "remaining": int} on success; "OUT_OF_STOCK: <sku>@<warehouse>" on insufficient stock."""

@mcp.tool()
def restock(sku: str, warehouse_code: str, quantity: int) -> dict | str: ...
```

C# (each tool decorated with `[McpServerTool, Description("...")]`):

```csharp
public static IReadOnlyList<Warehouse> ListWarehouses(InventoryState state);
public static object CheckStock(InventoryState state, string sku, string? warehouseCode = null);
public static object ReserveUnits(InventoryState state, string sku, string warehouseCode, int quantity);
public static object Restock(InventoryState state, string sku, string warehouseCode, int quantity);
```

## Acceptance criteria (every item testable in the verify script for the chosen language)

1. Server runs at `http://127.0.0.1:5300/mcp` (Streamable HTTP) in both stacks.
2. Server loads `data/zava_warehouses.json` **into memory** at startup. Mutations stay in memory — verify reads the file before and after the run and asserts it is byte-identical.
3. Python: agent's `mcp_servers` entry uses key `"zava-inventory"` and `tools: ["*"]`. Verify reads the *private* attribute `agent._mcp_servers` (the constructor normalizes `default_options` and moves `mcp_servers` / `on_permission_request` onto `agent._mcp_servers` / `agent._permission_handler`; they no longer appear in `agent.default_options`). C#: `InventoryAgent` connects via `McpClient`, casts the discovered tools as `mcpTools.Cast<AIFunction>()`, and passes them through `SessionConfig.Tools` (every `McpClientTool` extends `Microsoft.Extensions.AI.AIFunction`).
4. Python: permission handler approves only `kind == PermissionRequestKind.MCP` (verified by at least one denied non-MCP request in `verify.py`). C#: `SessionConfig.OnPermissionRequest` is mandatory — the SDK throws `ArgumentException` at session creation otherwise. Use `PermissionHandler.ApproveAll`; MCP tool calls do not flow through the CLI permission channel, so the handler only sees CLI-side kinds (shell/read/write/url).
5. Lab 2's tools are reused, not duplicated: Python uses `sys.path.insert(...)` from `lab-02-single-agent`; C# adds a `ProjectReference` to `../../lab-02-single-agent/csharp/ProductAdvisor/ProductAdvisor.csproj` (or copies only the tool delegates if a circular ref forms).
6. Turn 1: *"Which warehouses do we have, and where is each located?"* → reply mentions all five warehouse codes (`WH-SEA`, `WH-LON`, `WH-SIN`, `WH-DXB`, `WH-GRU`).
7. Turn 2: *"How many LIP-001 do we have in Dubai?"* → reply mentions `0` and `Dubai`.
8. Turn 3: *"Reserve 5 units of SKN-030 in Seattle."* → reply reports success and remaining count `115` (Seattle starts at 120).
9. Verify exits 0 on full pass; tears the server subprocess down in `finally:`. Final line: `[OK] Lab 3 complete.`

## Verification command

Python:

```bash
# or any Python 3.10+ env that satisfies requirements.txt
cd lab-03-mcp
pip install -r requirements.txt
python verify.py
```

C# / .NET (`Verify` spawns the server subprocess with `--no-build`, so build both projects first):

```bash
cd lab-03-mcp/csharp
dotnet build InventoryServer/InventoryServer.csproj
dotnet build Verify/Verify.csproj
GITHUB_COPILOT_MODEL=gpt-5.5 dotnet run --project Verify --no-build
```

## PR checklist (paste into the PR body)

- [ ] `target_language` honoured: only the language(s) declared above were touched.
- [ ] Each acceptance criterion mapped to a line in the verify script(s).
- [ ] `data/zava_warehouses.json` byte-identical before/after the run.
- [ ] Lab 2 tools reused (Python `sys.path` import or C# `ProjectReference`), not duplicated.
- [ ] Server subprocess always torn down in `finally` (Python) / `finally { server.Kill(entireProcessTree: true); }` (C#).
- [ ] No edits outside `lab-03-mcp/`.
- [ ] Python deliverables present when applicable; C# deliverables present when applicable.
