# MCP Integration Reference

Model Context Protocol (MCP) integration patterns for `GitHubCopilotAgent`. MCP servers are configured **declaratively** via the `mcp_servers` option — the Copilot CLI manages the connections. There is no `HostedMCPTool` / `MCPStreamableHTTPTool` import; everything goes through the CLI's MCP layer.

## Overview

| Transport | `type` value | Use case |
|-----------|--------------|----------|
| Local subprocess | `"stdio"` | npm/pip-installed MCP servers, local tools |
| Remote HTTP | `"http"` | Hosted MCP endpoints (e.g. Microsoft Learn) |

All MCP tool invocations also surface a `PermissionRequest(kind="mcp")`, so you must have an `on_permission_request` handler that approves the `"mcp"` kind (or approves selectively).

---

## Configuring MCP Servers

`mcp_servers` is a `dict[str, MCPServerConfig]` where keys are arbitrary server names.

```python
from agent_framework.github import GitHubCopilotAgent
from copilot.generated.session_events import PermissionRequest
from copilot.session import MCPServerConfig, PermissionRequestResult


def prompt_permission(request: PermissionRequest, context: dict[str, str]) -> PermissionRequestResult:
    print(f"\n[Permission Request: {request.kind}]")
    response = input("Approve? (y/n): ").strip().lower()
    if response in ("y", "yes"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


mcp_servers: dict[str, MCPServerConfig] = {
    "filesystem": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "tools": ["*"],
    },
    "microsoft-learn": {
        "type": "http",
        "url": "https://learn.microsoft.com/api/mcp",
        "tools": ["*"],
    },
}

agent = GitHubCopilotAgent(
    instructions="You can use the local filesystem and Microsoft Learn.",
    default_options={
        "on_permission_request": prompt_permission,
        "mcp_servers": mcp_servers,
    },
)

async with agent:
    # Exercises the local filesystem MCP server
    result1 = await agent.run("List files in the current directory")
    print(result1)

    # Remote MCP — give it more time
    result2 = await agent.run(
        "Search Microsoft Learn for 'Azure Functions Python' and summarize the top result",
        options={"timeout": 120},
    )
    print(result2)
```

---

## Stdio (Local) MCP Servers

Spawn a local process and communicate over stdin/stdout.

```python
"filesystem": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
    "tools": ["*"],
},
```

Fields:

| Field | Description |
|-------|-------------|
| `type` | Must be `"stdio"`. |
| `command` | Executable to launch (e.g. `npx`, `uvx`, `python`). |
| `args` | Argument list passed to the command. |
| `tools` | List of allowed tool names, or `["*"]` for all. |
| `env` | (Optional) Environment variables for the subprocess. |

### Example: Python MCP server

```python
"my-tools": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "env": {"MY_API_KEY": "..."},
    "tools": ["search", "lookup"],   # Allow only these tools
},
```

---

## HTTP (Remote) MCP Servers

Connect to a hosted MCP endpoint.

```python
"microsoft-learn": {
    "type": "http",
    "url": "https://learn.microsoft.com/api/mcp",
    "tools": ["*"],
},
```

Fields:

| Field | Description |
|-------|-------------|
| `type` | Must be `"http"`. |
| `url` | MCP endpoint URL. |
| `tools` | Allowed tools (`["*"]` or explicit list). |
| `headers` | (Optional) Static headers, e.g. `{"Authorization": "Bearer ..."}`. |

### Example: Authenticated HTTP MCP

```python
"private-mcp": {
    "type": "http",
    "url": "https://mcp.example.com/api/mcp",
    "headers": {
        "Authorization": "Bearer your-api-key",
        "X-Custom-Header": "custom-value",
    },
    "tools": ["*"],
},
```

> Remote MCP calls often take longer than local ones. Pass `options={"timeout": 120}` (or higher) on `agent.run()` if you see timeouts.

---

## Restricting Tools per Server

Use the `tools` field to whitelist exactly which MCP tools the agent may call.

```python
"filesystem": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
    "tools": ["read_file", "list_directory"],   # No writes / deletes
},
```

Pair this with a selective permission handler for defense in depth:

```python
def approve_safe_mcp(request, context):
    if request.kind != "mcp":
        return PermissionRequestResult(kind="denied-interactively-by-user")
    cmd = (request.full_command_text or "")
    if any(bad in cmd for bad in ("delete", "rm ", "drop")):
        return PermissionRequestResult(kind="denied-interactively-by-user")
    return PermissionRequestResult(kind="approved")
```

---

## Multiple MCP Servers

Add as many entries to `mcp_servers` as you need.

```python
mcp_servers: dict[str, MCPServerConfig] = {
    "filesystem": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "tools": ["*"],
    },
    "github": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp",
        "headers": {"Authorization": f"Bearer {os.environ['GITHUB_PAT']}"},
        "tools": ["*"],
    },
    "microsoft-learn": {
        "type": "http",
        "url": "https://learn.microsoft.com/api/mcp",
        "tools": ["*"],
    },
}
```

---

## Runtime Override

Replace `mcp_servers` for a single call without rebuilding the agent.

```python
async with agent:
    result = await agent.run(
        "Find docs for Azure Functions Python",
        options={
            "mcp_servers": {
                "microsoft-learn": {
                    "type": "http",
                    "url": "https://learn.microsoft.com/api/mcp",
                    "tools": ["*"],
                },
            },
        },
    )
```

---

## Combining MCP with Function Tools

MCP servers and `@tool` functions coexist on the same agent. The model picks whichever is appropriate.

```python
from typing import Annotated

from agent_framework import tool
from pydantic import Field


@tool(approval_mode="never_require")
def get_user_id() -> str:
    """Get the current user's ID."""
    return "user-123"


agent = GitHubCopilotAgent(
    instructions=(
        "You can call internal company APIs via MCP and look up the current user. "
        "Always verify identity before accessing sensitive data."
    ),
    tools=[get_user_id],
    default_options={
        "on_permission_request": prompt_permission,
        "mcp_servers": {
            "company-api": {
                "type": "http",
                "url": "https://internal-api.company.com/mcp",
                "headers": {"Authorization": f"Bearer {os.environ['COMPANY_TOKEN']}"},
                "tools": ["*"],
            },
        },
    },
)
```

---

## Error Handling for MCP

The CLI surfaces MCP failures back through `agent.run()`. Wrap calls in `try/except` when interacting with potentially unreliable remote servers, and prefer slightly larger timeouts.

```python
try:
    result = await agent.run(
        "Search Microsoft Learn for Container Apps",
        options={"timeout": 120},
    )
except TimeoutError as e:
    print(f"MCP call timed out: {e}")
except Exception as e:
    print(f"MCP error: {e}")
```

---

## Configuration Comparison

| Aspect | Stdio | HTTP |
|--------|-------|------|
| Where it runs | Local subprocess spawned by the CLI | Remote endpoint |
| Setup | `command` + `args` (+ optional `env`) | `url` (+ optional `headers`) |
| Auth | Via subprocess env vars | Via `headers` |
| Latency | Low | Network-bound — increase `timeout` |
| Best for | Trusted local tools, dev workflows | Hosted/shared services |
