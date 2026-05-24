# Session Management Reference (.NET)

Patterns for managing conversation state and multi-turn interactions with `GitHubCopilotAgent`. Sessions are persisted server-side by the Copilot CLI; the SDK exposes them as `AgentSession` (concrete type: `GitHubCopilotAgentSession`).

## Overview

An `AgentSession` links agent runs to a persistent server-side conversation, enabling:

- Multi-turn conversations that retain prior context.
- Saving and resuming a conversation across processes or agent instances.
- Multiple independent conversations from the same agent.

**Key rule:** `agent.RunAsync(prompt)` without a `session` argument creates a brand-new session for that single call. To carry context across calls, you must pass the same `AgentSession` instance.

---

## Creating and Using Sessions

### Basic Multi-Turn Conversation

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful assistant.");

AgentSession session = await agent.CreateSessionAsync();

// Turn 1
AgentResponse r1 = await agent.RunAsync("My name is Alice", session);
Console.WriteLine($"Agent: {r1}");

// Turn 2 — same session → agent still knows "Alice"
AgentResponse r2 = await agent.RunAsync("What's my name?", session);
Console.WriteLine($"Agent: {r2}");

// Turn 3
AgentResponse r3 = await agent.RunAsync("Tell me a joke about my name", session);
Console.WriteLine($"Agent: {r3}");
```

### Accessing Session Information

```csharp
using Microsoft.Agents.AI.GitHub.Copilot;

AgentSession session = await agent.CreateSessionAsync();
await agent.RunAsync("Hello!", session);

// Server-side session ID — save this to resume later.
// It is populated after the first RunAsync turn.
string? sessionId = ((GitHubCopilotAgentSession)session).SessionId;
Console.WriteLine($"Session ID: {sessionId}");
```

---

## Automatic vs Explicit Sessions

```csharp
// ❌ Each call creates a new session — no shared context
await agent.RunAsync("My favorite color is blue");
await agent.RunAsync("What's my favorite color?");  // Agent does not know

// ✅ Same session → context is retained
AgentSession session = await agent.CreateSessionAsync();
await agent.RunAsync("My favorite color is blue", session);
await agent.RunAsync("What's my favorite color?", session);  // Knows it's blue
```

---

## Conversation Persistence

### Saving the Session ID

```csharp
using System.Text.Json;

static async Task SaveSessionAsync(AgentSession session, string filePath)
{
    string? id = ((GitHubCopilotAgentSession)session).SessionId;
    string json = JsonSerializer.Serialize(new { sessionId = id });
    await File.WriteAllTextAsync(filePath, json);
}

// Usage
AgentSession session = await agent.CreateSessionAsync();
await agent.RunAsync("Start a conversation about Azure Functions.", session);
await SaveSessionAsync(session, "conversation.json");
```

### Resuming a Conversation

Use the typed overload `GitHubCopilotAgent.CreateSessionAsync(string sessionId)` to bind a fresh `AgentSession` to an existing server-side conversation.

```csharp
using System.Text.Json;
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.GitHub.Copilot;

static async Task ResumeSessionAsync(string filePath)
{
    using JsonDocument doc = JsonDocument.Parse(await File.ReadAllTextAsync(filePath));
    string sessionId = doc.RootElement.GetProperty("sessionId").GetString()!;

    await using CopilotClient copilotClient = new();
    await copilotClient.StartAsync();

    AIAgent agent = copilotClient.AsAIAgent(
        ownsClient: true,
        instructions: "You are a helpful assistant.");

    // Cast to the concrete agent type to use the (string) overload of CreateSessionAsync.
    AgentSession session = await ((GitHubCopilotAgent)agent).CreateSessionAsync(sessionId);

    AgentResponse response = await agent.RunAsync("Continue where we left off.", session);
    Console.WriteLine(response);
}
```

This works across process boundaries — a second process can construct a fresh `GitHubCopilotAgent` and still pick up the same server-side conversation.

> You can also serialize/deserialize the full session state with `AgentSession.SerializeAsync` / `DeserializeAsync` on the agent — `GitHubCopilotAgentSession` is JSON-serializable.

---

## Sessions with Streaming

Streaming works identically; just pass the same session to every call.

```csharp
AgentSession session = await agent.CreateSessionAsync();

// Turn 1 — streaming
Console.Write("Agent: ");
await foreach (AgentResponseUpdate chunk in agent.RunStreamingAsync("Tell me about C#", session))
{
    Console.Write(chunk);
}
Console.WriteLine();

// Turn 2 — non-streaming, same session
AgentResponse r2 = await agent.RunAsync("What was that language again?", session);
Console.WriteLine($"Agent: {r2}");

// Turn 3 — streaming again
Console.Write("Agent: ");
await foreach (AgentResponseUpdate chunk in agent.RunStreamingAsync("Show me a code example", session))
{
    Console.Write(chunk);
}
Console.WriteLine();
```

---

## Sessions with Tools

Function tools work seamlessly within a session.

```csharp
using Microsoft.Extensions.AI;

string SearchDatabase(string query) =>
    $"Results for '{query}': Item A, Item B, Item C";

string GetItemDetails(string itemName) =>
    $"Details for {itemName}: Price $99, In Stock: Yes";

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "Help users find and learn about products.",
    tools:
    [
        AIFunctionFactory.Create(SearchDatabase),
        AIFunctionFactory.Create(GetItemDetails),
    ]);

AgentSession session = await agent.CreateSessionAsync();

await agent.RunAsync("Search for laptops", session);
await agent.RunAsync("Tell me more about Item A", session);
await agent.RunAsync("Is it available?", session);   // Knows we're talking about Item A
```

---

## Multiple Parallel Conversations

One agent can hold many concurrent sessions — one per user.

```csharp
static async Task HandleUserAsync(AIAgent agent, string userId, string[] messages)
{
    AgentSession session = await agent.CreateSessionAsync();
    foreach (string msg in messages)
    {
        AgentResponse response = await agent.RunAsync(msg, session);
        Console.WriteLine($"[{userId}] User: {msg}");
        Console.WriteLine($"[{userId}] Agent: {response}");
    }
}

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    instructions: "You are a helpful assistant.");

await Task.WhenAll(
    HandleUserAsync(agent, "user1", ["Hello", "What's 2+2?"]),
    HandleUserAsync(agent, "user2", ["Hi there", "Tell me a joke"]),
    HandleUserAsync(agent, "user3", ["Good morning", "Weather today?"]));
```

---

## Session Best Practices

### Do's

```csharp
// ✅ Create one session per logical conversation
AgentSession session = await agent.CreateSessionAsync();

// ✅ Reuse the same session to keep context
await agent.RunAsync("Message 1", session);
await agent.RunAsync("Message 2", session);

// ✅ Save SessionId for conversations that need resumption
string? sessionId = ((GitHubCopilotAgentSession)session).SessionId;
```

### Don'ts

```csharp
// ❌ Creating a new session per message loses context
foreach (string msg in messages)
{
    AgentSession s = await agent.CreateSessionAsync();   // Wrong — fresh session each time
    await agent.RunAsync(msg, s);
}

// ❌ Sharing a session created by one agent instance with a different
//    instance without resuming via CreateSessionAsync(sessionId)
AgentSession sessionA = await agentA.CreateSessionAsync();
await agentB.RunAsync("Hi", sessionA);   // Use ((GitHubCopilotAgent)agentB).CreateSessionAsync(id) instead

// ❌ Omitting the session argument when you want continuity
await agent.RunAsync("Message 1");        // No session — context not saved
await agent.RunAsync("Message 2");        // Cannot reference Message 1
```

---

## Session Lifecycle

```
1. agent.CreateSessionAsync()
   └── Returns a GitHubCopilotAgentSession (SessionId = null)
   └── Server-side session is materialized on first agent.RunAsync(..., session)

2. agent.RunAsync(prompt, session)
   └── User turn appended to server session
   └── Agent response appended
   └── session.SessionId is now populated; context accumulates

3. (Optional) Save GitHubCopilotAgentSession.SessionId
   └── Persist for later resumption

4. (Optional) ((GitHubCopilotAgent)agent).CreateSessionAsync(sessionId)
   └── Returns a new AgentSession wrapping the existing server-side conversation
```

---

## Stateless vs Stateful Patterns

### Stateless (no session)

Each call is independent — good for one-shot queries:

```csharp
AgentResponse response = await agent.RunAsync("What is 2+2?");
```

### Stateful (with session)

Context persists — good for conversations:

```csharp
AgentSession session = await agent.CreateSessionAsync();
await agent.RunAsync("My favorite color is blue", session);
await agent.RunAsync("What's my favorite color?", session);   // Knows it's blue
```
