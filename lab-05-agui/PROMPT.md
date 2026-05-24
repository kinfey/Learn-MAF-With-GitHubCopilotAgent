# Lab 5 — Task Prompt

> **Paste the content of this file into a GitHub Issue (or `@copilot` comment) in your fork to start the Coding Agent.**

## Assignment

Assign this task to the **`zava-agui-engineer`** custom agent.

> @copilot assign zava-agui-engineer to this task

The agent profile lives at [`.github/agents/zava-agui-engineer.md`](../.github/agents/zava-agui-engineer.md). It already knows the server/client/verify shape for **both Python and C#** and which skills to read. **Do not repeat that here.**

## Language Directive

```
target_language: both
```

Allowed values: `python`, `csharp`, `both`. The agent reads only the matching AG-UI skill (`agent-framework-agui-py` or `agent-framework-agui-csharp`) plus the matching workflow and Copilot SDK skills, and scaffolds only the matching files. When `both`, deliver Python at the lab root *and* C# under `csharp/`.

## Goal

Publish the Lab 4 retail workflow behind an **AG-UI** HTTP/SSE endpoint, and consume it with a matching client that fires a **client-side** notification tool. Server tools and client tools must live in different files / projects.

## Deliverables

### Python (`target_language: python` or `both`) — inside `lab-05-agui/`

- `requirements.txt`.
- `server.py` — FastAPI + AG-UI mounted at `/retail` on port `5100`.
- `client.py` — `Agent` wrapping `AGUIChatClient` + the client-only tool.
- `verify.py` — boots the server subprocess, runs one scripted turn, asserts, tears down in `finally:`.

### C# / .NET (`target_language: csharp` or `both`) — inside `lab-05-agui/csharp/`

- `RetailServer/RetailServer.csproj` — `Microsoft.NET.Sdk.Web`, `net10.0`, refs (all `--prerelease` where applicable): `Microsoft.Agents.AI`, `Microsoft.Agents.AI.GitHub.Copilot`, `Microsoft.Agents.AI.Workflows`, `Microsoft.Agents.AI.Hosting.AGUI.AspNetCore`, `GitHub.Copilot.SDK`, plus `ProjectReference` to `../../lab-04-multi-agent-workflow/csharp/Workflows/Workflows.csproj`.
- `RetailServer/Program.cs` — `builder.Services.AddAGUI()` + `builder.AddAIAgent("retail_orchestrator", sp => ...).WithInMemorySessionStore()` + `app.UseMiddleware<ApiKeyMiddleware>()` + `app.MapAGUI("retail_orchestrator", "/retail")` + `app.Run("http://127.0.0.1:5100")`.
- `RetailServer/Tools/ServerTools.cs` — `static` methods `SearchProducts`, `GetWarehouseStock`, `RunRetailWorkflow`, each with `[Description(...)]`, exposed via `AIFunctionFactory.Create(...)`.
- `RetailServer/Middleware/ApiKeyMiddleware.cs` — reads `AG_UI_API_KEY` from env. Set → require matching `X-API-Key` header or respond 401. Unset → log a warning and pass through (dev mode).
- `RetailClient/RetailClient.csproj` — `Microsoft.NET.Sdk`, refs `Microsoft.Agents.AI`, `Microsoft.Agents.AI.AGUI`.
- `RetailClient/Program.cs` — `new AGUIChatClient(httpClient, new Uri(endpoint))` + `chatClient.AsAIAgent(name: "zava_ops", tools: new[] { AIFunctionFactory.Create(NotifyLocalUser.Notify) })` + REPL streaming via `agent.CreateSessionAsync()` and `session.RunStreamingAsync(input)`.
- `RetailClient/Tools/NotifyLocalUser.cs` — `[Description(...)] public static string Notify(string message)`.
- `Verify/Verify.csproj` — refs `RetailClient.csproj`.
- `Verify/Program.cs` — `Process.Start("dotnet", "run --project ../RetailServer")` + `WaitForPortAsync(5100)` + scripted turn + asserts + `finally { server.Kill(entireProcessTree: true); }`. Exit 0 only on full pass. Final line: `[OK] Lab 5 complete.`.

## Server tools (server side only — Python `server.py` / C# `RetailServer/Tools/ServerTools.cs`)

```python
@tool
def search_products(query: str) -> list[dict]: ...           # reuse Lab 2 via sys.path

@tool
def get_warehouse_stock(sku: str, warehouse_code: str) -> int | str: ...  # reads data/zava_warehouses.json

@tool
def run_retail_workflow(customer_id: str, sku: str, quantity: int, preferred_warehouse: str) -> dict: ...
   # imports build_retail_workflow from Lab 4 via sys.path
```

```csharp
[Description("Search the ZavaShop product catalog.")]
public static IReadOnlyList<Product> SearchProducts(string query) { ... }

[Description("Get current stock for a SKU at a warehouse.")]
public static int GetWarehouseStock(string sku, string warehouseCode) { ... }

[Description("Run the Lab 4 retail workflow and return the final OrderRecord.")]
public static Task<OrderRecord> RunRetailWorkflow(string customerId, string sku, int quantity, string preferredWarehouse) { ... }
```

## Client tool (client side only — Python `client.py` / C# `RetailClient/Tools/NotifyLocalUser.cs`; server must NOT define it)

```python
@tool
def notify_local_user(message: str) -> str:
    """Ring the operator's terminal and print [NOTIFY] message. Returns "OK"."""
```

```csharp
[Description("Ring the operator's terminal and print [NOTIFY] message.")]
public static string Notify(string message) { Console.Write('\a'); Console.WriteLine($"[NOTIFY] {message}"); return "OK"; }
```

## Acceptance criteria (every item is testable in `verify.py` / `Verify/Program.cs`)

1. Server runs at `http://127.0.0.1:5100`, AG-UI mounted at `/retail` (Python: `add_agent_framework_fastapi_endpoint`; C#: `app.MapAGUI("retail_orchestrator", "/retail")`).
2. `AG_UI_API_KEY` set → requests without `X-API-Key` (or with a wrong one) are rejected with **401**. Unset → server logs a warning and allows the request (dev-mode behavior from the AG-UI skill).
3. The three server tools are defined exactly once on the server side and **not** on the client side.
4. `notify_local_user` / `NotifyLocalUser.Notify` is defined exactly once on the client side and **not** on the server side.
5. Lab 2 and Lab 4 are reused, not copy-pasted: Python via `sys.path`; C# via `ProjectReference` to `lab-04 Workflows.csproj` and (if used) Lab 2's project.
6. Verify runs a single scripted turn against the server:
   *"Please reserve 2 units of LIP-001 from the Seattle warehouse for customer CUST-501, and notify me locally once the reservation completes."*
7. The final response text:
   - matches `ZS-[0-9A-F]{8}` (tracking number from Lab 4),
   - contains `LIP-001` and `WH-SEA`,
   - contains the literal `[NOTIFY]` (proves the client tool fired locally).
8. Verify sets `AG_UI_API_KEY = "test-key-do-not-use-in-prod"` for both subprocesses before booting.
9. Verify tears down the server subprocess on every exit path (Python `finally:` / C# `finally { server.Kill(entireProcessTree: true); }`). Exit 0 only on full pass. Final line: `[OK] Lab 5 complete.`
10. C# only: `builder.AddAIAgent(...)` chain ends with `.WithInMemorySessionStore()`; the agent name passed to `MapAGUI` matches the name passed to `AddAIAgent` exactly (case-sensitive).

## Verification commands

### Python

```bash
cd lab-05-agui
uv pip install -r requirements.txt
python verify.py
```

### C# / .NET

```bash
cd lab-05-agui/csharp
dotnet run --project Verify
```

## PR checklist (paste into the PR body)

- [ ] `target_language` directive present and obeyed.
- [ ] Server tools live only on the server side; client tool lives only on the client side.
- [ ] Lab 2 and Lab 4 imported / referenced — never duplicated.
- [ ] Verify cleans up the server subprocess on every exit path.
- [ ] Each acceptance criterion mapped to a line in `verify.py` and/or `Verify/Program.cs`.
- [ ] C#: `MapAGUI` agent name matches `AddAIAgent` exactly; `.WithInMemorySessionStore()` present.
- [ ] No edits outside `lab-05-agui/`.
