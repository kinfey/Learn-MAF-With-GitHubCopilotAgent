# MCP Integration Reference (.NET)

Model Context Protocol (MCP) integration patterns for a GitHub Copilot–powered `AIAgent`. Two approaches are supported and may be combined:

| # | Approach | Where it comes from | When to use |
|---|----------|---------------------|-------------|
| A | **Programmatic** — `ModelContextProtocol.Client` + pass tools into `CopilotClient.AsAIAgent(tools: ...)` | Canonical MAF pattern from [`02-agents/ModelContextProtocol`](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/02-agents/ModelContextProtocol) | You own the MCP client lifecycle, want OAuth-protected servers, long-running task tools, custom logging, or shared `HttpClient`. |
| B | **Declarative** — `SessionConfig.McpServers` | GitHub Copilot SDK ([`AgentProviders/Agent_With_GitHubCopilot`](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/02-agents/AgentProviders/Agent_With_GitHubCopilot)) | The Copilot CLI manages the MCP servers and surfaces MCP permission prompts through `SessionConfig.OnPermissionRequest`. |

Approach A is what the MAF `ModelContextProtocol` samples show — default to it whenever the MCP behavior is non-trivial. The two GitHub Copilot SDK overloads of `AsAIAgent` accept tools the same way Azure OpenAI's `AsAIAgent` does:

```csharp
// GitHub.Copilot.SDK — overload with tools (CopilotClientExtensions.cs)
public static AIAgent AsAIAgent(
    this CopilotClient client,
    bool ownsClient = false,
    string? id = null,
    string? name = null,
    string? description = null,
    IList<AITool>? tools = null,
    string? instructions = null);
```

That `IList<AITool>` is exactly what `McpClient.ListToolsAsync()` produces — every `McpClientTool` derives from `Microsoft.Extensions.AI.AIFunction`, which itself derives from `AITool`. Cast as `AIFunction` (not `AITool`) when you need to mix MCP tools into a `SessionConfig.Tools` (`ICollection<AIFunction>`).

> ⚠️ **GitHub Copilot SDK gotcha — `OnPermissionRequest` is mandatory.** Even when every tool comes from an MCP client, the SDK's `CreateSessionAsync` throws `ArgumentException("An OnPermissionRequest handler is required when creating a session.")` if `SessionConfig.OnPermissionRequest` is null. The simple `AsAIAgent(ownsClient, instructions, tools)` overload still routes through `CreateSessionAsync` internally, so it throws too. **Prefer the `AsAIAgent(SessionConfig sessionConfig, ...)` overload** and set `OnPermissionRequest = PermissionHandler.ApproveAll` (or a stricter delegate) explicitly. The handler only ever sees the CLI-side kinds (`Shell` / `Read` / `Write` / `Url`) for Approach A — MCP tool calls go through the `McpClient` channel and never reach this delegate.

---

## Approach A — Programmatic MCP client (canonical)

The pattern below mirrors [`Agent_MCP_Server/Program.cs`](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/02-agents/ModelContextProtocol/Agent_MCP_Server) and swaps the Azure OpenAI client for `CopilotClient`.

### Packages

```bash
dotnet add package GitHub.Copilot.SDK --prerelease
dotnet add package Microsoft.Agents.AI.GitHub.Copilot --prerelease
dotnet add package ModelContextProtocol --prerelease
```

For long-running MCP tasks (Approach A.3 below) also add:

```bash
dotnet add package Microsoft.Agents.AI.Mcp --prerelease
```

### A.1 Stdio MCP server (local subprocess)

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using ModelContextProtocol.Client;

// 1) Connect to a stdio MCP server (here: the public GitHub MCP server, like the MAF sample).
await using McpClient mcpClient = await McpClient.CreateAsync(new StdioClientTransport(new()
{
    Name = "MCPServer",
    Command = "npx",
    Arguments = ["-y", "--verbose", "@modelcontextprotocol/server-github"],
}));

// 2) Discover tools advertised by the server (McpClientTool : AIFunction).
IList<McpClientTool> mcpTools = await mcpClient.ListToolsAsync();

// 3) Start the Copilot client.
await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

// 4) Build a SessionConfig — OnPermissionRequest is mandatory (see gotcha above).
SessionConfig sessionConfig = new()
{
    OnPermissionRequest = PermissionHandler.ApproveAll,
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You answer questions related to GitHub repositories only.",
    },
    Tools = [.. mcpTools.Cast<AIFunction>()],
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

Console.WriteLine(await agent.RunAsync(
    "Summarize the last four commits to the microsoft/agent-framework repository?"));
```

Notes
- The MCP client (`mcpClient`) and the Copilot client (`copilotClient`) have independent lifetimes — keep both alive while the agent runs.
- The MCP subprocess is spawned by `McpClient.CreateAsync`, not by the Copilot CLI. The CLI's `Mcp` permission kind does **not** intercept these tool calls; you control approval inside the tool layer. `OnPermissionRequest` only fires for `Shell` / `Read` / `Write` / `Url`.

### A.2 HTTP MCP server with OAuth (protected)

Adapted from [`Agent_MCP_Server_Auth/Program.cs`](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/02-agents/ModelContextProtocol/Agent_MCP_Server_Auth). The OAuth callback handler is identical to the MAF sample — only the agent construction changes.

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using ModelContextProtocol.Client;

using SocketsHttpHandler sharedHandler = new()
{
    PooledConnectionLifetime = TimeSpan.FromMinutes(2),
    PooledConnectionIdleTimeout = TimeSpan.FromMinutes(1),
};
using HttpClient httpClient = new(sharedHandler);
using ILoggerFactory loggerFactory = LoggerFactory.Create(b => b.AddConsole());

HttpClientTransport transport = new(
    new()
    {
        Endpoint = new Uri("http://localhost:7071/"),
        Name = "Secure Weather Client",
        OAuth = new()
        {
            DynamicClientRegistration = new() { ClientName = "ProtectedMcpClient" },
            RedirectUri = new Uri("http://localhost:1179/callback"),
            AuthorizationRedirectDelegate = HandleAuthorizationUrlAsync,
        },
    },
    httpClient,
    loggerFactory);

await using McpClient mcpClient = await McpClient.CreateAsync(transport, loggerFactory: loggerFactory);
IList<McpClientTool> mcpTools = await mcpClient.ListToolsAsync();

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

// Same SessionConfig pattern as A.1 — OnPermissionRequest is mandatory.
SessionConfig sessionConfig = new()
{
    OnPermissionRequest = PermissionHandler.ApproveAll,
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You answer questions related to the weather.",
    },
    Tools = [.. mcpTools.Cast<AIFunction>()],
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

Console.WriteLine(await agent.RunAsync("Get current weather alerts for New York?"));

// HandleAuthorizationUrlAsync(...) — copy the implementation verbatim from the MAF sample.
```

### A.3 Long-running MCP tasks (transparent polling)

When an MCP tool advertises `TaskSupport.Required` (SEP-2663), wrap the tool list with `McpClientTaskExtensions.ListAgentToolsWithTaskSupportAsync` from `Microsoft.Agents.AI.Mcp`. The wrapper polls `tasks/get` internally on every `RunAsync` / `RunStreamingAsync` invocation — no application-level polling loop is needed. See [`Agent_MCP_LongRunningTask_Client/Program.cs`](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/02-agents/ModelContextProtocol/Agent_MCP_LongRunningTask_Client).

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Mcp;
using Microsoft.Extensions.AI;
using ModelContextProtocol.Client;

string thisAssemblyPath = typeof(Program).Assembly.Location;

await using McpClient mcpClient = await McpClient.CreateAsync(new StdioClientTransport(new()
{
    Name = "DatasetAnalyzer",
    Command = "dotnet",
    Arguments = [thisAssemblyPath, "--server"],
}));

McpTaskOptions taskOptions = new() { DefaultTimeToLive = TimeSpan.FromMinutes(5) };
IList<AITool> mcpTools = await mcpClient.ListAgentToolsWithTaskSupportAsync(taskOptions);

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

// Long-running wrapper returns IList<AITool>; cast each element back to AIFunction for SessionConfig.Tools.
SessionConfig sessionConfig = new()
{
    OnPermissionRequest = PermissionHandler.ApproveAll,
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You answer data-analysis questions by invoking the available tools. "
                + "Always invoke a tool when one matches the request.",
    },
    Tools = [.. mcpTools.Cast<AIFunction>()],
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

AgentResponse response = await agent.RunAsync(
    "Analyze the dataset named 'sales-2025-q1' and summarize the findings.");
Console.WriteLine(response.Text);

// Streaming works exactly the same way — the wrapper still polls the task before the
// model's final answer begins to stream:
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(
    "Analyze the dataset named 'sales-2025-q1' and summarize the findings."))
{
    Console.Write(update);
}
```

### A.4 Combining MCP tools with C# function tools

`SessionConfig.Tools` is `ICollection<AIFunction>`. Mix `AIFunctionFactory.Create(...)` results with MCP tools freely — they share the same base type:

```csharp
using Microsoft.Extensions.AI;

string GetWeather(string location) =>
    $"The weather in {location} is sunny with a high of 25°C.";

SessionConfig sessionConfig = new()
{
    OnPermissionRequest = PermissionHandler.ApproveAll,
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You can use local helpers and the connected MCP server.",
    },
    Tools =
    [
        .. mcpTools.Cast<AIFunction>(),                  // McpClientTool : AIFunction
        AIFunctionFactory.Create(GetWeather),
    ],
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);
```

---

## Approach B — Declarative `SessionConfig.McpServers`

When you want the Copilot CLI itself to launch and manage the MCP servers, register them on `SessionConfig`. Every MCP tool invocation then also raises a `PermissionRequest` with `Kind = Mcp` that flows through `SessionConfig.OnPermissionRequest`. This path is unique to the GitHub Copilot SDK provider — there is no equivalent in the Azure OpenAI samples.

`SessionConfig.McpServers` is a `Dictionary<string, McpServerConfig>` (defined in `GitHub.Copilot.SDK`).

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

static Task<PermissionRequestResult> PromptPermission(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    Console.WriteLine($"\n[Permission Request: {request.Kind}]");
    Console.Write("Approve? (y/n): ");
    string? input = Console.ReadLine()?.Trim().ToUpperInvariant();
    return Task.FromResult(new PermissionRequestResult
    {
        Kind = input is "Y" or "YES"
            ? PermissionRequestResultKind.Approved
            : PermissionRequestResultKind.Rejected,
    });
}

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

SessionConfig sessionConfig = new()
{
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You can use the local filesystem and Microsoft Learn.",
    },
    OnPermissionRequest = PromptPermission,
    McpServers = new Dictionary<string, McpServerConfig>
    {
        ["filesystem"] = new()
        {
            Type = "stdio",
            Command = "npx",
            Args = ["-y", "@modelcontextprotocol/server-filesystem", "."],
            Tools = ["*"],
        },
        ["microsoft-learn"] = new()
        {
            Type = "http",
            Url = "https://learn.microsoft.com/api/mcp",
            Tools = ["*"],
        },
    },
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

Console.WriteLine(await agent.RunAsync("List files in the current directory"));
```

### Stdio fields

| Field | Description |
|-------|-------------|
| `Type` | `"stdio"` |
| `Command` | Executable to launch (`npx`, `uvx`, `python`, `dotnet`, ...) |
| `Args` | Argument list |
| `Tools` | Whitelist of tool names, or `["*"]` for all |
| `Env` | (Optional) environment variables for the subprocess |

### HTTP fields

| Field | Description |
|-------|-------------|
| `Type` | `"http"` |
| `Url` | MCP endpoint URL |
| `Tools` | Whitelist of tool names, or `["*"]` |
| `Headers` | (Optional) static headers, e.g. `["Authorization"] = "Bearer ..."` |

### Selective MCP permission handler

```csharp
static readonly string[] DangerousTokens = ["delete", "rm ", "drop"];

static Task<PermissionRequestResult> ApproveSafeMcp(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    if (request.Kind != PermissionRequestKind.Mcp)
    {
        return Task.FromResult(new PermissionRequestResult
        {
            Kind = PermissionRequestResultKind.Rejected,
        });
    }

    string cmd = request.FullCommandText ?? string.Empty;
    bool dangerous = DangerousTokens.Any(t => cmd.Contains(t, StringComparison.OrdinalIgnoreCase));

    return Task.FromResult(new PermissionRequestResult
    {
        Kind = dangerous
            ? PermissionRequestResultKind.Rejected
            : PermissionRequestResultKind.Approved,
    });
}
```

### Multiple declarative servers

```csharp
McpServers = new Dictionary<string, McpServerConfig>
{
    ["filesystem"] = new()
    {
        Type = "stdio",
        Command = "npx",
        Args = ["-y", "@modelcontextprotocol/server-filesystem", "."],
        Tools = ["read_file", "list_directory"],   // no writes
    },
    ["github"] = new()
    {
        Type = "http",
        Url = "https://api.githubcopilot.com/mcp",
        Headers = new Dictionary<string, string>
        {
            ["Authorization"] = $"Bearer {Environment.GetEnvironmentVariable("GITHUB_PAT")}",
        },
        Tools = ["*"],
    },
    ["microsoft-learn"] = new()
    {
        Type = "http",
        Url = "https://learn.microsoft.com/api/mcp",
        Tools = ["*"],
    },
},
```

> The exact property names (`Type`, `Command`, `Args`, `Url`, `Headers`, `Env`, `Tools`) are defined by the `McpServerConfig` shape in `GitHub.Copilot.SDK`. If your SDK version exposes them under slightly different casing or types, prefer the SDK's definition — the patterns above remain valid.

---

## Choosing between A and B

| You want… | Approach |
|-----------|----------|
| OAuth-protected MCP endpoint (dynamic client registration, redirect flow) | **A.2** |
| Long-running MCP tasks (SEP-2663) | **A.3** |
| Inject a custom `HttpClient` / `ILoggerFactory` into the MCP transport | **A** |
| The Copilot CLI to spawn and supervise the MCP subprocess | **B** |
| MCP tool calls to flow through `OnPermissionRequest` alongside `Shell` / `Read` / `Write` / `Url` | **B** |
| Mix MCP tools with `AIFunctionFactory.Create(...)` function tools | **either** (`tools: [..mcp, ..local]` for A; `SessionConfig.Tools` + `McpServers` for B) |

Both approaches can coexist on the same agent: pass an explicit `IList<AITool>` *and* configure `SessionConfig.McpServers`.

---

## Timeouts

Remote MCP calls often take longer than local ones. Increase the per-call budget with a `CancellationToken`, or raise the CLI default via `GITHUB_COPILOT_TIMEOUT`:

```csharp
using CancellationTokenSource cts = new(TimeSpan.FromSeconds(120));
AgentResponse response = await agent.RunAsync(
    "Search Microsoft Learn for 'Azure Functions Python' and summarize the top result",
    thread: null,
    options: null,
    cancellationToken: cts.Token);
```
