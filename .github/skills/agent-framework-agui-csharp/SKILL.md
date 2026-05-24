---
name: agent-framework-agui-csharp
description: Build AG-UI protocol clients and servers with the Microsoft Agent Framework .NET SDK (Microsoft.Agents.AI.AGUI + Microsoft.Agents.AI.Hosting.AGUI.AspNetCore). Use when exposing an AIAgent over HTTP with server-sent events, building remote agent clients, supporting frontend tool rendering, agentic generative UI, predictive state updates, shared state, or human-in-the-loop UX. Covers AGUIChatClient, MapAGUI, AddAGUI, session storage, DelegatingAIAgent, and the AgentResponseUpdate streaming contract.
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
  package: Microsoft.Agents.AI.AGUI
---

# Agent Framework AG-UI (.NET)

Expose any `AIAgent` over the [AG-UI protocol](https://docs.ag-ui.com/) and consume it from a remote client over server-sent events. AG-UI standardizes the wire format for `messages → tool calls → text deltas → state updates → errors` so frontends, mobile apps, and CLI clients can interop with any compliant agent server.

This SDK ships two pieces:

- **`Microsoft.Agents.AI.Hosting.AGUI.AspNetCore`** — `app.MapAGUI(endpoint, agent)` extension that turns an `AIAgent` into an AG-UI server endpoint backed by SSE.
- **`Microsoft.Agents.AI.AGUI`** — `AGUIChatClient` that connects to an AG-UI endpoint and surfaces the stream as `AgentResponseUpdate`s through the normal `AIAgent` API.

## Architecture

```
┌──────────── AG-UI Client ─────────────┐         ┌──────────── AG-UI Server ─────────────┐
│                                        │         │                                        │
│  AGUIChatClient(httpClient, endpoint)  │  HTTP   │  builder.Services.AddAGUI()            │
│           ↓ .AsAIAgent(...)            │  POST   │  app.MapAGUI("/agentName", agent)      │
│  AIAgent  ──────────────────────────── │ ──────► │  AIAgent (ChatClientAgent /            │
│           agent.RunStreamingAsync(     │         │           DelegatingAIAgent / custom)  │
│             messages, session)         │  SSE    │           ↓                            │
│           ↓ async foreach              │ ◄────── │   AgentResponseUpdate stream:          │
│   AgentResponseUpdate                  │         │     TextContent / FunctionCallContent  │
│     .Contents                          │         │     FunctionResultContent /            │
│       TextContent                      │         │     DataContent / ErrorContent         │
│       FunctionCallContent (frontend)   │         │                                        │
│       FunctionResultContent            │         │  .WithInMemorySessionStore()           │
│       DataContent (state snapshot)     │         │  .WithSessionStore<TStore>()           │
│       ErrorContent                     │         │                                        │
│     .ConversationId  /  .ResponseId    │         │                                        │
└────────────────────────────────────────┘         └────────────────────────────────────────┘
```

Two highlights worth understanding before writing code:

- **Frontend tools.** Tools registered on the **client** (via `AIFunctionFactory.Create`) are exposed to the server's model as callable functions. The server emits `FunctionCallContent`; the client executes the .NET delegate locally and returns the result. This is how AG-UI does generative UI / browser-side actions.
- **Backend tools** registered on the **server** run server-side as usual. The server emits no client-side dispatch; the client just sees text deltas.

## Installation

```bash
# Server
dotnet add package Microsoft.Agents.AI.Hosting.AGUI.AspNetCore --prerelease
dotnet add package Microsoft.Agents.AI.OpenAI --prerelease
dotnet add package Azure.AI.OpenAI
dotnet add package Azure.Identity

# Client
dotnet add package Microsoft.Agents.AI --prerelease
dotnet add package Microsoft.Agents.AI.AGUI --prerelease
```

The server project's csproj uses `Microsoft.NET.Sdk.Web`:

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFrameworks>net10.0</TargetFrameworks>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
```

## Prerequisites

- **.NET 10 SDK** or later
- **Azure OpenAI** deployment (or any `IChatClient`-compatible model)
- `az login` (server uses `DefaultAzureCredential` by default)
- Network reachability from client to server (default: `http://localhost:5100`)

## Environment Variables

```bash
# Server
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-5.4-mini"

# Client
export AGUI_SERVER_URL="http://localhost:5100"
```

## Authentication & Lifecycle

> **🔑 Two rules apply to every code sample below:**
>
> 1. **Prefer `DefaultAzureCredential` / `AzureCliCredential`.** The server side authenticates to Azure OpenAI; the AGUI HTTP channel itself is plain HTTP/SSE (add your own auth middleware in production).
> 2. **Dispose `HttpClient` and `AGUIChatClient` consumers correctly.** `AGUIChatClient` takes ownership of the underlying transport via the `HttpClient` you supply; wrap it in `using` (or register it via `IHttpClientFactory`).

```csharp
using Azure.Identity;

// Server-side credential for Azure OpenAI
var credential = new DefaultAzureCredential();
// Production: prefer a specific identity to avoid latency from probing
// var credential = new ManagedIdentityCredential();
```

## Core Workflow

### Minimal Server (`MapAGUI`)

Mirrors [`AGUIServer/Program.cs`](https://github.com/microsoft/agent-framework/blob/main/dotnet/samples/05-end-to-end/AGUIClientServer/AGUIServer/Program.cs).

```csharp
using System.ComponentModel;
using AGUIServer;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI.Hosting;
using Microsoft.Agents.AI.Hosting.AGUI.AspNetCore;
using Microsoft.Extensions.AI;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient().AddLogging();
builder.Services.ConfigureHttpJsonOptions(options =>
    options.SerializerOptions.TypeInfoResolverChain.Add(AGUIServerSerializerContext.Default));

// ⬇ The single line that wires AG-UI into the DI container.
builder.Services.AddAGUI();

string endpoint = builder.Configuration["AZURE_OPENAI_ENDPOINT"]
    ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
string deploymentName = builder.Configuration["AZURE_OPENAI_DEPLOYMENT_NAME"]
    ?? throw new InvalidOperationException("AZURE_OPENAI_DEPLOYMENT_NAME is not set.");

const string AgentName = "AGUIAssistant";

var agent = new AzureOpenAIClient(new Uri(endpoint), new DefaultAzureCredential())
    .GetChatClient(deploymentName)
    .AsAIAgent(
        name: AgentName,
        tools: [
            AIFunctionFactory.Create(
                () => DateTimeOffset.UtcNow,
                name: "get_current_time",
                description: "Get the current UTC time."),
            AIFunctionFactory.Create(
                ([Description("The weather forecast request")] ServerWeatherForecastRequest request) =>
                    new ServerWeatherForecastResponse
                    {
                        Summary = "Sunny",
                        TemperatureC = 25,
                        Date = request.Date,
                    },
                name: "get_server_weather_forecast",
                description: "Gets the forecast for a specific location and date",
                AGUIServerSerializerContext.Default.Options),
        ]);

builder
    .AddAIAgent(AgentName, (_, _) => agent)
    .WithInMemorySessionStore();   // session storage (swap for persistent store in prod)

WebApplication app = builder.Build();
app.MapAGUI(AgentName, "/");
await app.RunAsync();
```

Run:

```bash
dotnet run --urls "http://localhost:5100"
```

### Minimal Client (`AGUIChatClient`)

Mirrors [`AGUIClient/Program.cs`](https://github.com/microsoft/agent-framework/blob/main/dotnet/samples/05-end-to-end/AGUIClientServer/AGUIClient/Program.cs).

```csharp
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.AGUI;
using Microsoft.Extensions.AI;

string serverUrl = Environment.GetEnvironmentVariable("AGUI_SERVER_URL") ?? "http://localhost:5100";

using HttpClient httpClient = new() { Timeout = TimeSpan.FromSeconds(60) };

var chatClient = new AGUIChatClient(
    httpClient,
    serverUrl,
    jsonSerializerOptions: AGUIClientSerializerContext.Default.Options);

AIAgent agent = chatClient.AsAIAgent(
    name: "agui-client",
    description: "AG-UI Client Agent",
    tools: []);                     // frontend tools go here

AgentSession session = await agent.CreateSessionAsync();
List<ChatMessage> messages = [new(ChatRole.System, "You are a helpful assistant.")];

while (true)
{
    Console.Write("\nUser (:q to exit): ");
    string? line = Console.ReadLine();
    if (string.IsNullOrWhiteSpace(line) || line is ":q" or "quit") { break; }

    messages.Add(new(ChatRole.User, line));

    await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(messages, session))
    {
        foreach (AIContent content in update.Contents)
        {
            switch (content)
            {
                case TextContent text:
                    Console.Write(text.Text);
                    break;
                case ErrorContent err:
                    Console.Error.WriteLine($"\n[Error] {err.Message}");
                    break;
            }
        }
    }
    messages.Clear();
}
```

### Frontend Tools (Tools Defined on the Client)

The client registers `AIFunction`s; the server's model sees them in the tool list and can call them. The .NET delegate executes **on the client** and the result is sent back.

```csharp
var changeBackground = AIFunctionFactory.Create(
    () =>
    {
        Console.ForegroundColor = ConsoleColor.DarkBlue;
        Console.WriteLine("Changing color to blue");
    },
    name: "change_background_color",
    description: "Change the console background color to dark blue.");

var readClientClimateSensors = AIFunctionFactory.Create(
    ([Description("The sensors measurements to include in the response")] SensorRequest request) =>
        new SensorResponse { Temperature = 22.5, Humidity = 45.0, AirQualityIndex = 75 },
    name: "read_client_climate_sensors",
    description: "Reads the climate sensor data from the client device.",
    serializerOptions: AGUIClientSerializerContext.Default.Options);

AIAgent agent = chatClient.AsAIAgent(
    name: "agui-client",
    tools: [changeBackground, readClientClimateSensors]);
```

Observe each tool round-trip in the stream:

```csharp
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(messages, session))
{
    foreach (AIContent content in update.Contents)
    {
        switch (content)
        {
            case TextContent text:
                Console.Write(text.Text);
                break;

            case FunctionCallContent call:
                Console.WriteLine($"\n[Function Call] {call.Name}({JsonSerializer.Serialize(call.Arguments)})");
                break;

            case FunctionResultContent result when result.Exception is not null:
                Console.WriteLine($"\n[Function Error] {result.Exception}");
                break;

            case FunctionResultContent result:
                Console.WriteLine($"\n[Function Result] {result.Result}");
                break;

            case ErrorContent err:
                string code = err.AdditionalProperties?["Code"] as string ?? "Unknown";
                Console.WriteLine($"\n[Error {code}] {err.Message}");
                break;
        }
    }
}
```

### Source-Generated Serializer Context (Required for AOT)

AG-UI uses `JsonSerializerContext` for trim-safe payload handling. Declare every type that crosses the wire.

```csharp
using System.Text.Json.Serialization;

[JsonSerializable(typeof(SensorRequest))]
[JsonSerializable(typeof(SensorResponse))]
internal sealed partial class AGUIClientSerializerContext : JsonSerializerContext;
```

On the server:

```csharp
[JsonSerializable(typeof(ServerWeatherForecastRequest))]
[JsonSerializable(typeof(ServerWeatherForecastResponse))]
internal sealed partial class AGUIServerSerializerContext : JsonSerializerContext;

builder.Services.ConfigureHttpJsonOptions(options =>
    options.SerializerOptions.TypeInfoResolverChain.Add(AGUIServerSerializerContext.Default));
```

Pass `xxxSerializerContext.Default.Options` to `AGUIChatClient(... jsonSerializerOptions: ...)` and to every `AIFunctionFactory.Create(... serializerOptions: ...)` for typed tool payloads.

### Multiple Endpoints on One Server

Mirror [`AGUIDojoServer/Program.cs`](https://github.com/microsoft/agent-framework/blob/main/dotnet/samples/05-end-to-end/AGUIClientServer/AGUIDojoServer/Program.cs) — register several agents on different paths from a single server:

```csharp
builder.Services.AddAGUI();

ChatClientAgentFactory.Initialize(app.Configuration);

app.MapAGUI("/agentic_chat",            ChatClientAgentFactory.CreateAgenticChat());
app.MapAGUI("/backend_tool_rendering",  ChatClientAgentFactory.CreateBackendToolRendering());
app.MapAGUI("/human_in_the_loop",       ChatClientAgentFactory.CreateHumanInTheLoop());
app.MapAGUI("/tool_based_generative_ui",ChatClientAgentFactory.CreateToolBasedGenerativeUI());

var jsonOptions = app.Services
    .GetRequiredService<IOptions<Microsoft.AspNetCore.Http.Json.JsonOptions>>();

app.MapAGUI("/agentic_generative_ui",   ChatClientAgentFactory.CreateAgenticUI(jsonOptions.Value.SerializerOptions));
app.MapAGUI("/shared_state",            ChatClientAgentFactory.CreateSharedState(jsonOptions.Value.SerializerOptions));
app.MapAGUI("/predictive_state_updates",ChatClientAgentFactory.CreatePredictiveStateUpdates(jsonOptions.Value.SerializerOptions));
```

### REST Test (`.http` File)

The server accepts a plain AG-UI POST. Use this for smoke tests before plugging in the client:

```http
@host = http://localhost:5100

### Send a message to the AG-UI agent
POST {{host}}/
Content-Type: application/json

{
  "threadId": "thread_123",
  "runId": "run_456",
  "messages": [
    { "role": "user", "content": "What is the capital of France?" }
  ],
  "context": {}
}
```

The response is an SSE stream — open it in the REST Client or `curl --no-buffer` to watch events arrive.

### Customizing Behavior with `DelegatingAIAgent`

Wrap an inner `AIAgent` to inject AG-UI-specific behavior — shared state, predictive state updates, structured snapshots, multi-turn orchestration. The Dojo server uses this pattern for every advanced scenario.

```csharp
internal sealed class SharedStateAgent(AIAgent innerAgent, JsonSerializerOptions options)
    : DelegatingAIAgent(innerAgent)
{
    protected override async IAsyncEnumerable<AgentResponseUpdate> RunCoreStreamingAsync(
        IEnumerable<ChatMessage> messages,
        AgentSession? session = null,
        AgentRunOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // 1. Read client-supplied state from ChatOptions.AdditionalProperties["ag_ui_state"]
        // 2. Inject the state into a system message for the inner agent
        // 3. Run the inner agent and capture structured output
        // 4. Emit a DataContent("application/json") snapshot to the client
        // 5. Optionally do a follow-up summarizing turn

        // ... full implementation in references/server.md
        await foreach (var u in InnerAgent.RunStreamingAsync(messages, session, options, cancellationToken))
        {
            yield return u;
        }
    }
}
```

See [references/server.md](references/server.md) for the full predictive-state-updates and shared-state patterns.

## Core Types Quick Reference

| Type | Namespace | Purpose |
|------|-----------|--------|
| `AGUIChatClient` | `Microsoft.Agents.AI.AGUI` | Client transport. Wraps an `HttpClient` and speaks AG-UI to a remote endpoint. |
| `AGUIChatClient.AsAIAgent(name, description, tools)` | `Microsoft.Agents.AI` | Promotes the chat client to an `AIAgent` with frontend tools. |
| `app.MapAGUI(name, agent)` / `app.MapAGUI(path, agent)` | `Microsoft.Agents.AI.Hosting.AGUI.AspNetCore` | Maps an `AIAgent` to an AG-UI HTTP endpoint. |
| `builder.Services.AddAGUI()` | `Microsoft.Agents.AI.Hosting.AGUI.AspNetCore` | Registers AG-UI services in DI. |
| `.AddAIAgent(name, factory).WithInMemorySessionStore()` | `Microsoft.Agents.AI.Hosting` | Registers the agent + in-memory session storage. |
| `AgentSession` / `agent.CreateSessionAsync()` | `Microsoft.Agents.AI` | Conversation handle that the AG-UI server uses as `threadId`. |
| `AgentResponseUpdate` | `Microsoft.Agents.AI` | Streaming update returned by `RunStreamingAsync`. |
| `update.AsChatResponseUpdate()` | `Microsoft.Agents.AI` | Cast to `ChatResponseUpdate` for `ConversationId`, `ResponseId`, etc. |
| `DelegatingAIAgent` | `Microsoft.Agents.AI` | Base class for wrapping an inner agent — override `RunCoreStreamingAsync`. |

## Streaming Content Types Quick Reference

| Content (in `update.Contents`) | When it appears | Notes |
|--------------------------------|----------------|-------|
| `TextContent` | Streaming text deltas from the model. | Concatenate to build the full message. |
| `FunctionCallContent` | Server-issued frontend tool call. | The client's tool executes locally; SDK auto-sends the result. |
| `FunctionResultContent` | Result of a tool call (frontend or backend). | Inspect `.Exception` for failures. |
| `DataContent` (`application/json`) | Structured state snapshot (shared state, predictive state updates). | Payload is JSON-serialized state. |
| `ErrorContent` | Server-reported error. | Read `.Message` and `.AdditionalProperties["Code"]`. |

## Complete Example

End-to-end pair that demonstrates streaming text + frontend tool + structured serializer context.

**Server**

```csharp
using System.ComponentModel;
using AGUIServer;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI.Hosting;
using Microsoft.Agents.AI.Hosting.AGUI.AspNetCore;
using Microsoft.Extensions.AI;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient().AddLogging();
builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.TypeInfoResolverChain.Add(AGUIServerSerializerContext.Default));
builder.Services.AddAGUI();

string endpoint = builder.Configuration["AZURE_OPENAI_ENDPOINT"]!;
string deployment = builder.Configuration["AZURE_OPENAI_DEPLOYMENT_NAME"]!;
const string AgentName = "AGUIAssistant";

var agent = new AzureOpenAIClient(new Uri(endpoint), new DefaultAzureCredential())
    .GetChatClient(deployment)
    .AsAIAgent(
        name: AgentName,
        tools: [
            AIFunctionFactory.Create(
                () => DateTimeOffset.UtcNow,
                name: "get_current_time",
                description: "Get the current UTC time."),
        ]);

builder.AddAIAgent(AgentName, (_, _) => agent).WithInMemorySessionStore();

WebApplication app = builder.Build();
app.MapAGUI(AgentName, "/");
await app.RunAsync();
```

**Client**

```csharp
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.AGUI;
using Microsoft.Extensions.AI;

string url = Environment.GetEnvironmentVariable("AGUI_SERVER_URL") ?? "http://localhost:5100";
using HttpClient http = new() { Timeout = TimeSpan.FromSeconds(60) };

var chatClient = new AGUIChatClient(http, url, jsonSerializerOptions: null);

var changeBackground = AIFunctionFactory.Create(
    () => Console.WriteLine("[client] changing background"),
    name: "change_background_color",
    description: "Change the console background color.");

AIAgent agent = chatClient.AsAIAgent(
    name: "agui-client",
    description: "AG-UI Client Agent",
    tools: [changeBackground]);

AgentSession session = await agent.CreateSessionAsync();
List<ChatMessage> messages = [new(ChatRole.System, "You are helpful.")];

while (true)
{
    Console.Write("\n> ");
    string? line = Console.ReadLine();
    if (string.IsNullOrWhiteSpace(line) || line is ":q") { break; }
    messages.Add(new(ChatRole.User, line));

    string? threadId = null, runId = null;
    bool isFirst = true;

    await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(messages, session))
    {
        ChatResponseUpdate chat = update.AsChatResponseUpdate();
        threadId ??= chat.ConversationId;
        runId = update.ResponseId;

        if (isFirst && threadId is not null && runId is not null)
        {
            Console.WriteLine($"[Run Started - Thread: {threadId}, Run: {runId}]");
            isFirst = false;
        }

        foreach (AIContent c in update.Contents)
        {
            switch (c)
            {
                case TextContent t:                Console.Write(t.Text); break;
                case FunctionCallContent fc:       Console.WriteLine($"\n[Call] {fc.Name}"); break;
                case FunctionResultContent fr:     Console.WriteLine($"\n[Result] {fr.Result}"); break;
                case ErrorContent err:             Console.Error.WriteLine($"\n[Error] {err.Message}"); break;
            }
        }
    }
    Console.WriteLine($"\n[Run Finished - Thread: {threadId}, Run: {runId}]");
    messages.Clear();
}
```

## Conventions

- **One agent per route.** `MapAGUI(path, agent)` binds one `AIAgent` to one route. For multiple personas / scenarios, register multiple endpoints on the same server (the Dojo sample).
- **Always register a session store.** Without `.WithInMemorySessionStore()` (or a persistent equivalent), the AG-UI server has no conversation context to associate with `threadId`.
- **Source-generate serializer contexts.** Every type that crosses the wire — tool arguments, tool results, state snapshots — must be reachable from a `[JsonSerializable]` partial context, and that context must be added to `ConfigureHttpJsonOptions` on the server and to `AGUIChatClient`/`AIFunctionFactory.Create` on the client.
- **Use `update.AsChatResponseUpdate()`** to access `ConversationId` and `ResponseId`. The raw `AgentResponseUpdate` only exposes `ResponseId` directly.
- **Frontend tools come from the client constructor**, backend tools come from the server `AsAIAgent(... tools: ...)` call. Don't duplicate the same tool on both sides.
- **`DelegatingAIAgent` for AG-UI customization.** When you need to inject state, emit structured snapshots, or rewrite messages, derive from `DelegatingAIAgent` and override `RunCoreStreamingAsync`. Don't try to hook the AG-UI middleware itself.

## Best Practices

1. **Production session storage.** `WithInMemorySessionStore()` loses everything on restart. Implement a session store backed by Redis, Cosmos DB, or your existing chat history store, and call `.WithSessionStore<TStore>()`.
2. **Auth at the HTTP layer.** AG-UI is plain HTTP/SSE — add ASP.NET Core auth middleware (`AddAuthentication` + `RequireAuthorization()`) in front of `MapAGUI`. Don't rely on the protocol for security.
3. **Bound client timeouts.** AG-UI runs can stream for a long time. Set `HttpClient.Timeout` generously (e.g. 60 s+) and pass `CancellationToken` through `RunStreamingAsync(..., cancellationToken)` so users can abort.
4. **Surface frontend tool errors.** Wrap your `AIFunctionFactory.Create` delegate body in try/catch and return a structured error object — otherwise the model receives an opaque exception string and can't recover.
5. **Don't block on `DataContent` snapshots.** State snapshots can arrive interleaved with text. Render them incrementally — patch your UI on every snapshot rather than waiting for the run to end.
6. **Production credential.** Replace `DefaultAzureCredential` with a specific credential (e.g. `ManagedIdentityCredential`) in deployed environments to avoid credential-chain probing latency and accidental fallbacks.
7. **HTTP logging in dev only.** The Dojo server enables full request/response body logging (`HttpLoggingFields.RequestBody | ResponseBody`). Keep that on `Development` profile only — SSE bodies are large.

## Reference Files

- [references/server.md](references/server.md): `MapAGUI`, `AddAGUI`, session storage, multiple endpoints, `DelegatingAIAgent` patterns (shared state, predictive state updates, agentic UI).
- [references/client.md](references/client.md): `AGUIChatClient`, `AsAIAgent`, frontend tools, `AgentResponseUpdate` content switching, session management, error handling.
- [references/protocol.md](references/protocol.md): AG-UI request shape, SSE event stream, `threadId` / `runId` semantics, content type reference.
- [references/advanced.md](references/advanced.md): Production hardening — auth, persistent session stores, AOT/source-generated serializer contexts, observability, structured state snapshots, multi-tenancy.
