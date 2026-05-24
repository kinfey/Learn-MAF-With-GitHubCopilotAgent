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

> **Reality check for verification.** The model used by both implementations is the local **GitHub Copilot CLI** (Python `GitHubCopilotAgent`, C# `CopilotClient.AsAIAgent`). Its tool list is fixed at session-creation time, so AG-UI frontend tools registered on the client do **not** transparently round-trip into the running Copilot session — the model is liable to hallucinate a tool call instead of dispatching it back to the client. To get deterministic, machine-checkable evidence that the client tool actually fired locally, every deliverable also exposes a **`/scripted-reservation`** bypass endpoint that the verify harness calls directly; the client then prints `[NOTIFY]` locally. The interactive REPL still streams real model output from the AG-UI mount.

## Deliverables

### Python (`target_language: python` or `both`) — inside `lab-05-agui/`

- `requirements.txt` — pulls in `agent-framework`, `agent-framework-ag-ui`, `fastapi`, `httpx`, `uvicorn` (unpinned).
- `server.py`:
  - Inserts `lab-02-single-agent/` and `lab-04-multi-agent-workflow/` into `sys.path` (no copy/paste).
  - Defines three `@tool` functions and a `GitHubCopilotAgent` whose `default_options={"on_permission_request": approve_all}` returns `PermissionRequestResult(kind="approve-once")` — without it the CLI denies every function call.
  - Mounts the agent at `/retail` via `add_agent_framework_fastapi_endpoint(app, agent, "/retail", dependencies=[Depends(verify_api_key)])`.
  - Adds a `POST /scripted-reservation` route (same `verify_api_key` dependency) that calls `run_retail_workflow` directly and returns `{"prompt": SCRIPTED_PROMPT, "order": <order>}`.
  - Reads `AG_UI_API_KEY` from env. Unset → log a warning **once** and pass through (dev mode). Set → 401 on missing / wrong `X-API-Key` header.
  - Boots with `uvicorn.run(app, host="127.0.0.1", port=5100)` under `if __name__ == "__main__":`.
- `client.py`:
  - `notify_local_user` tool prints `\a[NOTIFY] {message}` and returns `"OK"`.
  - `--scripted` mode: hits `POST /scripted-reservation` directly, calls `notify_local_user(...)` locally, and prints the final `… [NOTIFY]` line. Used by `verify.py`.
  - Interactive mode (default): wraps `AGUIChatClient(endpoint=..., http_client=httpx.AsyncClient(headers={"X-API-Key": ...}))` with `Agent(name="zava_ops", client=remote, tools=[notify_local_user])`, reuses `agent.create_session()` and iterates `agent.run(message, stream=True, session=session)`.
- `verify.py`:
  - Spawns the server with `subprocess.Popen([sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "5100"], start_new_session=True)`.
  - Polls port 5100 (timeout ≥ 30 s), asserts a 401 against `/scripted-reservation` without `X-API-Key`, then runs `python client.py --scripted` and asserts the captured output.
  - `finally:` block terminates the entire process group (`os.killpg(server.pid, signal.SIGTERM)` then `SIGKILL` after timeout). Exit 0 only on full pass. Final line: `[OK] Lab 5 complete.`

### C# / .NET (`target_language: csharp` or `both`) — inside `lab-05-agui/csharp/`

#### `RetailServer/RetailServer.csproj` (`Microsoft.NET.Sdk.Web`, `net10.0`)

```xml
<ItemGroup>
  <PackageReference Include="Microsoft.Agents.AI" Version="*-*" />
  <PackageReference Include="Microsoft.Agents.AI.GitHub.Copilot" Version="*-*" />
  <PackageReference Include="Microsoft.Agents.AI.Hosting" Version="*-*" />
  <PackageReference Include="Microsoft.Agents.AI.Hosting.AGUI.AspNetCore" Version="*-*" />
  <PackageReference Include="Microsoft.Agents.AI.Workflows" Version="*-*" />
  <PackageReference Include="Microsoft.Extensions.AI" Version="*-*" />
</ItemGroup>
<ItemGroup>
  <ProjectReference Include="../../../lab-02-single-agent/csharp/ProductAdvisor/ProductAdvisor.csproj" />
  <ProjectReference Include="../../../lab-04-multi-agent-workflow/csharp/Workflows/Workflows.csproj" />
</ItemGroup>
```

Do **not** add a direct `PackageReference` to `GitHub.Copilot.SDK` — let it flow transitively through `Microsoft.Agents.AI.GitHub.Copilot`. A direct ref breaks NuGet restore (`CopilotCliVersion is not set`).

#### `RetailServer/Program.cs`

- Build `CopilotClient` at module scope with `await copilotClient.StartAsync()` **before** `WebApplication.CreateBuilder(args)`. `CopilotClientOptions.CliPath` reads `COPILOT_CLI_PATH` / `GITHUB_COPILOT_CLI_PATH` (default `"copilot"`).
- Build the agent with a full `SessionConfig`:

  ```csharp
  SessionConfig sessionConfig = new()
  {
      OnPermissionRequest = PermissionHandler.ApproveAll,
      Model = Environment.GetEnvironmentVariable("GITHUB_COPILOT_MODEL") ?? "gpt-5.5",
      SystemMessage = new SystemMessageConfig { Mode = SystemMessageMode.Append, Content = Instructions },
      Tools =
      [
          AIFunctionFactory.Create(ServerTools.SearchProducts,    name: "search_products",     description: "..."),
          AIFunctionFactory.Create(ServerTools.GetWarehouseStock, name: "get_warehouse_stock", description: "..."),
          AIFunctionFactory.Create(ServerTools.RunRetailWorkflow, name: "run_retail_workflow", description: "..."),
      ],
  };

  AIAgent retailAgent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true,
      id: "retail-orchestrator", name: AgentName, description: Instructions);
  ```

  Calling the bare `AsAIAgent(ownsClient, name, instructions, tools)` overload throws `ArgumentException "An OnPermissionRequest handler is required"` at first tool call — always go through `SessionConfig`. Always pass an **explicit `name:`** to `AIFunctionFactory.Create` so the function name the model sees matches the snake_case names referenced in the system prompt.
- Wire AG-UI:

  ```csharp
  builder.Services.AddHttpClient().AddLogging();
  builder.Services.AddAGUI();
  builder.AddAIAgent(AgentName, (_, _) => retailAgent).WithInMemorySessionStore();

  WebApplication app = builder.Build();
  app.UseMiddleware<ApiKeyMiddleware>();
  app.MapAGUI(AgentName, "/retail");      // (agentName, pattern) — order matters
  ```

  Never define a local `MapAGUI` extension on `WebApplication` — it shadows the real `IEndpointRouteBuilder` overload and the client will only see a one-shot JSON blob.
- Add the scripted bypass:

  ```csharp
  app.MapPost("/scripted-reservation", async (ReservationRequest request) =>
  {
      var order = await ServerTools.RunRetailWorkflow(
          request.CustomerId, request.Sku, request.Quantity, request.PreferredWarehouse);
      return Results.Ok(new { order });
  });

  await app.RunAsync("http://127.0.0.1:5100");
  ```
- `internal sealed record ReservationRequest(string CustomerId, string Sku, int Quantity, string PreferredWarehouse);`

#### `RetailServer/Tools/ServerTools.cs`

`public static` methods with `[Description(...)]`:

- `IReadOnlyList<CatalogRow> SearchProducts(string query)` — delegates to Lab 2's `CatalogTools.SearchProducts`.
- `int GetWarehouseStock(string sku, string warehouseCode)` — reads `data/zava_warehouses.json` (resolved by walking up from `AppContext.BaseDirectory`).
- `Task<OrderRecord> RunRetailWorkflow(string customerId, string sku, int quantity, string preferredWarehouse)` — builds the Lab 4 workflow with `RetailWorkflow.BuildRetailWorkflow()` and runs it through `InProcessExecution.RunStreamingAsync`, returning the `OrderRecord` from `WorkflowOutputEvent`. Translate `WorkflowErrorEvent` / `ExecutorFailedEvent` into `InvalidOperationException`.

#### `RetailServer/Middleware/ApiKeyMiddleware.cs`

`public sealed class ApiKeyMiddleware(RequestDelegate next, ILogger<ApiKeyMiddleware> logger)` — reads `AG_UI_API_KEY` from env. Set → 401 on missing / wrong `X-API-Key` header. Unset → log a one-time warning and pass through.

#### `RetailClient/RetailClient.csproj` (`Microsoft.NET.Sdk`, `net10.0`)

```xml
<ItemGroup>
  <PackageReference Include="Microsoft.Agents.AI" Version="*-*" />
  <PackageReference Include="Microsoft.Agents.AI.AGUI" Version="*-*" />
  <PackageReference Include="Microsoft.Extensions.AI" Version="*-*" />
</ItemGroup>
```

#### `RetailClient/Program.cs`

- `using HttpClient http = new() { Timeout = TimeSpan.FromSeconds(60) };` + add `X-API-Key` to `DefaultRequestHeaders` if `AG_UI_API_KEY` is set.
- `--scripted` mode: `POST /scripted-reservation` directly, parse the `order`, call `NotifyLocalUser.Notify(notice)`, and print `"<scripted prompt>\n<notice> [NOTIFY]"`.
- Interactive mode (default):

  ```csharp
  AGUIChatClient chatClient = new(http, endpoint);              // endpoint is a string, NOT a Uri
  AIAgent agent = chatClient.AsAIAgent(
      name: "zava_ops",
      tools:
      [
          AIFunctionFactory.Create(
              NotifyLocalUser.Notify,
              name: "notify_local_user",
              description: "Ring the operator's terminal locally and print [NOTIFY] <message>."),
      ]);

  AgentSession session = await agent.CreateSessionAsync();
  while (true)
  {
      Console.Write("you> ");
      string? message = Console.ReadLine();
      if (string.IsNullOrWhiteSpace(message)) break;
      await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(message, session))
          Console.Write(update);
      Console.WriteLine();
  }
  ```

#### `RetailClient/Tools/NotifyLocalUser.cs`

```csharp
[Description("Ring the operator's terminal and print [NOTIFY] message.")]
public static string Notify(string message)
{
    Console.Write('\a');
    Console.WriteLine($"[NOTIFY] {message}");
    return "OK";
}
```

#### `Verify/Verify.csproj` (`Microsoft.NET.Sdk`, `net10.0`)

References `../RetailClient/RetailClient.csproj` so the harness can read the client source path through the build graph.

#### `Verify/Program.cs`

- **Locate the repo root** by walking up from `AppContext.BaseDirectory` until `data/zava_warehouses.json` exists. Use absolute paths to build `serverProj` and `clientProj` — relative paths break because the verify binary lives in `bin/Debug/net10.0/`.
- Spawn the server: `dotnet run --project "{serverProj}" -c Debug --no-build`, env `AG_UI_API_KEY=test-key-do-not-use-in-prod`. Pre-build all three projects before invoking Verify.
- Wait for port 5100 (timeout ≥ 60 s), then `POST /scripted-reservation` without `X-API-Key` and assert 401.
- Spawn the client: `dotnet run --project "{clientProj}" -c Debug --no-build -- --scripted`, same env plus `AGUI_SERVER_URL=http://127.0.0.1:5100/retail`. Capture stdout+stderr and run every assertion.
- `finally { if (!server.HasExited) { server.Kill(entireProcessTree: true); await server.WaitForExitAsync(); } }`. Exit 0 only on full pass. Final line: `[OK] Lab 5 complete.`

## Server tools (server side only — Python `server.py` / C# `RetailServer/Tools/ServerTools.cs`)

```python
@tool(approval_mode="never_require")
def search_products(query: str) -> list[dict]: ...           # reuse Lab 2 via sys.path

@tool(approval_mode="never_require")
def get_warehouse_stock(sku: str, warehouse_code: str) -> int | str: ...  # reads data/zava_warehouses.json

@tool(approval_mode="never_require")
async def run_retail_workflow(customer_id: str, sku: str, quantity: int, preferred_warehouse: str) -> dict: ...
   # awaits build_retail_workflow().run({...}) from Lab 4 via sys.path
```

```csharp
[Description("Search the ZavaShop product catalog.")]
public static IReadOnlyList<CatalogRow> SearchProducts(string query) { ... }

[Description("Get current stock for a SKU at a warehouse.")]
public static int GetWarehouseStock(string sku, string warehouseCode) { ... }

[Description("Run the Lab 4 retail workflow and return the final OrderRecord.")]
public static Task<OrderRecord> RunRetailWorkflow(string customerId, string sku, int quantity, string preferredWarehouse) { ... }
```

`@tool(approval_mode="never_require")` only skips the framework-side gate. The Copilot CLI still emits a `CUSTOM_TOOL` permission per call, so the server agent **must** install `default_options={"on_permission_request": approve_all}` returning `PermissionRequestResult(kind="approve-once")`. The C# equivalent is `SessionConfig.OnPermissionRequest = PermissionHandler.ApproveAll`.

## Client tool (client side only — Python `client.py` / C# `RetailClient/Tools/NotifyLocalUser.cs`; server must NOT define it)

```python
@tool(approval_mode="never_require")
def notify_local_user(message: str) -> str:
    """Ring the operator's terminal and print [NOTIFY] message. Returns "OK"."""
    print(f"\a[NOTIFY] {message}", flush=True)
    return "OK"
```

```csharp
[Description("Ring the operator's terminal and print [NOTIFY] message.")]
public static string Notify(string message) { Console.Write('\a'); Console.WriteLine($"[NOTIFY] {message}"); return "OK"; }
```

## Acceptance criteria (every item is testable in `verify.py` / `Verify/Program.cs`)

1. Server runs at `http://127.0.0.1:5100`. AG-UI is mounted at `/retail` (Python: `add_agent_framework_fastapi_endpoint`; C#: `app.MapAGUI("retail_orchestrator", "/retail")`). The C# `MapAGUI` overload used is `(IEndpointRouteBuilder, string agentName, string pattern)` — the agent name **must** match the name passed to `AddAIAgent` exactly (case-sensitive).
2. `AG_UI_API_KEY` set → requests without `X-API-Key` (or with a wrong one) are rejected with **401** on both `/retail` and `/scripted-reservation`. Unset → server logs a one-time warning and allows the request (dev-mode behaviour from the AG-UI skill).
3. The three server tools are defined exactly once on the server side and **not** on the client side. Both implementations name them `search_products`, `get_warehouse_stock`, `run_retail_workflow` — Python via decorator name, C# via the explicit `name:` argument of `AIFunctionFactory.Create`.
4. `notify_local_user` (Python) / `NotifyLocalUser.Notify` (C#) is defined exactly once on the client side and **not** on the server side. The C# client tool is registered via `AIFunctionFactory.Create(NotifyLocalUser.Notify, name: "notify_local_user", description: "...")`.
5. Lab 2 and Lab 4 are reused, not copy-pasted: Python via `sys.path.insert(0, …)` for `lab-02-single-agent` and `lab-04-multi-agent-workflow`; C# via `ProjectReference` to `lab-02-single-agent/csharp/ProductAdvisor/ProductAdvisor.csproj` and `lab-04-multi-agent-workflow/csharp/Workflows/Workflows.csproj`.
6. Server exposes `POST /scripted-reservation` taking `{customer_id, sku, quantity, preferred_warehouse}` and returning `{order: <Lab 4 OrderRecord>}`. The verify harness calls this directly to obtain a deterministic Lab 4 tracking number — `/retail` is exercised only for the 401 check and for ad-hoc interactive smoke tests.
7. Verify runs a scripted turn via `--scripted` against `/scripted-reservation` with payload `customer_id=CUST-501`, `sku=LIP-001`, `quantity=2`, `preferred_warehouse=WH-SEA` (matching the prompt: *"Please reserve 2 units of LIP-001 from the Seattle warehouse for customer CUST-501, and notify me locally once the reservation completes."*).
8. The captured stdout+stderr of the scripted client turn:
   - matches `ZS-[0-9A-F]{8}` (tracking number from Lab 4),
   - contains `LIP-001` and `WH-SEA`,
   - contains the literal `[NOTIFY]` (proves the client tool fired locally).
9. Verify sets `AG_UI_API_KEY = "test-key-do-not-use-in-prod"` for both subprocesses before booting. The client subprocess also receives `AGUI_SERVER_URL=http://127.0.0.1:5100/retail`.
10. Verify tears down the server subprocess on every exit path (Python `finally:` + process-group kill; C# `finally { server.Kill(entireProcessTree: true); }`). Port 5100 must be free when Verify exits. Exit 0 only on full pass. Final line: `[OK] Lab 5 complete.`
11. C# only: `builder.AddAIAgent(...)` chain ends with `.WithInMemorySessionStore()`. The agent is constructed with `CopilotClient.AsAIAgent(sessionConfig, ownsClient, id, name, description)` — never the bare `(ownsClient, name, instructions, tools)` overload. `SessionConfig.OnPermissionRequest` is `PermissionHandler.ApproveAll`. No custom `MapAGUI` extension is defined on `WebApplication`.
12. Python only: the `GitHubCopilotAgent` instance is constructed with `default_options={"on_permission_request": <handler>}` where the handler returns `PermissionRequestResult(kind="approve-once")` from `copilot.session`. Without it the CLI denies every `CUSTOM_TOOL` permission and the LLM reports "tool was denied permission".

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
dotnet build RetailServer/RetailServer.csproj
dotnet build RetailClient/RetailClient.csproj
dotnet build Verify/Verify.csproj
dotnet run --project Verify --no-build
```

(Pre-building all three projects matters — Verify spawns subprocesses with `--no-build` to keep stdout deterministic.)

## PR checklist (paste into the PR body)

- [ ] `target_language` directive present and obeyed.
- [ ] Server tools live only on the server side; client tool lives only on the client side.
- [ ] Server agent has a working permission handler (`approve-once` / `PermissionHandler.ApproveAll`).
- [ ] `/scripted-reservation` bypass endpoint exists and 401s without `X-API-Key`.
- [ ] Lab 2 and Lab 4 imported / referenced — never duplicated.
- [ ] Verify cleans up the server subprocess and frees port 5100 on every exit path.
- [ ] Each acceptance criterion mapped to a line in `verify.py` and/or `Verify/Program.cs`.
- [ ] C#: `MapAGUI` agent name matches `AddAIAgent` exactly; `.WithInMemorySessionStore()` present; no stub `MapAGUI` extension on `WebApplication`; no direct `GitHub.Copilot.SDK` `PackageReference`.
- [ ] C#: every server and client tool is registered with `AIFunctionFactory.Create(..., name: "snake_case_name", description: "...")` matching the system prompt.
- [ ] No edits outside `lab-05-agui/`.
