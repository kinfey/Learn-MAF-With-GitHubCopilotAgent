---
name: agent-framework-githubcopilot-csharp
description: Build local GitHub Copilot–backed agents using the Microsoft Agent Framework for .NET (Microsoft.Agents.AI.GitHub.Copilot). Use when creating agents with CopilotClient + AsAIAgent that delegate to the GitHub Copilot CLI, configuring permission handlers (shell, read, write, url, mcp), managing Copilot sessions for multi-turn conversations, registering local/HTTP MCP servers, applying skill directories, enforcing function-tool approval, and streaming responses. Covers function tools (AIFunctionFactory), runtime SessionConfig overrides, and multi-permission workflows.
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
  package: Microsoft.Agents.AI.GitHub.Copilot
---

# Agent Framework GitHub Copilot Agents (.NET)

Build local agents backed by the GitHub Copilot CLI using the Microsoft Agent Framework for .NET. The `CopilotClient` (from `GitHub.Copilot.SDK`) spawns and talks to the `copilot` CLI on the user's machine — there is no Azure endpoint and no cloud credential to configure. Permissions, sessions, MCP servers, and skills are managed by the CLI; this SDK gives you an idiomatic, async-first `AIAgent` on top.

## Architecture

```
User Query →
  AIAgent (Microsoft.Agents.AI) ← CopilotClient.AsAIAgent(sessionConfig)
                              ↓
                GitHub Copilot CLI (local process)
                              ↓
      agent.RunAsync() / agent.RunStreamingAsync()
                              ↓
   Tools: AIFunction tools | Built-in actions (shell/read/write/url) | MCP servers
                              ↓
              Permission handler (SessionConfig.OnPermissionRequest)
                              ↓
                 AgentSession (multi-turn conversation persistence)
```

## Installation

Add the NuGet packages to your `.csproj`:

```xml
<ItemGroup>
  <PackageReference Include="GitHub.Copilot.SDK" />
  <PackageReference Include="Microsoft.Agents.AI.GitHub.Copilot" />
</ItemGroup>
```

Or via CLI:

```bash
dotnet add package GitHub.Copilot.SDK
dotnet add package Microsoft.Agents.AI.GitHub.Copilot
```

> The Agent Framework `GitHub.Copilot` package is currently shipped as part of the `microsoft/agent-framework` repo and depends on the `GitHub.Copilot.SDK` (1.0.0-beta.x). Until both are on NuGet, reference the project directly from the cloned repo.

## Prerequisites

1. **.NET 10 SDK** or later.
2. **GitHub Copilot CLI** — install and authenticate (`copilot auth`). Ensure `copilot` is on `PATH`, or set a custom path via `CopilotClientOptions`.
3. **Active GitHub Copilot subscription** — required for the CLI to call models.

> ⚠️ **Container recommendation.** GitHub Copilot can execute shell and file tools that touch your host. Run the sample inside Docker / Dev Container in any non-trusted scenario.

## Environment Variables

All are optional and read by the underlying CLI. Configure them when you need to override defaults:

```bash
export GITHUB_COPILOT_CLI_PATH="copilot"        # Path to the Copilot CLI executable
export GITHUB_COPILOT_MODEL="gpt-5"              # e.g. "gpt-5", "claude-sonnet-4.5"; server default otherwise
export GITHUB_COPILOT_TIMEOUT="60"               # Request timeout in seconds
export GITHUB_COPILOT_LOG_LEVEL="info"           # CLI log level
export GITHUB_COPILOT_COPILOT_HOME="~/.copilot"  # Directory for CLI session state and config
```

Most settings can also be set programmatically on `SessionConfig` (`WorkingDirectory`, `ConfigDir`, `Model`, ...).

## Lifecycle & Permissions

> **🔑 Two rules apply to every code sample below:**
>
> 1. **Always wrap the client in `await using`.** `CopilotClient` owns a child Copilot CLI process; the async disposable pattern guarantees it is started, drained, and terminated cleanly. When `ownsClient: true` is passed to `AsAIAgent`, the agent will dispose the client for you.
> 2. **Permissions are deny-by-default.** Built-in capabilities (shell, read, write, url, mcp) are gated by the CLI. To allow them, set `SessionConfig.OnPermissionRequest` to a handler that returns an `Approved` or `Rejected` result. Function tools you author can do their own per-call approval inside the delegate body.

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

// Permission handler that prompts the user for approval per request.
static Task<PermissionRequestResult> PromptPermission(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    Console.WriteLine($"\n[Permission: {request.Kind}]");
    Console.Write("Approve? (y/n): ");

    string? input = Console.ReadLine()?.Trim().ToUpperInvariant();
    PermissionRequestResultKind kind = input is "Y" or "YES"
        ? PermissionRequestResultKind.Approved
        : PermissionRequestResultKind.Rejected;

    return Task.FromResult(new PermissionRequestResult { Kind = kind });
}
```

`PermissionRequest.Kind` covers the built-in CLI capability kinds (`shell`, `read`, `write`, `url`, `mcp`). The same handler can gate any subset — inspect `request.Kind` (and the request payload's command / path / url where available) and approve selectively. **Only enable the permissions you actually need.**

## Core Workflow

### Basic Agent

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    name: "MyAgent",
    instructions: "You are a helpful assistant.");

AgentResponse response = await agent.RunAsync("Hello!");
Console.WriteLine(response);
```

### Agent with Function Tools

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

string GetWeather(string location)
{
    string[] conditions = ["sunny", "cloudy", "rainy", "stormy"];
    int i = Random.Shared.Next(conditions.Length);
    return $"The weather in {location} is {conditions[i]} with a high of {Random.Shared.Next(10, 31)}°C.";
}

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    name: "WeatherAgent",
    instructions: "You are a helpful weather agent.",
    tools: [AIFunctionFactory.Create(GetWeather)]);

AgentResponse response = await agent.RunAsync("What's the weather in Seattle?");
Console.WriteLine(response);
```

### Enabling Built-In Capabilities (Shell / Read / Write / URL)

Built-in actions are unlocked simply by attaching a permission handler on `SessionConfig`. The agent decides when to call them.

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

static Task<PermissionRequestResult> ApproveReadsOnly(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    PermissionRequestResultKind kind =
        request.Kind == PermissionRequestKind.Read
            ? PermissionRequestResultKind.Approved
            : PermissionRequestResultKind.Rejected;

    return Task.FromResult(new PermissionRequestResult { Kind = kind });
}

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

SessionConfig sessionConfig = new()
{
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You can read project files to answer questions.",
    },
    OnPermissionRequest = ApproveReadsOnly,
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

AgentResponse response = await agent.RunAsync("Read README.md and summarize it.");
Console.WriteLine(response);
```

### Streaming Responses

```csharp
await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful assistant.");

Console.Write("Agent: ");
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("Tell me a short story"))
{
    Console.Write(update);
}
Console.WriteLine();
```

### Multi-Turn Conversations with Sessions

```csharp
await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful weather agent.");

// Create a fresh session; the first RunAsync turn binds it to a CLI session id.
AgentSession session = await agent.CreateSessionAsync();

AgentResponse first = await agent.RunAsync("What's the weather in Tokyo?", session);
Console.WriteLine(first);

// Same session → context is preserved
AgentResponse second = await agent.RunAsync("How about London?", session);
Console.WriteLine(second);

// Persist the session id (after the first run) to resume later.
string? savedId = ((GitHubCopilotAgentSession)session).SessionId;
```

To resume an existing conversation by id:

```csharp
AgentSession resumed = await ((GitHubCopilotAgent)agent).CreateSessionAsync(savedId!);
await agent.RunAsync("Continue where we left off.", resumed);
```

### MCP Servers (Local + Remote)

```csharp
using GitHub.Copilot.SDK;

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
```

> The exact property names on `McpServerConfig` are defined in `GitHub.Copilot.SDK`. See [references/mcp.md](references/mcp.md) for the field-by-field reference.

## Agent Methods

| Method | Description |
|--------|-------------|
| `agent.RunAsync(prompt, session?, options?)` | Run a single turn; returns an `AgentResponse`. |
| `agent.RunStreamingAsync(prompt, session?, options?)` | Returns an `IAsyncEnumerable<AgentResponseUpdate>` that streams chunks. |
| `agent.CreateSessionAsync()` | Create a fresh Copilot-backed `AgentSession` for multi-turn context. |
| `((GitHubCopilotAgent)agent).CreateSessionAsync(sessionId)` | Resume an existing CLI session by its server-side ID. |
| `await using` on `CopilotClient` / `agent` | Required — manages the underlying CLI subprocess lifecycle. |

## SessionConfig Quick Reference

Set on `new SessionConfig { ... }` and pass into `AsAIAgent(sessionConfig, ...)`. Any field can be varied per call by handing a different `SessionConfig`-derived option through `AgentRunOptions` (see [references/advanced.md](references/advanced.md)).

| Property | Purpose |
|----------|---------|
| `Model` | Underlying model name (e.g. `"gpt-5"`, `"claude-opus-4.5"`). |
| `ReasoningEffort` | Reasoning budget hint for reasoning-capable models. |
| `SystemMessage` | `SystemMessageConfig { Mode = Replace \| Append, Content = "..." }`. |
| `Tools` / `AvailableTools` / `ExcludedTools` | Function tools + CLI tool gating. |
| `OnPermissionRequest` | Callback that approves/denies CLI permission prompts (`Shell`, `Read`, `Write`, `Url`, `Mcp`). |
| `OnUserInputRequest` | Callback for interactive input requests. |
| `Hooks` | Lifecycle hooks for the CLI session. |
| `WorkingDirectory` | Working directory the CLI is invoked from. |
| `ConfigDir` | Override for the Copilot config / state directory. |
| `McpServers` | Map of MCP server configs (`stdio` or `http`). |
| `CustomAgents` | Custom CLI agents to register for this session. |
| `SkillDirectories` | Directories of custom skill files the CLI loads. |
| `DisabledSkills` | Skill names to disable for this session. |
| `InfiniteSessions` | Whether to keep the session alive across idle events. |
| `Provider` | Underlying model provider override. |
| `Streaming` | Set automatically — leave as default. |

## Complete Example

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.GitHub.Copilot;
using Microsoft.Extensions.AI;

string GetWeather(string location)
{
    string[] conditions = ["sunny", "cloudy", "rainy", "stormy"];
    int i = Random.Shared.Next(conditions.Length);
    return $"Weather in {location}: {conditions[i]}, {Random.Shared.Next(10, 31)}°C.";
}

static Task<PermissionRequestResult> PromptPermission(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    Console.WriteLine($"\n[Permission: {request.Kind}]");
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
    Model = "gpt-5",
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You are a research assistant with multiple capabilities.",
    },
    Tools = [AIFunctionFactory.Create(GetWeather)],
    OnPermissionRequest = PromptPermission,
    McpServers = new Dictionary<string, McpServerConfig>
    {
        ["microsoft-learn"] = new()
        {
            Type = "http",
            Url = "https://learn.microsoft.com/api/mcp",
            Tools = ["*"],
        },
    },
};

AIAgent agent = copilotClient.AsAIAgent(
    sessionConfig,
    ownsClient: true,
    name: "ResearchAssistant",
    description: "Research assistant powered by GitHub Copilot.");

AgentSession session = await agent.CreateSessionAsync();

// Non-streaming
AgentResponse result = await agent.RunAsync(
    "Look up Azure Functions Python on Microsoft Learn and summarize.",
    session);
Console.WriteLine($"Response: {result}");

// Streaming with the same session
Console.Write("\nStreaming: ");
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(
    "Now compare it to Container Apps.", session))
{
    Console.Write(update);
}
Console.WriteLine();
```

## Conventions

- Always use `await using` on the `CopilotClient` (and pass `ownsClient: true` when handing it to the agent) — the CLI subprocess must be cleaned up.
- Build function tools with `AIFunctionFactory.Create(...)` from `Microsoft.Extensions.AI` and pass them via the `tools:` parameter of `AsAIAgent(...)` or `SessionConfig.Tools`.
- Use XML doc comments and `[Description]` attributes on tool method parameters to give the model parameter intent.
- Create one `AgentSession` per logical conversation; persist `GitHubCopilotAgentSession.SessionId` to resume later via `agent.CreateSessionAsync(sessionId)`.
- Approve only the `PermissionRequest.Kind` values your workload requires; deny everything else.
- Configure MCP servers via `SessionConfig.McpServers`; do **not** import other framework MCP types (e.g. `HostedMCPTool`) — those belong to other providers.

## Best Practices

1. **Async-first.** All handlers, callbacks, and `agent.RunAsync` / `RunStreamingAsync` calls are awaitable. `OnPermissionRequest` returns a `Task<PermissionRequestResult>`.
2. **Least privilege.** Each `PermissionRequest.Kind` you approve grants the agent real access to the host. Approve narrowly (per-kind, or per-call by inspecting the request payload before returning `Approved`).
3. **Persist sessions explicitly.** Capture `GitHubCopilotAgentSession.SessionId` after the first run to resume the same conversation later — sessions are not implicitly re-used across `RunAsync` calls unless you pass the same `AgentSession` instance.
4. **Override at runtime, not on the class.** Pass a per-call `AgentRunOptions` (or a fresh `SessionConfig` to a new short-lived agent) to vary `SystemMessage`, `SkillDirectories`, `McpServers`, or `Model` for one call instead of constructing a new long-lived agent.
5. **Enable observability when debugging.** Wire `Microsoft.Extensions.Logging` + an OpenTelemetry exporter around `agent.RunAsync`/`RunStreamingAsync` to trace every CLI round-trip. See [references/advanced.md](references/advanced.md).

## Reference Files

- [references/permissions.md](references/permissions.md): Permission handler patterns for shell, read, write, url, and mcp.
- [references/sessions.md](references/sessions.md): Session creation, persistence, and resumption.
- [references/mcp.md](references/mcp.md): MCP server configuration (stdio + HTTP) for the Copilot CLI.
- [references/advanced.md](references/advanced.md): Function approval, skill directories, runtime overrides, streaming details, and observability.
