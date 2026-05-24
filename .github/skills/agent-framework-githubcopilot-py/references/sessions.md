# Session Management Reference

Patterns for managing conversation state and multi-turn interactions with `GitHubCopilotAgent`. Sessions are persisted server-side by the Copilot CLI; the SDK exposes them via lightweight `Session` objects.

## Overview

A `Session` links agent runs to a persistent server-side conversation, enabling:

- Multi-turn conversations that retain prior context.
- Saving and resuming a conversation across processes / agent instances.
- Multiple independent conversations from the same agent.

**Key rule:** `agent.run()` without a `session=` argument creates a brand-new session for that single call. To carry context across calls, you must pass the same `session` object.

---

## Creating and Using Sessions

### Basic Multi-Turn Conversation

```python
from agent_framework.github import GitHubCopilotAgent

agent = GitHubCopilotAgent(instructions="You are a helpful assistant.")

async with agent:
    session = agent.create_session()

    # Turn 1
    result1 = await agent.run("My name is Alice", session=session)
    print(f"Agent: {result1}")

    # Turn 2 — same session → agent still knows "Alice"
    result2 = await agent.run("What's my name?", session=session)
    print(f"Agent: {result2}")

    # Turn 3
    result3 = await agent.run("Tell me a joke about my name", session=session)
    print(f"Agent: {result3}")
```

### Accessing Session Information

```python
session = agent.create_session()
await agent.run("Hello!", session=session)

# Server-side session ID — save this to resume later
print(f"Session ID: {session.service_session_id}")
```

---

## Automatic vs Explicit Sessions

```python
# ❌ Each call creates a new session — no shared context
await agent.run("My favorite color is blue")
await agent.run("What's my favorite color?")  # Agent does not know

# ✅ Same session → context is retained
session = agent.create_session()
await agent.run("My favorite color is blue", session=session)
await agent.run("What's my favorite color?", session=session)  # Knows it's blue
```

---

## Conversation Persistence

### Saving the Session ID

```python
import json


async def save_session(session, filepath: str) -> None:
    """Persist the session ID so the conversation can be resumed later."""
    data = {"service_session_id": session.service_session_id}
    with open(filepath, "w") as f:
        json.dump(data, f)


# Usage
session = agent.create_session()
await agent.run("Start a conversation about Azure Functions.", session=session)
await save_session(session, "conversation.json")
```

### Resuming a Conversation

```python
import json

from agent_framework.github import GitHubCopilotAgent


async def resume_session(filepath: str) -> None:
    with open(filepath) as f:
        data = json.load(f)

    agent = GitHubCopilotAgent(instructions="You are a helpful assistant.")
    async with agent:
        session = agent.get_session(service_session_id=data["service_session_id"])

        result = await agent.run("Continue where we left off.", session=session)
        print(result)
```

This works across process boundaries — the second process can be a fresh `GitHubCopilotAgent` instance and still pick up the same server-side conversation.

---

## Sessions with Streaming

Streaming works identically; just pass the same `session` to every call.

```python
session = agent.create_session()

# Turn 1 — streaming
print("Agent: ", end="", flush=True)
async for chunk in agent.run("Tell me about Python", session=session, stream=True):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()

# Turn 2 — non-streaming, same session
result = await agent.run("What was that language again?", session=session)
print(f"Agent: {result}")

# Turn 3 — streaming again
print("Agent: ", end="", flush=True)
async for chunk in agent.run("Show me a code example", session=session, stream=True):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()
```

---

## Sessions with Tools

Function tools work seamlessly within a session.

```python
from typing import Annotated

from agent_framework import tool
from pydantic import Field


@tool(approval_mode="never_require")
def search_database(
    query: Annotated[str, Field(description="Search query")],
) -> str:
    """Search the product catalog."""
    return f"Results for '{query}': Item A, Item B, Item C"


@tool(approval_mode="never_require")
def get_item_details(
    item_name: Annotated[str, Field(description="Name of the item")],
) -> str:
    """Get details for a specific item."""
    return f"Details for {item_name}: Price $99, In Stock: Yes"


agent = GitHubCopilotAgent(
    instructions="Help users find and learn about products.",
    tools=[search_database, get_item_details],
)

async with agent:
    session = agent.create_session()

    await agent.run("Search for laptops", session=session)
    await agent.run("Tell me more about Item A", session=session)
    await agent.run("Is it available?", session=session)  # Knows we're talking about Item A
```

---

## Multiple Parallel Conversations

One agent can hold many concurrent sessions — one per user.

```python
import asyncio


async def handle_user(agent, user_id: str, messages: list[str]) -> None:
    session = agent.create_session()
    for msg in messages:
        result = await agent.run(msg, session=session)
        print(f"[{user_id}] User: {msg}")
        print(f"[{user_id}] Agent: {result}")


async def main() -> None:
    agent = GitHubCopilotAgent(instructions="You are a helpful assistant.")
    async with agent:
        await asyncio.gather(
            handle_user(agent, "user1", ["Hello", "What's 2+2?"]),
            handle_user(agent, "user2", ["Hi there", "Tell me a joke"]),
            handle_user(agent, "user3", ["Good morning", "Weather today?"]),
        )
```

---

## Session Best Practices

### Do's

```python
# ✅ Create one session per logical conversation
session = agent.create_session()

# ✅ Reuse the same session to keep context
await agent.run("Message 1", session=session)
await agent.run("Message 2", session=session)

# ✅ Save service_session_id for conversations that need resumption
session_id = session.service_session_id
```

### Don'ts

```python
# ❌ Creating a new session per message loses context
for msg in messages:
    session = agent.create_session()         # Wrong — fresh session each time
    await agent.run(msg, session=session)

# ❌ Sharing a session created by one agent instance with a different
#    instance without resuming via get_session()
session_a = agent_a.create_session()
await agent_b.run("Hi", session=session_a)   # Use agent_b.get_session(...) instead

# ❌ Omitting the session argument when you want continuity
await agent.run("Message 1")                  # No session — context not saved
await agent.run("Message 2")                  # Cannot reference Message 1
```

---

## Session Lifecycle

```
1. agent.create_session()
   └── Creates a Session object
   └── Server-side session is materialized on first agent.run(..., session=session)

2. agent.run(prompt, session=session)
   └── User turn appended to session
   └── Agent response appended to session
   └── Context accumulates

3. (Optional) Save session.service_session_id
   └── Persist for later resumption

4. (Optional) agent.get_session(service_session_id=...)
   └── Wraps the existing server-side session for use with a new agent instance
```

---

## Stateless vs Stateful Patterns

### Stateless (no session)

Each call is independent — good for one-shot queries:

```python
result = await agent.run("What is 2+2?")
```

### Stateful (with session)

Context persists — good for conversations:

```python
session = agent.create_session()
await agent.run("My favorite color is blue", session=session)
await agent.run("What's my favorite color?", session=session)  # Knows it's blue
```
