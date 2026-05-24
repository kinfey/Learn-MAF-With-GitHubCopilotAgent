# Advanced Patterns Reference (.NET)

Advanced patterns for `GitHubCopilotAgent`: function-tool approval, skill directories, runtime overrides, streaming details, observability, and error handling.

## Function Tool Approval

For function tools that have side effects, gate the invocation inside the tool body itself or wrap it with a tiny approval delegate. Unlike `OnPermissionRequest` (which gates the CLI's built-in actions), function-tool approval lives in your code — you control when and how to prompt.

If the tool simply throws / returns an error when the user denies, the model receives the error and can apologize or try a different approach.

### Synchronous Approval

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

static bool PromptForApproval(string toolName, string args)
{
    Console.WriteLine($"\n[Function Approval Request]");
    Console.WriteLine($"  Tool: {toolName}");
    Console.WriteLine($"  Arguments: {args}");
    Console.Write("Approve this tool call? (y/n): ");
    return Console.ReadLine()?.Trim().ToUpperInvariant() is "Y" or "YES";
}

string GetWeatherDetail(string location)
{
    if (!PromptForApproval(nameof(GetWeatherDetail), $"location={location}"))
    {
        return "Tool call denied by the user.";
    }

    string[] conditions = ["sunny", "cloudy", "rainy", "stormy"];
    return $"The weather in {location} is {conditions[Random.Shared.Next(conditions.Length)]} "
         + $"with a high of {Random.Shared.Next(10, 31)}°C and humidity of 88%.";
}

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful weather assistant.",
    tools: [AIFunctionFactory.Create(GetWeatherDetail)]);

AgentResponse response = await agent.RunAsync("Give me the detailed weather for Seattle.");
Console.WriteLine(response);
```

### Asynchronous Approval

When the approval involves I/O (HTTP review service, UI queue, DB lookup), expose an async tool. `AIFunctionFactory.Create` accepts both `Func<T>` and `Func<T, Task<TResult>>` shapes.

```csharp
async Task<string> GetWeatherDetailAsync(string location)
{
    bool approved = await PromptForApprovalAsync(nameof(GetWeatherDetailAsync), $"location={location}");
    if (!approved)
    {
        return "Tool call denied by the user.";
    }

    // ...real work...
    return $"Weather in {location}: sunny, 25°C.";
}

static async Task<bool> PromptForApprovalAsync(string toolName, string args)
{
    Console.WriteLine($"\n[Function Approval - async]");
    Console.WriteLine($"  Tool: {toolName}");
    Console.WriteLine($"  Arguments: {args}");
    Console.Write("Approve this tool call? (y/n): ");
    string? input = await Task.Run(() => Console.ReadLine());
    return input?.Trim().ToUpperInvariant() is "Y" or "YES";
}

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful weather assistant.",
    tools: [AIFunctionFactory.Create(GetWeatherDetailAsync)]);
```

### Deny-by-Default

```csharp
// Tool always denies and surfaces a clear error to the model.
string GetWeatherDetailReadOnly(string location) =>
    "Tool call denied: this agent is not authorized to call GetWeatherDetail.";

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful weather assistant.",
    tools: [AIFunctionFactory.Create(GetWeatherDetailReadOnly)]);

AgentResponse response = await agent.RunAsync("Give me the detailed weather for Paris.");
Console.WriteLine(response);   // Agent will apologize / try a different approach
```

### When to Use Which Gate

| Gate | Gates | Receives | Returns |
|------|-------|----------|---------|
| `SessionConfig.OnPermissionRequest` | Built-in CLI actions: `Shell`, `Read`, `Write`, `Url`, `Mcp` | `PermissionRequest`, `PermissionInvocation` | `Task<PermissionRequestResult>` |
| Inside your `AIFunctionFactory.Create`-wrapped method | Each call to that specific function tool | Method arguments | A normal return value or an error string |

---

## Skill Directories

`SessionConfig.SkillDirectories` lets the CLI load project-specific or team-shared skill files alongside its built-in skills. Set the directories that contain your `.copilot` skill files.

### Default Skill Directories

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

string projectRoot = Directory.GetCurrentDirectory();
List<string> skillDirs =
[
    Path.Combine(projectRoot, ".copilot", "skills"),
    Path.Combine(projectRoot, "docs", "agent-guidelines"),
];

SessionConfig sessionConfig = new()
{
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You are a helpful coding assistant.",
    },
    OnPermissionRequest = PromptPermission,
    SkillDirectories = skillDirs,
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

AgentResponse response = await agent.RunAsync("Summarize the coding conventions I should follow.");
Console.WriteLine(response);
```

### Runtime Override

For per-call overrides, construct a new short-lived agent that wraps the *same* `CopilotClient` (don't dispose it!) but with a different `SessionConfig`:

```csharp
SessionConfig teamShared = new()
{
    SkillDirectories = ["/team/shared/skills"],
    OnPermissionRequest = PromptPermission,
};

SessionConfig projectSpecific = new()
{
    SkillDirectories = ["/project/specific/skills"],
    OnPermissionRequest = PromptPermission,
};

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent teamAgent = copilotClient.AsAIAgent(teamShared);          // ownsClient: false (default)
AIAgent projectAgent = copilotClient.AsAIAgent(projectSpecific);   // shares the same client

await teamAgent.RunAsync("What instructions are you following?");
await projectAgent.RunAsync("Now what instructions are you following?");
```

> Pass `ownsClient: true` to **only one** agent (the last one you want disposed with the client), or leave it `false` everywhere and dispose `copilotClient` yourself via `await using`.

---

## Runtime System Message Override

Set a per-agent `SessionConfig.SystemMessage` to control the instructions sent every turn. Modes:

- `SystemMessageMode.Replace` — replace any default instructions for this agent.
- `SystemMessageMode.Append` — append to the default instructions for this agent.

```csharp
SessionConfig terseConfig = new()
{
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Replace,
        Content = "Always respond in exactly 3 words.",
    },
    Tools = [AIFunctionFactory.Create(GetWeather)],
    OnPermissionRequest = PromptPermission,
};

SessionConfig expertConfig = new()
{
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Replace,
        Content = "You are a weather expert. Provide detailed weather information with temperature and recommendations.",
    },
    Tools = [AIFunctionFactory.Create(GetWeather)],
    OnPermissionRequest = PromptPermission,
};

AIAgent terse = copilotClient.AsAIAgent(terseConfig);
AIAgent expert = copilotClient.AsAIAgent(expertConfig);

// 3-word answer
Console.WriteLine(await terse.RunAsync("What's the weather in Paris?"));

// Detailed answer
Console.WriteLine(await expert.RunAsync("What's the weather in Paris?"));
```

---

## Streaming Responses

`agent.RunStreamingAsync(...)` returns an `IAsyncEnumerable<AgentResponseUpdate>`. Each update has text and metadata; `update.ToString()` (or just passing it to `Console.Write`) renders the streaming text.

```csharp
AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful weather agent.");

Console.Write("Agent: ");
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("What's the weather in Tokyo?"))
{
    Console.Write(update);
}
Console.WriteLine();
```

Streaming works the same way with a session for multi-turn conversations — just pass the same `AgentSession` to every call.

```csharp
AgentSession session = await agent.CreateSessionAsync();

await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("Tell me about Tokyo.", session))
{
    Console.Write(update);
}
```

You can also inspect the typed contents (`TextContent`, `UsageContent`, ...) on each update for things like token-usage metrics:

```csharp
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("Hello", session))
{
    foreach (AIContent content in update.Contents)
    {
        switch (content)
        {
            case TextContent text:
                Console.Write(text.Text);
                break;
            case UsageContent usage:
                Console.WriteLine($"\n[usage] in={usage.Details.InputTokenCount} out={usage.Details.OutputTokenCount}");
                break;
        }
    }
}
```

---

## Observability with OpenTelemetry

The Agent Framework emits `ActivitySource` traces around every agent invocation. Wire it to the OpenTelemetry .NET SDK and an exporter of your choice.

```csharp
using OpenTelemetry;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

using TracerProvider tracerProvider = Sdk.CreateTracerProviderBuilder()
    .SetResourceBuilder(ResourceBuilder.CreateDefault().AddService("copilot-agent-sample"))
    .AddSource("Microsoft.Agents.AI")
    .AddSource("Microsoft.Extensions.AI")
    .AddConsoleExporter()
    .Build();

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "Say hello.");

AgentResponse response = await agent.RunAsync("Hello!");
Console.WriteLine(response);
```

Add `AddOtlpExporter()` or `AddAzureMonitorTraceExporter()` (from `Azure.Monitor.OpenTelemetry.Exporter`) for production telemetry. Wire `Microsoft.Extensions.Logging` similarly via `AddOpenTelemetry(o => o.AddConsoleExporter())` on a `ILoggerFactory` to capture log events.

---

## Configuring Timeouts

Two layers:

```bash
# Default for every call — read by the underlying CLI
export GITHUB_COPILOT_TIMEOUT=60
```

```csharp
// Per-call override via a CancellationToken
using CancellationTokenSource cts = new(TimeSpan.FromSeconds(120));
AgentResponse response = await agent.RunAsync(
    "Search Microsoft Learn for Azure Functions Python and summarize",
    thread: null,
    options: null,
    cancellationToken: cts.Token);
```

Increase the timeout for remote MCP calls, long shell commands, or large file operations.

---

## Error Handling Patterns

### Graceful Degradation

```csharp
static async Task<string> RunWithFallbackAsync(
    CopilotClient copilotClient,
    AIAgent agent,
    string query,
    AgentSession? session = null)
{
    try
    {
        AgentResponse response = await agent.RunAsync(query, session);
        return response.ToString();
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Agent run failed: {ex.Message}");

        // Fall back to an agent with no built-in capabilities enabled (no permission handler).
        AIAgent fallback = copilotClient.AsAIAgent(
            instructions: "Answer based on your knowledge only — no tools.");
        AgentResponse response = await fallback.RunAsync(query);
        return $"[Fallback] {response}";
    }
}
```

### Retry with Exponential Backoff

```csharp
static async Task<AgentResponse> RunWithRetryAsync(
    AIAgent agent,
    string query,
    AgentSession? session = null,
    int maxRetries = 3)
{
    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        try
        {
            return await agent.RunAsync(query, session);
        }
        catch (Exception ex) when (attempt < maxRetries - 1)
        {
            int waitSeconds = (int)Math.Pow(2, attempt);
            Console.WriteLine($"Attempt {attempt + 1} failed, retrying in {waitSeconds}s: {ex.Message}");
            await Task.Delay(TimeSpan.FromSeconds(waitSeconds));
        }
    }

    // Last attempt: let exceptions propagate.
    return await agent.RunAsync(query, session);
}
```

---

## Performance: Reuse the Client and Agent

The `CopilotClient` owns a Copilot CLI subprocess. **Construct it once and reuse it** for multiple calls — don't spin up a new `CopilotClient` per request.

```csharp
// ✅ Good: one client + agent, many calls
await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();
AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "Answer questions concisely.");

foreach (string query in queries)
{
    AgentResponse response = await agent.RunAsync(query);
    Console.WriteLine(response);
}

// ❌ Bad: process churn on every call
foreach (string query in queries)
{
    await using CopilotClient c = new();
    await c.StartAsync();
    AIAgent a = c.AsAIAgent(ownsClient: true, instructions: "...");
    await a.RunAsync(query);
}
```

For independent conversations within the same agent, give each one its own session:

```csharp
static async Task<AgentResponse> HandleAsync(AIAgent agent, string query)
{
    AgentSession session = await agent.CreateSessionAsync();
    return await agent.RunAsync(query, session);
}

AgentResponse[] results = await Task.WhenAll(queries.Select(q => HandleAsync(agent, q)));
```

---

## Debugging

Increase CLI log verbosity via the environment:

```bash
export GITHUB_COPILOT_LOG_LEVEL=debug
```

Enable .NET logging for the framework via `Microsoft.Extensions.Logging`:

```csharp
using Microsoft.Extensions.Logging;

using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddConsole();
    builder.SetMinimumLevel(LogLevel.Debug);
});
```

Inspect streaming updates (text + tool events + usage):

```csharp
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("Hello"))
{
    Console.WriteLine($"[update] role={update.Role} contents={update.Contents.Count}");
    foreach (AIContent content in update.Contents)
    {
        Console.WriteLine($"  - {content.GetType().Name}");
    }
}
```
