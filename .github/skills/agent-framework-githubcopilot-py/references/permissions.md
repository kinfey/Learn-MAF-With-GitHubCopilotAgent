# Permissions Reference

`GitHubCopilotAgent` delegates to the local GitHub Copilot CLI. The CLI **denies built-in capabilities by default** and emits a `PermissionRequest` whenever the agent wants to use one. To allow capabilities, install an `on_permission_request` callback on `default_options` (or per-call via `options=`).

## Permission Kinds

`PermissionRequest.kind` is one of:

| Kind | Capability | Notable `PermissionRequest` fields |
|------|------------|-------------------------------------|
| `shell` | Execute a shell command on the host. | `full_command_text` |
| `read` | Read a file from the filesystem. | `path` |
| `write` | Create or modify a file. | `path` |
| `url` | Fetch content from a URL. | `url` |
| `mcp` | Invoke an MCP tool from a configured server. | `full_command_text` (when applicable) |

The result returned to the CLI must be one of:

- `PermissionRequestResult(kind="approved")` — allow this single action.
- `PermissionRequestResult(kind="denied-interactively-by-user")` — block this single action; the agent receives an error and can react.

---

## Interactive Prompt (All Kinds)

A single handler that prompts the user for each request. Useful for development.

```python
from agent_framework.github import GitHubCopilotAgent
from copilot.generated.session_events import PermissionRequest
from copilot.session import PermissionRequestResult


def prompt_permission(request: PermissionRequest, context: dict[str, str]) -> PermissionRequestResult:
    print(f"\n[Permission Request: {request.kind}]")
    if request.full_command_text is not None:
        print(f"  Command: {request.full_command_text}")
    if request.path is not None:
        print(f"  Path: {request.path}")
    if request.url is not None:
        print(f"  URL: {request.url}")

    response = input("Approve? (y/n): ").strip().lower()
    if response in ("y", "yes"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


agent = GitHubCopilotAgent(
    instructions="You are a helpful assistant.",
    default_options={"on_permission_request": prompt_permission},
)
```

---

## Shell Permission

Lets the agent run shell commands. Inspect `request.full_command_text` before approving.

```python
def approve_shell_listing_only(request, context):
    if request.kind != "shell":
        return PermissionRequestResult(kind="denied-interactively-by-user")
    cmd = (request.full_command_text or "").strip()
    # Allow only safe read-only commands.
    if cmd.startswith(("ls", "cat", "pwd", "echo")):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


agent = GitHubCopilotAgent(
    instructions="You can list files and inspect directories.",
    default_options={"on_permission_request": approve_shell_listing_only},
)

async with agent:
    result = await agent.run("List the first 3 Python files in the current directory")
    print(result)
```

> **Security:** shell commands run with the privileges of the current process. Never auto-approve `shell` unconditionally in untrusted environments.

---

## Read / Write File Permissions

Distinguish reads from writes. Optionally restrict by path prefix.

```python
from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()


def approve_project_files(request, context):
    if request.kind not in ("read", "write"):
        return PermissionRequestResult(kind="denied-interactively-by-user")
    if request.path is None:
        return PermissionRequestResult(kind="denied-interactively-by-user")
    target = Path(request.path).resolve()
    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError:
        # Path escapes the project root — deny.
        return PermissionRequestResult(kind="denied-interactively-by-user")
    return PermissionRequestResult(kind="approved")


agent = GitHubCopilotAgent(
    instructions="You can read and edit project files only.",
    default_options={"on_permission_request": approve_project_files},
)

async with agent:
    result = await agent.run("Read README.md and write a summary to SUMMARY.md")
    print(result)
```

---

## URL Permission

Allow the agent to fetch a web URL. Inspect `request.url` before approving.

```python
ALLOWED_HOSTS = {"learn.microsoft.com", "docs.python.org"}


def approve_known_hosts(request, context):
    if request.kind != "url" or request.url is None:
        return PermissionRequestResult(kind="denied-interactively-by-user")
    from urllib.parse import urlparse
    host = urlparse(request.url).hostname or ""
    if host in ALLOWED_HOSTS:
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


agent = GitHubCopilotAgent(
    instructions="Fetch and summarize web pages.",
    default_options={"on_permission_request": approve_known_hosts},
)

async with agent:
    result = await agent.run(
        "Fetch https://learn.microsoft.com/agent-framework/tutorials/quick-start and summarize it"
    )
    print(result)
```

---

## MCP Permission

When MCP servers are configured (see [mcp.md](mcp.md)), the CLI also surfaces `PermissionRequest(kind="mcp")` for tool invocations. Approve them like any other kind.

```python
def approve_shell_and_mcp(request, context):
    if request.kind in ("shell", "mcp"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")
```

---

## Combining Multiple Kinds

For workflows that need several capabilities, gate each kind explicitly. A single yes/no prompt that prints the kind and relevant field works well for interactive use:

```python
def prompt_permission(request, context):
    print(f"\n[Permission Request: {request.kind}]")
    if request.full_command_text is not None:
        print(f"  Command: {request.full_command_text}")
    if request.path is not None:
        print(f"  Path: {request.path}")
    if request.url is not None:
        print(f"  URL: {request.url}")
    response = input("Approve? (y/n): ").strip().lower()
    if response in ("y", "yes"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


agent = GitHubCopilotAgent(
    instructions=(
        "You are a development assistant that can read, write files, "
        "and run shell commands."
    ),
    default_options={"on_permission_request": prompt_permission},
)

async with agent:
    result = await agent.run(
        "List the first 3 Python files, read the first one, "
        "then write a summary to summary.txt"
    )
    print(result)
```

---

## Permission Best Practices

```python
# ✅ Approve only the kinds your workflow requires.
if request.kind == "read":
    return PermissionRequestResult(kind="approved")
return PermissionRequestResult(kind="denied-interactively-by-user")

# ✅ Inspect command_text / path / url before approving for sensitive kinds.
if request.kind == "shell" and (request.full_command_text or "").startswith("rm "):
    return PermissionRequestResult(kind="denied-interactively-by-user")

# ❌ Don't auto-approve everything in production.
return PermissionRequestResult(kind="approved")  # Avoid blanket approval
```
