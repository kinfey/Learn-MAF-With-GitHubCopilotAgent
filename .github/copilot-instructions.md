# Copilot Repo Instructions — ZavaShop Coding Agents Workshop

These instructions are injected into **every** GitHub Copilot Coding Agent task in this repository. Keep them short and stable — task-specific details belong in the per-lab `PROMPT.md`, and role-specific behavior belongs in the assigned **custom agent** profile.

## Three-Layer Customization

This workshop deliberately splits customization across three layers (see the GitHub docs on [agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) and [custom agents](https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/cloud-agent/about-custom-agents)):

| Layer | Where | Scope |
| --- | --- | --- |
| **Repo instructions** (this file) | `.github/copilot-instructions.md` | Conventions every task in this repo follows |
| **Custom agents** | `.github/agents/<name>.md` | A reusable role / persona with focused scope and required skills |
| **Skills** | `.github/skills/<name>/SKILL.md` | API reference material the agent loads on demand |
| **Task prompts** | `lab-NN/PROMPT.md` | One specific deliverable: goal, acceptance criteria, PR checklist |

**Read those in order.** When a task arrives:

1. This file gives you the repo defaults.
2. The PROMPT.md tells you which **custom agent** is assigned and what to deliver.
3. The custom agent profile tells you the conventions for that role and which skills to read.
4. The skills give you the API surface.

If a PROMPT.md was assigned to your repo but does **not** name a custom agent, refuse the task and ask the user to assign one of the four below.

## Project Context

This workshop teaches **Microsoft Agent Framework (MAF)** + **GitHub Copilot SDK** in **Python and C# (.NET 10)**. Every lab builds a small AI system for **ZavaShop**, a fictional retail + supply-chain company. Each custom agent below handles **both** languages — the per-lab `PROMPT.md` picks the target via a `target_language` directive.

Custom agents available in this repo (each speaks both Python and C#):

| Custom agent | Profile | Use for |
| --- | --- | --- |
| `zava-single-agent-builder` | [`.github/agents/zava-single-agent-builder.md`](agents/zava-single-agent-builder.md) | One `GitHubCopilotAgent` (Py) / `CopilotClient.AsAIAgent` (C#) + function tools (Lab 2) |
| `zava-mcp-integrator` | [`.github/agents/zava-mcp-integrator.md`](agents/zava-mcp-integrator.md) | `FastMCP` (Py) / `ModelContextProtocol` (C#) server + agent that consumes it (Lab 3) |
| `zava-workflow-architect` | [`.github/agents/zava-workflow-architect.md`](agents/zava-workflow-architect.md) | MAF Workflows: executors, edges, orchestration (Lab 4) |
| `zava-agui-engineer` | [`.github/agents/zava-agui-engineer.md`](agents/zava-agui-engineer.md) | AG-UI FastAPI (Py) / ASP.NET Core `MapAGUI` (C#) server + client (Lab 5) |

Skills shipped with the repo:

**Python (`-py`)**
- `agent-framework-githubcopilot-py` — building `GitHubCopilotAgent`, sessions, permissions, MCP wiring
- `agent-framework-workflows-py` — MAF Workflows (executors, edges, orchestration builders)
- `agent-framework-agui-py` — hosting agents/workflows on AG-UI HTTP/SSE; building clients

**C# / .NET (`-csharp`)**
- `agent-framework-githubcopilot-csharp` — `CopilotClient` + `AsAIAgent`, `SessionConfig`, `AIFunctionFactory.Create`, `AgentSession`
- `agent-framework-workflows-csharp` — `WorkflowBuilder`, `Executor<TIn, TOut>`, `IWorkflowContext`, sequential / concurrent / handoff / Magentic
- `agent-framework-agui-csharp` — `app.MapAGUI(...)` + `AGUIChatClient` (Microsoft.Agents.AI.AGUI)

**Domain**
- `zavashop-context` — ZavaShop catalog, warehouse map, order schema, naming conventions (language-neutral)

## Repo-Wide Defaults (apply to every task)

### Common (both languages)

- **Model**: GPT-5.5 via the GitHub Copilot SDK (`GITHUB_COPILOT_MODEL=gpt-5.5` in `.env`). All agents in the workshop are backed by the local GitHub Copilot CLI — no Azure / OpenAI keys.
- **Data files**: Everything in `data/` is read-only fixtures. Never edit them.
- **Async-first**: All MAF agents are async.
- **Comments**: Only when the *why* is non-obvious. Don't restate what the code says.
- **target_language**: Every `PROMPT.md` from Lab 2 onward specifies `target_language: python` or `target_language: csharp` (or `both`). Honor it — don't deliver C# if `python` was requested and vice versa.

### Python

- **Language**: Python 3.10+. Entry: `asyncio.run(main())` + `async with agent:`.
- **Package manager**: `uv pip install`; fall back to `pip` if `uv` is missing. Do not pin versions in `requirements.txt`.
- **Type hints**: Required on every public function signature.
- **Imports**:
  ```python
  from agent_framework import Agent, Workflow, WorkflowBuilder, WorkflowContext, executor, tool
  from agent_framework.github import GitHubCopilotAgent
  from agent_framework.ag_ui import AGUIChatClient, add_agent_framework_fastapi_endpoint
  ```

### C# / .NET

- **Language**: C# on **.NET 10 SDK** (or newer). Entry: top-level `await Main()` in a `Program.cs`.
- **Project layout**: One `.csproj` per lab folder. Console apps use `Microsoft.NET.Sdk`; AG-UI servers use `Microsoft.NET.Sdk.Web`. `<TargetFramework>net10.0</TargetFramework>`, `<Nullable>enable</Nullable>`, `<ImplicitUsings>enable</ImplicitUsings>`.
- **Package manager**: `dotnet add package <name> --prerelease` for all `Microsoft.Agents.AI.*` packages. Do not pin specific versions.
- **NuGet** (typical set; pick per lab):
  ```text
  GitHub.Copilot.SDK
  Microsoft.Agents.AI                 (--prerelease)
  Microsoft.Agents.AI.GitHub.Copilot  (--prerelease)
  Microsoft.Agents.AI.Workflows       (--prerelease, Lab 4)
  Microsoft.Agents.AI.AGUI            (--prerelease, Lab 5 client)
  Microsoft.Agents.AI.Hosting.AGUI.AspNetCore  (--prerelease, Lab 5 server)
  Microsoft.Extensions.AI             (--prerelease)
  ModelContextProtocol                (--prerelease, Lab 3)
  ```
- **Lifecycle**: Always `await using` on `CopilotClient` and `StreamingRun`. Pass `ownsClient: true` to `AsAIAgent` so the agent disposes the CLI subprocess on shutdown.
- **Async**: Use `await`/`async`, `IAsyncEnumerable<T>` for streaming, `ValueTask` for executor hot paths.
- **JSON**: Use System.Text.Json source generators (`[JsonSerializable]` + `JsonSerializerContext`) for catalog records — keeps the build trim-/AOT-friendly.
- **Usings**:
  ```csharp
  using GitHub.Copilot.SDK;
  using Microsoft.Agents.AI;
  using Microsoft.Agents.AI.GitHub.Copilot;
  using Microsoft.Agents.AI.Workflows;
  using Microsoft.Agents.AI.AGUI;
  using Microsoft.Extensions.AI;
  ```

## Universal Workflow (every lab)

1. Identify which **custom agent** the PROMPT.md assigns. Refuse to start without one.
2. Read the `target_language` directive in PROMPT.md (`python`, `csharp`, or `both`). The custom agent profile contains a section for each language — read **only** the section(s) for the requested language(s).
3. Read the assigned custom agent profile in full (skip the language sections that don't apply).
4. Read the skills the agent profile points at — and **only** those. Pick the `-py` or `-csharp` skill that matches `target_language`.
5. Read `zavashop-context` for any domain references touched by the PROMPT (language-neutral).
6. Scaffold the requested files **inside the assigned `lab-NN/` folder only**. For C# tasks, place sources under `lab-NN/csharp/` (a single `.csproj` per project). For Python tasks, place sources directly in `lab-NN/`.
7. Per-lab dependency manifest:
   - Python → `requirements.txt` (unpinned).
   - C# → `*.csproj` with `<PackageReference>` entries (no explicit `Version` — let `--prerelease` pick).
8. Add a one-sentence header at the top of each new file (which lab and language it belongs to).
9. Self-verify against the PROMPT.md acceptance criteria with `verify.py` (Python) or `dotnet run --project ./csharp/verify` (C#).
10. Open the PR with a body that maps every acceptance criterion to a diff line.

## Universal Prohibitions

- Generating solutions for multiple labs in one PR.
- Editing `data/`, `.github/skills/`, `.github/agents/`, `README.md`, `README.zh.md`, `SETUP.md`, `.github/copilot-instructions.md`, or **any other lab's folder** unless the PROMPT explicitly asks.
- Hard-coding API keys or secrets — read from environment variables.
- **Python**: importing libraries not in the lab's `requirements.txt`. Using `print(...)` for structured data — use `json.dumps(..., indent=2)`.
- **C#**: adding NuGet packages not in the lab's `.csproj`. Using `Console.WriteLine` for structured data — use `JsonSerializer.Serialize(obj, opts)`.
- Delivering the wrong language (e.g. PROMPT says `target_language: csharp` but you ship a `.py` file). When in doubt, ask.
- Working without an assigned custom agent — always require the assignment first.

## Conflict Resolution

If the assigned custom agent's profile and the PROMPT.md disagree, **the PROMPT.md wins for "what to deliver" and the agent profile wins for "how to deliver it"**. If they conflict on something fundamental (e.g., the PROMPT asks for an MCP server but assigns `zava-single-agent-builder`), stop and ask the user to reassign instead of improvising.
