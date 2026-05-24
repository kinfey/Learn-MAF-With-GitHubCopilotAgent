# Lab 5 — AGUI: Hosted Coding-Agent UI

> Estimated time: 75 minutes. **Driven by Copilot Coding Agent.**
>
> **Learning goal**: practice MAF's **AG-UI integration + hybrid tool execution** by exposing the Lab 4 workflow over HTTP/SSE behind an API-key gate. The GitHub Copilot SDK still powers the agent itself; the Coding Agent writes both server and client; you decide which tools live on which side. Pick your language with `target_language` in [`PROMPT.md`](PROMPT.md): Python uses FastAPI + `add_agent_framework_fastapi_endpoint`; C# uses ASP.NET Core (`Microsoft.NET.Sdk.Web`) + `AddAGUI()` + `MapAGUI(...)` with the GitHub Copilot SDK backbone.

## ZavaShop Story

Your retail workflow from Lab 4 works on the command line, but the ops team lives in a browser. They want a chat-style UI where they can:

- Type customer orders in natural language ("Reserve 2 LIP-001 for CUST-501 from Seattle").
- Watch the workflow execute live, step by step.
- Approve sensitive actions (large reservations) before they happen.

You will wrap the retail workflow in an **AG-UI** HTTP/SSE endpoint using `add_agent_framework_fastapi_endpoint`, then build a Python `AGUIChatClient` that consumes it interactively. You will also add one **client-side tool** to demonstrate AG-UI's hybrid execution model.

## Microsoft Agent Framework concepts in this lab

Lab 5 lives in the **Integrations** layer of MAF — it doesn't introduce new agent or workflow primitives, it ships them over a protocol.

| Concept | What it means in code | Microsoft Learn |
| --- | --- | --- |
| **AG-UI integration** | A first-class **UI Framework integration**: expose any `Agent` or `Workflow` over HTTP/SSE so any AG-UI client (Python, C#, web) can stream events. Python: `add_agent_framework_fastapi_endpoint(app, agent, "/retail", dependencies=[...])`. C#: `builder.Services.AddAGUI()` + `builder.AddAIAgent(name, factory).WithInMemorySessionStore()` + `app.MapAGUI(name, "/retail")`. | [Integrations](https://learn.microsoft.com/en-us/agent-framework/integrations/) (UI Framework integrations) |
| **Workflow-as-Agent in AG-UI** | Wraps a `Workflow` for AG-UI so each conversation thread gets its own fresh workflow instance and state. Python: `AgentFrameworkWorkflow(workflow_factory=...)`. C#: register a factory `builder.AddAIAgent("retail_orchestrator", sp => BuildOrchestrator(sp))`. | [Workflows overview](https://learn.microsoft.com/en-us/agent-framework/workflows/) (the `.as_agent()` pattern) |
| **Hybrid tool execution** | Some tools live on the server (catalog / inventory / workflow), some on the client (`notify_local_user`). The AG-UI protocol negotiates which side runs each invocation. Same model in both languages — register the tool on the side where it should actually run. | [Tools Overview](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) |
| **Auth at the integration boundary** | The AG-UI endpoint always sits behind an identity check. Python: FastAPI `Depends(verify_api_key)`. C#: an ASP.NET Core middleware that reads `X-API-Key` and short-circuits with `401` before the AG-UI handler. | [Integrations](https://learn.microsoft.com/en-us/agent-framework/integrations/) |

## Run This Lab

1. Open an issue (or `@copilot` comment) in your fork with the contents of [`PROMPT.md`](PROMPT.md). The first line assigns the custom agent; `target_language` picks `python`, `csharp`, or `both`.
2. The Coding Agent will:
   - Load the [`zava-agui-engineer`](../.github/agents/zava-agui-engineer.md) profile (server / client / verify shape for both languages).
   - Read the AG-UI skill matching the chosen language plus minimal slices of the workflows + Copilot SDK skills.
   - Scaffold the language-appropriate files (Python `.py` at the lab root; C# under `csharp/`).
   - Open a PR. You review, run the language-matching verify, merge.

| Layer | Where the role / API / task lives |
| --- | --- |
| Role (HOW) | [`.github/agents/zava-agui-engineer.md`](../.github/agents/zava-agui-engineer.md) (Python + C# canonical patterns) |
| API reference (Python) | [`agent-framework-agui-py`](../.github/skills/agent-framework-agui-py/SKILL.md), [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md), [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) |
| API reference (C#) | [`agent-framework-agui-csharp`](../.github/skills/agent-framework-agui-csharp/SKILL.md), [`agent-framework-workflows-csharp`](../.github/skills/agent-framework-workflows-csharp/SKILL.md), [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) |
| Task (WHAT + which language) | [`PROMPT.md`](PROMPT.md) |

## What You Will Learn

- Hosting an `Agent` (and a `Workflow`) behind an AG-UI FastAPI endpoint.
- Streaming events over SSE to a Python client with `AGUIChatClient`.
- Maintaining thread-scoped state with `AgentFrameworkWorkflow(workflow_factory=...)`.
- Hybrid tool execution — server has heavy tools (catalog/inventory); client has a local tool (`notify_local_user`) that runs in the operator's terminal.
- Protecting the endpoint with a FastAPI API-key dependency.

## Custom Agent + Skills (set by [`PROMPT.md`](PROMPT.md))

- **Custom agent**: [`zava-agui-engineer`](../.github/agents/zava-agui-engineer.md) — the role profile encodes the server/client/verify shape and the hybrid execution split.
- **Skills the agent will read**:
  - [`agent-framework-agui-py`](../.github/skills/agent-framework-agui-py/SKILL.md) — every section.
  - [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md) — only **workflow_factory** patterns.
  - [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) — only **Tools** and **Sessions**.
- **Reused from previous labs**: Lab 4's `retail_workflow.py` and Lab 2's `search_products` (imported via `sys.path`, not duplicated).

## Architecture

```
┌──────────────────────────────────────┐   HTTP/SSE   ┌────────────────────────────────────────┐
│ server.py                            │ ───────────► │ client.py                              │
│ FastAPI                              │              │ Agent(client=AGUIChatClient(...),      │
│ + add_agent_framework_fastapi_       │ ◄─────────── │         tools=[notify_local_user])     │
│   endpoint(app, retail_orchestrator, │              │ + AgentSession for multi-turn          │
│   "/retail", deps=[API key])         │              │ + streams text chunks                  │
│ port 5100, X-API-Key required        │              │                                        │
│ server tools: search_products,       │              │ client tool:                           │
│   get_warehouse_stock,               │              │   notify_local_user(msg) — terminal    │
│   run_retail_workflow                │              │     beep + print                       │
└──────────────────────────────────────┘              └────────────────────────────────────────┘
```

- `retail_orchestrator` is a `GitHubCopilotAgent` that wraps Lab 4's `build_retail_workflow()` and exposes it as a tool (`run_retail_workflow(...)`).
- Server-side tools: read catalog, check warehouse stock, run the workflow.
- Client-side tool: `notify_local_user(message)` — fired from the *operator's machine* whenever a reservation succeeds.

## Deliverable

### Python (`target_language: python`)

```
lab-05-agui/
├── README.md
├── PROMPT.md
├── requirements.txt
├── server.py             ← FastAPI + AG-UI endpoint
├── client.py             ← AGUIChatClient + Agent wrapper + client tool
└── verify.py             ← Boots server, runs scripted client turn, asserts
```

### C# / .NET (`target_language: csharp`)

```
lab-05-agui/
└── csharp/
    ├── RetailServer/
    │   ├── RetailServer.csproj   # Microsoft.NET.Sdk.Web; refs Microsoft.Agents.AI.Hosting.AGUI.AspNetCore,
    │   │                         #   Microsoft.Agents.AI.GitHub.Copilot, Microsoft.Agents.AI.Workflows,
    │   │                         #   GitHub.Copilot.SDK; ProjectReference to lab-04 Workflows.csproj
    │   ├── Program.cs            # AddAGUI() + AddAIAgent(...).WithInMemorySessionStore() + ApiKeyMiddleware + MapAGUI
    │   ├── Tools/ServerTools.cs  # [Description]-annotated static methods exposed as AIFunctions
    │   └── Middleware/ApiKeyMiddleware.cs
    ├── RetailClient/
    │   ├── RetailClient.csproj   # Microsoft.NET.Sdk; refs Microsoft.Agents.AI.AGUI, Microsoft.Agents.AI
    │   ├── Program.cs            # new AGUIChatClient(httpClient, endpoint).AsAIAgent(name, tools)
    │   └── Tools/NotifyLocalUser.cs # client-only tool
    └── Verify/
        ├── Verify.csproj         # refs RetailClient.csproj
        └── Program.cs            # boots RetailServer subprocess, runs scripted turn, asserts, kills in finally
```

## .NET / C# Implementation

Follow [`zava-agui-engineer`](../.github/agents/zava-agui-engineer.md). Key shapes:

**Server — `RetailServer/Program.cs`**:

```csharp
WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

builder.Services.AddAGUI();
builder.Services.AddSingleton(copilotClient);

builder.AddAIAgent("retail_orchestrator", sp =>
{
    var copilot = sp.GetRequiredService<CopilotClient>();
    return copilot.AsAIAgent(
        ownsClient: false,
        name: "retail_orchestrator",
        instructions: "You are ZavaShop's retail orchestrator. Use the tools to honor reservations.",
        tools: new[]
        {
            AIFunctionFactory.Create(ServerTools.SearchProducts),
            AIFunctionFactory.Create(ServerTools.GetWarehouseStock),
            AIFunctionFactory.Create(ServerTools.RunRetailWorkflow),
        });
}).WithInMemorySessionStore();

WebApplication app = builder.Build();
app.UseMiddleware<ApiKeyMiddleware>();   // checks X-API-Key against AG_UI_API_KEY
app.MapAGUI("retail_orchestrator", "/retail");
app.Run("http://127.0.0.1:5100");
```

**Server tools — `RetailServer/Tools/ServerTools.cs`** use `[Description(...)]` so `AIFunctionFactory.Create(...)` picks up the schema, and `RunRetailWorkflow` calls Lab 4's workflow via project reference:

```csharp
[Description("Run the Lab 4 retail workflow and return the final order record.")]
public static async Task<OrderRecord> RunRetailWorkflow(
    string customerId, string sku, int quantity, string preferredWarehouse)
{
    Workflow workflow = RetailWorkflow.BuildRetailWorkflow(/* agents */);
    CustomerOrder input = new(customerId, sku, quantity, preferredWarehouse);
    await using StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, input);
    await foreach (WorkflowEvent evt in run.WatchStreamAsync())
    {
        if (evt is OutputEvent<OrderRecord> output) return output.Value;
    }
    throw new InvalidOperationException("Workflow produced no OrderRecord.");
}
```

**Client — `RetailClient/Program.cs`** registers the **client-only** tool and streams replies:

```csharp
using HttpClient httpClient = new() { Timeout = TimeSpan.FromSeconds(60) };
httpClient.DefaultRequestHeaders.Add("X-API-Key", Environment.GetEnvironmentVariable("AG_UI_API_KEY")!);

AGUIChatClient chatClient = new(httpClient, new Uri("http://127.0.0.1:5100/retail"));
AIAgent agent = chatClient.AsAIAgent(
    name: "zava_ops",
    tools: new[] { AIFunctionFactory.Create(NotifyLocalUser.Notify) });   // client-side only

AgentSession session = await agent.CreateSessionAsync();
await foreach (string chunk in session.RunStreamingAsync(userMessage))
    Console.Write(chunk);
```

**Client tool — `RetailClient/Tools/NotifyLocalUser.cs`** (must NOT exist on the server):

```csharp
public static class NotifyLocalUser
{
    [Description("Ring the operator's terminal and print [NOTIFY] message.")]
    public static string Notify(string message)
    {
        Console.Write('\a');
        Console.WriteLine($"[NOTIFY] {message}");
        return "OK";
    }
}
```

**Verify — `Verify/Program.cs`** boots `RetailServer` as a subprocess, polls the port, runs one scripted turn through `RetailClient` (or its library form), and tears down in `finally`:

```csharp
Process server = Process.Start(new ProcessStartInfo("dotnet", "run --project ../RetailServer")
{
    EnvironmentVariables = { ["AG_UI_API_KEY"] = "test-key-do-not-use-in-prod" },
});
try
{
    await WaitForPortAsync(5100);
    string final = await RunScriptedTurnAsync("Please reserve 2 units of LIP-001 ...");
    Assert.Matches(@"ZS-[0-9A-F]{8}", final);
    Assert.Contains("LIP-001", final);
    Assert.Contains("WH-SEA", final);
    Assert.Contains("[NOTIFY]", final);
    Console.WriteLine("[OK] Lab 5 complete.");
    return 0;
}
finally { server.Kill(entireProcessTree: true); }
```

## Acceptance Criteria

### Server (`server.py`)

1. Imports `build_retail_workflow` from `lab-04-multi-agent-workflow/retail_workflow.py` (via `sys.path`).
2. Defines server-side `@tool` functions:
   - `search_products(query: str) -> list[dict]` — wraps Lab 2's `search_products`.
   - `get_warehouse_stock(sku: str, warehouse_code: str) -> int | str` — reads `data/zava_warehouses.json`.
   - `run_retail_workflow(customer_id: str, sku: str, quantity: int, preferred_warehouse: str) -> dict` — invokes Lab 4's workflow and returns the final output dict.
3. Builds a `GitHubCopilotAgent` named `retail_orchestrator` with those three tools.
4. Mounts on FastAPI at path `/retail` via `add_agent_framework_fastapi_endpoint(app, retail_orchestrator, "/retail", dependencies=[Depends(verify_api_key)])`.
5. `verify_api_key` reads `AG_UI_API_KEY` from environment; if unset, allows the request but logs a warning (dev-mode behavior from the `agent-framework-agui-py` skill).
6. Runs with `uvicorn.run(app, host="127.0.0.1", port=5100)` when `__main__`.

### Client (`client.py`)

7. Defines a client-side `@tool` `notify_local_user(message: str) -> str` that prints `[NOTIFY] {message}` and prepends a `\a` bell character. Returns `"OK"`.
8. Builds an `Agent(name="zava_ops", client=AGUIChatClient(endpoint=..., headers={"X-API-Key": ...}), tools=[notify_local_user])`.
9. Reads `AGUI_SERVER_URL` (default `http://127.0.0.1:5100/retail`) and `AG_UI_API_KEY` from env.
10. Maintains one `agent.create_session()` across an interactive loop (`while True: input(...)`).
11. Streams each response chunk to stdout.

### Verification (`verify.py`)

12. Starts `server.py` as a background subprocess; polls `http://127.0.0.1:5100/retail` until ready.
13. Sets `AG_UI_API_KEY = "test-key-do-not-use-in-prod"` for both server and client subprocesses.
14. Runs a single scripted client turn programmatically (not via the interactive loop):
    *"Please reserve 2 units of LIP-001 from the Seattle warehouse for customer CUST-501, and notify me locally once the reservation completes."*
15. Asserts the final response text:
    - Contains a tracking number matching `r"ZS-[0-9A-F]{8}"`.
    - References `LIP-001` and `WH-SEA`.
    - Contains the string `[NOTIFY]` (proves the client-side tool fired locally).
16. Tears down the server subprocess in `finally:`. Exit `0` only on full pass. Final line: `[OK] Lab 5 complete.`

## Run It

### Python

```bash
cd lab-05-agui
uv pip install -r requirements.txt
export AG_UI_API_KEY=anything-non-empty

# Terminal 1
python server.py

# Terminal 2
python client.py
```

Or just:

```bash
python verify.py
```

### C# / .NET

```bash
cd lab-05-agui/csharp
export AG_UI_API_KEY=anything-non-empty

# Terminal 1
dotnet run --project RetailServer

# Terminal 2
dotnet run --project RetailClient
```

Or just:

```bash
dotnet run --project Verify
```

## Common Mistakes

| Symptom | Cause |
| --- | --- |
| Client never sees `[NOTIFY]` | `notify_local_user` / `NotifyLocalUser.Notify` not registered on the client's `Agent` / `chatClient.AsAIAgent(tools: ...)`, or the server also registered it (must be client-only) |
| `401` from client | `X-API-Key` header not set on `AGUIChatClient` headers (Python) or `httpClient.DefaultRequestHeaders` (C#) |
| Server hangs on first request | Lab 4 workflow not importable / not referenceable — Python: fix `sys.path`. C#: add `ProjectReference` to `lab-04 Workflows.csproj` |
| Streaming stops mid-response | Default HTTP timeout — Python: pass `timeout=60.0` to `AGUIChatClient`. C#: set `httpClient.Timeout = TimeSpan.FromSeconds(60)` |
| `verify.py` / `Verify/Program.cs` leaves the server running | Forgot the `finally:` block (Python) / `finally { server.Kill(entireProcessTree: true); }` (C#) — kill any stragglers manually |
| C#: AG-UI endpoint not reachable | Forgot `app.MapAGUI(AgentName, "/retail")` or registered the agent name with a different case |
| C#: `AddAIAgent(...)` instance leaks state across calls | Forgot `.WithInMemorySessionStore()` so all clients share one session |

When Lab 5 is green, you've completed the ZavaShop Coding Agents Workshop.

## Reflection

After all five labs:

1. Compare the **prompt size** vs. the **PR diff size** for Labs 2–5. The MAF skills did a lot of heavy lifting.
2. Note which acceptance criteria the Coding Agent satisfied on the first PR vs. needed a revision comment. Those failure modes are what new skills should be written for.
3. Re-run the labs with **GPT-4o** or **Claude Sonnet 4** if available — does the same prompt produce a passing PR with a different model? That's an exercise in prompt portability.
