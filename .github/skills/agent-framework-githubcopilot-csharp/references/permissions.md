# Permissions Reference (.NET)

`GitHubCopilotAgent` delegates to the local GitHub Copilot CLI. The CLI **denies built-in capabilities by default** and emits a `PermissionRequest` whenever the agent wants to use one. To allow capabilities, set `SessionConfig.OnPermissionRequest` to a `Func<PermissionRequest, PermissionInvocation, Task<PermissionRequestResult>>`.

## Permission Kinds

`PermissionRequest.Kind` is one of:

| Kind | Capability | Notable `PermissionRequest` fields |
|------|------------|-------------------------------------|
| `Shell` | Execute a shell command on the host. | `FullCommandText` |
| `Read` | Read a file from the filesystem. | `Path` |
| `Write` | Create or modify a file. | `Path` |
| `Url` | Fetch content from a URL. | `Url` |
| `Mcp` | Invoke an MCP tool from a configured server. | `FullCommandText` (when applicable) |

The result returned to the CLI must be one of:

- `new PermissionRequestResult { Kind = PermissionRequestResultKind.Approved }` — allow this single action.
- `new PermissionRequestResult { Kind = PermissionRequestResultKind.Rejected }` — block this single action; the agent receives an error and can react.

---

## Interactive Prompt (All Kinds)

A single handler that prompts the user for each request. Useful for development.

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;

static Task<PermissionRequestResult> PromptPermission(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    Console.WriteLine($"\n[Permission Request: {request.Kind}]");
    if (!string.IsNullOrEmpty(request.FullCommandText))
        Console.WriteLine($"  Command: {request.FullCommandText}");
    if (!string.IsNullOrEmpty(request.Path))
        Console.WriteLine($"  Path: {request.Path}");
    if (!string.IsNullOrEmpty(request.Url))
        Console.WriteLine($"  URL: {request.Url}");

    Console.Write("Approve? (y/n): ");
    string? input = Console.ReadLine()?.Trim().ToUpperInvariant();
    PermissionRequestResultKind kind = input is "Y" or "YES"
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
        Content = "You are a helpful assistant.",
    },
    OnPermissionRequest = PromptPermission,
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);
```

---

## Shell Permission

Lets the agent run shell commands. Inspect `request.FullCommandText` before approving.

```csharp
static readonly string[] SafePrefixes = ["ls", "cat", "pwd", "echo"];

static Task<PermissionRequestResult> ApproveShellListingOnly(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    if (request.Kind != PermissionRequestKind.Shell)
    {
        return Task.FromResult(new PermissionRequestResult
        {
            Kind = PermissionRequestResultKind.Rejected,
        });
    }

    string cmd = (request.FullCommandText ?? string.Empty).Trim();
    bool isSafe = SafePrefixes.Any(p => cmd.StartsWith(p, StringComparison.Ordinal));

    return Task.FromResult(new PermissionRequestResult
    {
        Kind = isSafe
            ? PermissionRequestResultKind.Approved
            : PermissionRequestResultKind.Rejected,
    });
}
```

> **Security:** shell commands run with the privileges of the current process. Never auto-approve `Shell` unconditionally in untrusted environments.

---

## Read / Write File Permissions

Distinguish reads from writes. Optionally restrict by path prefix.

```csharp
static readonly string ProjectRoot = Path.GetFullPath(Directory.GetCurrentDirectory());

static Task<PermissionRequestResult> ApproveProjectFiles(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    if (request.Kind is not (PermissionRequestKind.Read or PermissionRequestKind.Write)
        || string.IsNullOrEmpty(request.Path))
    {
        return Task.FromResult(new PermissionRequestResult
        {
            Kind = PermissionRequestResultKind.Rejected,
        });
    }

    string target = Path.GetFullPath(request.Path);
    bool insideProject = target.StartsWith(ProjectRoot + Path.DirectorySeparatorChar, StringComparison.Ordinal)
                       || string.Equals(target, ProjectRoot, StringComparison.Ordinal);

    return Task.FromResult(new PermissionRequestResult
    {
        Kind = insideProject
            ? PermissionRequestResultKind.Approved
            : PermissionRequestResultKind.Rejected,
    });
}
```

---

## URL Permission

Allow the agent to fetch a web URL. Inspect `request.Url` before approving.

```csharp
static readonly HashSet<string> AllowedHosts = new(StringComparer.OrdinalIgnoreCase)
{
    "learn.microsoft.com",
    "docs.python.org",
};

static Task<PermissionRequestResult> ApproveKnownHosts(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    if (request.Kind != PermissionRequestKind.Url
        || string.IsNullOrEmpty(request.Url)
        || !Uri.TryCreate(request.Url, UriKind.Absolute, out Uri? uri))
    {
        return Task.FromResult(new PermissionRequestResult
        {
            Kind = PermissionRequestResultKind.Rejected,
        });
    }

    return Task.FromResult(new PermissionRequestResult
    {
        Kind = AllowedHosts.Contains(uri.Host)
            ? PermissionRequestResultKind.Approved
            : PermissionRequestResultKind.Rejected,
    });
}
```

---

## MCP Permission

When MCP servers are configured (see [mcp.md](mcp.md)), the CLI also surfaces `PermissionRequest` instances with `Kind = Mcp` for tool invocations. Approve them like any other kind.

```csharp
static Task<PermissionRequestResult> ApproveShellAndMcp(
    PermissionRequest request,
    PermissionInvocation invocation)
{
    bool approved = request.Kind is PermissionRequestKind.Shell or PermissionRequestKind.Mcp;
    return Task.FromResult(new PermissionRequestResult
    {
        Kind = approved
            ? PermissionRequestResultKind.Approved
            : PermissionRequestResultKind.Rejected,
    });
}
```

---

## Combining Multiple Kinds

For workflows that need several capabilities, gate each kind explicitly. A single yes/no prompt that prints the kind and relevant field works well for interactive use — see the **Interactive Prompt** section above. For production / unattended runs, prefer explicit allow-lists like the `Shell` and `Read/Write` examples.

```csharp
SessionConfig sessionConfig = new()
{
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = "You are a development assistant that can read, write files, and run shell commands.",
    },
    OnPermissionRequest = PromptPermission,
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig, ownsClient: true);

AgentResponse response = await agent.RunAsync(
    "List the first 3 .cs files, read the first one, then write a summary to summary.txt");
Console.WriteLine(response);
```

> The exact enum value names (`Shell`, `Read`, `Write`, `Url`, `Mcp`) and property names (`FullCommandText`, `Path`, `Url`) are defined in `GitHub.Copilot.SDK`. If your SDK version exposes them under slightly different names, use IntelliSense or `Go to Definition` to confirm — the patterns above remain valid.
