# Lab 1 — Fundamentals

> Estimated time: 30 minutes. **You do not call the Coding Agent in this lab** — you set up the environment and run a smoke test in your language of choice to confirm everything works.
>
> **Learning goal**: meet the **MAF agent runtime model** by bringing up your first Copilot-backed agent. Both languages are walked through inline below; pick **Python**, **C# (.NET 10)**, or run both. From Lab 2 onward, the GitHub Copilot SDK is the runtime and the Coding Agent writes the code; both depend on this lab working.

## ZavaShop Story

Before you wire up agents for retail and supply chain, your local toolbox needs to talk to GitHub Copilot. In this lab you bring up a minimal Copilot-backed agent that introduces itself as ZavaShop's AI assistant — running on **GPT-5.5**.

If this lab works, the next four labs work too. If it doesn't, fix it here before moving on.

## Microsoft Agent Framework concepts in this lab

Lab 1 anchors on the foundational mental model the rest of the workshop builds on.

| Concept | What it means | Microsoft Learn |
| --- | --- | --- |
| **Agent vs Workflow** | An *agent* is LLM-driven and decides its steps at runtime; a *workflow* is an explicit graph of steps. Labs 2–3 build agents, Lab 4 builds workflows, Lab 5 hosts both. | [Overview](https://learn.microsoft.com/en-us/agent-framework/overview/) |
| **Default Agent Runtime Execution Model** | The standard loop: user input → model inference → (optional) tool call → response. `GitHubCopilotAgent` (Python) and `CopilotClient.AsAIAgent` (.NET) are two concrete realisations of this model — same loop, different language surface. | [Agent types](https://learn.microsoft.com/en-us/agent-framework/agents/) |
| **`Agent` base abstraction** | Every MAF agent inherits a common base (Python `Agent` / .NET `AIAgent`), which is why multi-agent orchestrations, workflows, and AG-UI can all consume them uniformly — you'll see this pay off in Labs 4 and 5. | [Agent types](https://learn.microsoft.com/en-us/agent-framework/agents/) |

## What You Will Learn

- How the GitHub Copilot SDK plugs the local `copilot` CLI into your runtime — Python via `GitHubCopilotAgent`, .NET via `CopilotClient.AsAIAgent`.
- How `GITHUB_COPILOT_MODEL` pins the workshop to GPT-5.5 in both stacks.
- How `async with agent:` (Python) and `await using CopilotClient` (.NET) manage the CLI subprocess lifecycle.
- How `.github/skills/` powers the GitHub Copilot Coding Agent that drives Labs 2–5 — with `-py` and `-csharp` variants of each MAF skill.

## Prerequisites

You have completed [SETUP.md](../SETUP.md). Specifically:

- `copilot auth` succeeded.
- `python -c "import agent_framework.github"` runs without error.
- `.env` contains `GITHUB_COPILOT_MODEL=gpt-5.5`.

## Concepts (read once)

```
┌──────────────────────────┐   spawns   ┌──────────────────────────┐
│  Python: GitHubCopilot   │ ─────────► │  copilot CLI (subprocess)│
│  Agent(...)              │ ◄───────── │  GPT-5.5 over GH Copilot │
│  - tools (Python fns)    │   stdio    │  - sessions, MCP, perms  │
│  - permission handlers   │            │                          │
└──────────────────────────┘            └──────────────────────────┘
```

- **You write Python**. The SDK runs the `copilot` CLI as a child process and streams events.
- **No Azure key, no OpenAI key.** Auth is handled by `copilot auth` once, then reused.
- **Async-first.** Use `asyncio.run(main())` and `async with agent:`.

The complete API is documented in [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md). Open it now and skim the table of contents — you will refer back to it in Labs 2 and 3.

## What You Will Do

1. Read this README.
2. Run the smoke test in your language of choice (or both):
   - **Python**: `verify.py` builds a tiny `GitHubCopilotAgent` whose only job is to say hello in character for ZavaShop.
   - **C# (.NET)**: `csharp/HelloZava/Program.cs` does the same with `CopilotClient.AsAIAgent`.
3. Confirm the agent uses **GPT-5.5** (the model is printed in the script's intro line).
4. Enable GitHub Copilot Coding Agent on your fork (only needed once for Labs 2–5).

### Python track

```bash
cd lab-01-fundamentals
python verify.py
```

Expected output (truncated):

```
[ZavaShop AI Bootstrap]
  Model:    gpt-5.5
  CLI:      copilot
  Skills:   7 found under ../.github/skills/

Agent  : Hello! I am the ZavaShop AI assistant, powered by GPT-5.5 …
        We carry beauty and lifestyle products across five regional warehouses …

[OK] Lab 1 complete. Proceed to Lab 2.
```

### C# / .NET track

The lab ships a minimal console project at `lab-01-fundamentals/csharp/HelloZava/`:

```
lab-01-fundamentals/csharp/HelloZava/
├── HelloZava.csproj           # Microsoft.NET.Sdk, net10.0, refs GitHub.Copilot.SDK + Microsoft.Agents.AI.GitHub.Copilot
└── Program.cs                 # See snippet below
```

`HelloZava.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="GitHub.Copilot.SDK" Version="*-*" />
    <PackageReference Include="Microsoft.Agents.AI" Version="*-*" />
    <PackageReference Include="Microsoft.Agents.AI.GitHub.Copilot" Version="*-*" />
    <PackageReference Include="Microsoft.Extensions.AI" Version="*-*" />
  </ItemGroup>
</Project>
```

`Program.cs`:

```csharp
using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.GitHub.Copilot;

string model = Environment.GetEnvironmentVariable("GITHUB_COPILOT_MODEL") ?? "gpt-5.5";
Console.WriteLine($"[ZavaShop AI Bootstrap]\n  Model:    {model}\n  CLI:      copilot\n");

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

AIAgent agent = copilotClient.AsAIAgent(
    ownsClient: true,
    name: "ZavaShopHello",
    instructions: "You are the ZavaShop AI assistant. Introduce yourself in one short paragraph and mention at least one product category (skincare, fragrance, makeup, haircare, or wellness).");

await foreach (AgentRunResponseUpdate update in agent.RunStreamingAsync("Please introduce yourself."))
{
    Console.Write(update);
}
Console.WriteLine("\n\n[OK] Lab 1 complete. Proceed to Lab 2.");
```

Run it:

```bash
cd lab-01-fundamentals/csharp/HelloZava
dotnet run
```

Expected output mirrors the Python run — a streamed intro from a Copilot-backed agent.

## Acceptance Criteria

- [ ] Either `verify.py` (Python) **or** `dotnet run --project csharp/HelloZava` (.NET) runs to completion with no traceback.
- [ ] The printed model is `gpt-5.5`.
- [ ] The streamed response mentions ZavaShop and at least one product category.
- [ ] `.github/skills/` discovery in `verify.py` lists **seven** skills (three Python MAF skills + three C# MAF skills + `zavashop-context`).
- [ ] You have enabled GitHub Copilot Coding Agent on your fork and selected GPT-5.5 as the model (UI step, no automated check).

## Common Mistakes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: agent_framework.github` | Python SDK not installed (or installed without `--pre`) | `uv pip install "agent-framework-github-copilot --pre"` |
| `error NU1102: Unable to find package Microsoft.Agents.AI...` | .NET preview packages need `--prerelease` | Re-run `dotnet add package <name> --prerelease`; or `dotnet restore` after editing the `.csproj` |
| `error NETSDK1045: The current .NET SDK does not support targeting net10.0` | .NET 10 SDK missing | Install .NET 10 SDK (see SETUP.md §1) |
| `copilot: command not found` (raised from inside Python/.NET) | `copilot` CLI not on `PATH` | Re-install GH Copilot CLI; verify with `which copilot` |
| Model prints as `gpt-5` (not `gpt-5.5`) | `.env` not loaded | Python: ensure `python-dotenv` is installed and the script calls `load_dotenv()`. .NET: export `GITHUB_COPILOT_MODEL` in your shell before `dotnet run`, or use `DotNetEnv` |
| Hangs on first run, no output | `copilot auth` not run on this machine | Run `copilot auth` and re-try |

When Lab 1 is green, move on. → [Lab 2 — Single Agent](../lab-02-single-agent/README.md)
