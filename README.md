# ZavaShop Coding Agents Workshop
### Microsoft Agent Framework + GitHub Copilot SDK · **Python and C# (.NET 10)** — Driven by GitHub Copilot Coding Agent (GPT-5.5)

> **Learning goal.** This workshop teaches the **Microsoft Agent Framework (MAF)** by example. The **GitHub Copilot SDK** (`GitHubCopilotAgent` in Python, `CopilotClient.AsAIAgent` in .NET) is the concrete agent runtime — zero API keys, zero model deployment — so your focus stays on MAF concepts. **GitHub Copilot Coding Agent** writes the code so you stay in the role of an *architect* who designs and reviews, not a typist. Every lab introduces one slice of MAF, builds it with the SDK, and ships it via the Coding Agent.
>
> **One workshop, two languages.** Every lab can be completed in **Python** or **C# (.NET 10)** — the model backbone, the custom agents, the PROMPT.md acceptance criteria, and the MAF concepts are identical. The per-lab `PROMPT.md` carries a `target_language` directive (`python`, `csharp`, or `both`) that tells the Coding Agent which stack to ship.

> **How the labs work.** For each lab you assign a **custom agent** (a reusable role that speaks both Python *and* C#) to a **task prompt** (a specific deliverable). GitHub Copilot Coding Agent (running on GPT-5.5) takes it from there — backed by the pre-installed Microsoft Agent Framework skills (one per language).

> **References**: [About custom agents](https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/cloud-agent/about-custom-agents) · [Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)

---

## The ZavaShop Story

ZavaShop is a fictional global retailer of beauty & lifestyle products. The company has two halves:

- **Retail** — customers browse, ask questions, place orders, and track shipments. Front-line agents need product knowledge, real-time stock, and access to order systems.
- **Supply Chain** — buyers forecast demand, place purchase orders with suppliers, route inventory through five warehouses, and reconcile stock with the retail side.

Over five labs you will **learn the Microsoft Agent Framework** by building automation for both halves — implemented in your choice of **Python** or **C# (.NET 10)** with the **GitHub Copilot SDK** as the agent runtime, and **written by GitHub Copilot Coding Agent** under your direction.

---

## Workshop Agenda (5 Labs)

| # | Lab | MAF concept(s) learned | How you build it | Outcome (Python and/or C#) |
| --- | --- | --- | --- | --- |
| 1 | [基础知识 — Fundamentals](lab-01-fundamentals/README.md) | Agent runtime model, `Agent` base abstraction | Hand-written (1 Python script + 1 C# console project) | A "Hello, ZavaShop" Copilot-backed agent |
| 2 | [单 Agent — Product Advisor](lab-02-single-agent/README.md) | Function tools, `AgentSession`, streaming | Coding Agent + `zava-single-agent-builder` | A product Q&A agent backed by Zava's catalog |
| 3 | [MCP — Inventory Service](lab-03-mcp/README.md) | Local MCP tools, tool approval (HITL) | Coding Agent + `zava-mcp-integrator` | Agent that queries live stock across warehouses |
| 4 | [多 Agent 工作流 — Retail & Supply Chain](lab-04-multi-agent-workflow/README.md) | Workflows: executors, edges, Sequential / Concurrent / Handoff | Coding Agent + `zava-workflow-architect` | Two end-to-end workflows for retail and supply chain |
| 5 | [AGUI — Hosted Coding Agent UI](lab-05-agui/README.md) | AG-UI integration, hybrid tool execution | Coding Agent + `zava-agui-engineer` | Web-ready streaming front for the retail workflow |

Each lab is independent in code but builds conceptually on the previous one. The **MAF concept** column is what you walk away knowing; **How you build it** is the vehicle. Pick Python or C# per lab — there is no requirement to stay on one stack across labs.

---

## Microsoft Agent Framework concept map

Each lab anchors on a distinct slice of the [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/). The order follows the official docs: **agents** first, then **workflows**, then **integrations**. Every lab README opens with a "Microsoft Agent Framework concepts in this lab" table — read it before assigning the custom agent so you know which MAF surface the Coding Agent is about to exercise.

| Lab | MAF concept(s) introduced | Microsoft Learn |
| --- | --- | --- |
| 1 | Agent runtime execution model · `Agent` base abstraction · Agent vs Workflow | [Overview](https://learn.microsoft.com/en-us/agent-framework/overview/) · [Agent types](https://learn.microsoft.com/en-us/agent-framework/agents/) |
| 2 | **Function Tools** · **`AgentSession`** (multi-turn) · Streaming responses | [Tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) · [Session](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/session) |
| 3 | **Local MCP Tools** · **Tool Approval (HITL)** · Function + MCP tools on one agent | [Tools Overview](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) |
| 4 | **Workflows**: Executors · Edges · WorkflowBuilder · Sequential / Concurrent / Handoff · Agent-as-Executor | [Workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/) · [Executors](https://learn.microsoft.com/en-us/agent-framework/workflows/executors) · [Edges](https://learn.microsoft.com/en-us/agent-framework/workflows/edges) |
| 5 | **AG-UI integration** · `workflow_factory` thread state · **Hybrid tool execution** (server + client tools) | [Integrations](https://learn.microsoft.com/en-us/agent-framework/integrations/) |

> The two top-level MAF capabilities — **Agents** (LLM-driven, dynamic) and **Workflows** (graph-based, explicit) — are introduced in Lab 1, exercised in Labs 2/3 (agents) and Lab 4 (workflows), and combined in Lab 5 via AG-UI.

---

## What Drives the Code: Custom Agents + Skills + Prompts

The workshop combines three GitHub Copilot customization mechanisms:

### 1. Custom Agents — the reusable *roles*

Defined under [`.github/agents/`](.github/agents/README.md). Each one encodes a specialist persona (scope, conventions, which skills to read) — **not** the lab-specific work itself. **Each profile contains parallel Python and C# (.NET) sections**; the assigned coding agent reads only the section matching the PROMPT.md `target_language` directive.

| Custom Agent | Lab | Role |
| --- | --- | --- |
| [`zava-single-agent-builder`](.github/agents/zava-single-agent-builder.md) | 2 | One Copilot-backed agent + function tools (Python `@tool` / C# `AIFunctionFactory.Create`) |
| [`zava-mcp-integrator`](.github/agents/zava-mcp-integrator.md) | 3 | MCP server (`FastMCP` / `ModelContextProtocol`) + agent that consumes it |
| [`zava-workflow-architect`](.github/agents/zava-workflow-architect.md) | 4 | MAF Workflows: executors, edges, orchestration (Python `@executor` / C# `Executor<TIn,TOut>`) |
| [`zava-agui-engineer`](.github/agents/zava-agui-engineer.md) | 5 | AG-UI server + client (FastAPI / ASP.NET Core) |

### 2. Skills — the *API reference*

Defined under [`.github/skills/`](.github/skills/README.md). Each custom agent declares which skill(s) it reads — Copilot loads only the language-matching `-py` or `-csharp` variant on demand.

| Skill | Teaches Copilot how to… |
| --- | --- |
| [`agent-framework-githubcopilot-py`](.github/skills/agent-framework-githubcopilot-py/SKILL.md) | Build `GitHubCopilotAgent` in Python, manage sessions, permissions, MCP servers |
| [`agent-framework-workflows-py`](.github/skills/agent-framework-workflows-py/SKILL.md) | Build MAF Workflows in Python: executors, edges, orchestration, HITL |
| [`agent-framework-agui-py`](.github/skills/agent-framework-agui-py/SKILL.md) | Host agents/workflows behind AG-UI HTTP/SSE in Python, build clients |
| [`agent-framework-githubcopilot-csharp`](.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) | Build Copilot-backed agents in .NET via `CopilotClient.AsAIAgent`, sessions, MCP, function tools |
| [`agent-framework-workflows-csharp`](.github/skills/agent-framework-workflows-csharp/SKILL.md) | Build MAF Workflows in .NET: `WorkflowBuilder`, `Executor<TIn,TOut>`, fan-out/fan-in, streaming |
| [`agent-framework-agui-csharp`](.github/skills/agent-framework-agui-csharp/SKILL.md) | Host agents in ASP.NET Core via `MapAGUI`, consume via `AGUIChatClient`, frontend tools |
| [`zavashop-context`](.github/skills/zavashop-context/SKILL.md) | ZavaShop catalog, warehouses, order schema, naming conventions (language-neutral) |

### 3. Task Prompts — the per-lab *deliverable*

Each lab ships a small [`PROMPT.md`](lab-02-single-agent/PROMPT.md) that names which custom agent to assign, declares the `target_language` (`python` / `csharp` / `both`), and lists the deliverables + acceptance criteria. The prompt does **not** restate conventions — those live in the agent profile.

### How a lab works (end to end)

```
1. Read lab-NN/README.md                 →  story, goal, architecture (Python + C# walk-through)
2. Open lab-NN/PROMPT.md                  →  copy its contents
     ▸ first line assigns the custom agent
     ▸ target_language directive picks Python / C# / both
3. Open an Issue / @copilot in your fork  →  paste the prompt
4. Coding Agent (GPT-5.5):
     a. loads .github/copilot-instructions.md   (repo defaults, dual-language)
     b. loads the assigned custom agent profile (the role)
     c. loads only the language-matching skills (-py or -csharp)
     d. writes code inside lab-NN/  (Python files at the root and/or C# files under lab-NN/csharp/)
     e. opens a PR
5. You review the PR, run verify.py (Python) and/or dotnet run --project ./csharp/verify (C#), merge
```

The Coding Agent uses **GPT-5.5** for all generation — the same model powers both the Python and the C# tracks. Configure it once in Lab 1.

---

## Prerequisites

Before you start, you need:

- **GitHub account** with **Copilot Pro+ / Business / Enterprise** (Coding Agent access)
- **GitHub Copilot CLI** installed and authenticated (`copilot auth`) — Lab 1 verifies this
- For the **Python track**: Python 3.10+ with `uv` (or `pip`)
- For the **C# track**: **.NET 10 SDK**
- **Node.js 18+** (for some MCP servers in Lab 3)
- A fork of this workshop repository (Coding Agent needs a repo to work in)

Full setup steps in [SETUP.md](SETUP.md).

---

## Repository Layout

```
zavashop-maf-ghc-workshop/
├── README.md                        # ← you are here
├── README.zh.md                     # Chinese mirror
├── SETUP.md                         # Environment + Copilot Coding Agent setup (Python + .NET)
├── .github/
│   ├── copilot-instructions.md      # Repo-wide instructions injected on every task (dual-language)
│   ├── agents/                      # Custom agents (each profile carries Python + C# sections)
│   │   ├── zava-single-agent-builder.md
│   │   ├── zava-mcp-integrator.md
│   │   ├── zava-workflow-architect.md
│   │   └── zava-agui-engineer.md
│   └── skills/                      # Skills (API reference loaded on demand)
│       ├── agent-framework-githubcopilot-py/
│       ├── agent-framework-workflows-py/
│       ├── agent-framework-agui-py/
│       ├── agent-framework-githubcopilot-csharp/
│       ├── agent-framework-workflows-csharp/
│       ├── agent-framework-agui-csharp/
│       └── zavashop-context/
├── data/                            # Shared sample data — read by both Python and C#
│   ├── zava_catalog.json
│   ├── zava_warehouses.json
│   └── zava_orders.sample.json
├── lab-01-fundamentals/             # Setup + verify (no Coding Agent task)
│   ├── verify.py                    # Python smoke test
│   └── csharp/HelloZava/            # C# smoke test (.csproj + Program.cs)
├── lab-02-single-agent/             # README.md + PROMPT.md → zava-single-agent-builder
│   └── csharp/                      # C# track lives here when target_language=csharp
├── lab-03-mcp/                      # README.md + PROMPT.md → zava-mcp-integrator
├── lab-04-multi-agent-workflow/     # README.md + PROMPT.md → zava-workflow-architect
└── lab-05-agui/                     # README.md + PROMPT.md → zava-agui-engineer
```

---

## Conventions Across the Workshop

- **Python packages** — `agent-framework-github-copilot`, `agent-framework-core`, `agent-framework-ag-ui`, plus `mcp` for the MCP server.
- **Python imports** — `from agent_framework.github import GitHubCopilotAgent`, `from agent_framework import Agent, Workflow, WorkflowBuilder, tool, executor`, `from agent_framework.ag_ui import ...`.
- **.NET NuGet packages** (all `--prerelease`) — `GitHub.Copilot.SDK`, `Microsoft.Agents.AI`, `Microsoft.Agents.AI.GitHub.Copilot`, `Microsoft.Agents.AI.Workflows`, `Microsoft.Agents.AI.AGUI`, `Microsoft.Agents.AI.Hosting.AGUI.AspNetCore`, `Microsoft.Extensions.AI`, `ModelContextProtocol`.
- **.NET project SDKs** — `Microsoft.NET.Sdk` for console / library; `Microsoft.NET.Sdk.Web` for AG-UI server and MCP HTTP server. Target framework `net10.0`, `Nullable=enable`, `ImplicitUsings=enable`.
- **Model** — `GITHUB_COPILOT_MODEL=gpt-5.5` (set in `.env` and read by both SDKs).
- **Domain data** — every lab's tools read from `data/zava_*.json`. Keep the data files unchanged; tools must adapt to the schema. Both Python and C# read the same JSON.
- **Code style** — async-first. Python: `async with agent:` / `async with client:`. C#: `await using CopilotClient ...` / `await using StreamingRun ...`.
- **Acceptance** — each lab's README ends with a checklist. The Coding Agent should self-verify with `verify.py` (Python) or `dotnet run --project ./csharp/verify` (C#); you ratify in the PR review.

---

## How to Use This Workshop With Copilot Coding Agent

1. **Fork** this repo. The Coding Agent only operates on repos you own.
2. **Enable Copilot Coding Agent** on the fork: repo Settings → Code & automation → Copilot → enable.
3. **Set the model to GPT-5.5** in your Copilot settings.
4. **For each lab** (Lab 2 onward), open an issue or `@copilot` mention in your fork with the contents of `lab-NN/PROMPT.md`. The first line assigns the custom agent; the `target_language` directive picks Python or C#.
5. **Review** the PR the Coding Agent opens. Run `python verify.py` (Python) and/or `dotnet run --project ./csharp/verify` (C#) locally, ratify the acceptance criteria, merge.

> Why split into custom agents + skills + prompts? Three reasons:
> 1. **Reusability** — a custom agent like `zava-workflow-architect` can be assigned to *any* workflow task in *either* language, not just Lab 4.
> 2. **Focus** — Copilot loads only the skills the assigned agent needs (and only the `-py` or `-csharp` variant), keeping the context window lean.
> 3. **Clarity for you** — you learn what belongs in a *role* (HOW), in a *skill* (API), in a *prompt* (WHAT + which language), and in *repo instructions* (defaults). Those are the four levers of agent customization.

Every PROMPT.md is also a perfectly valid task description for any other coding agent (Claude Code, Cursor, your own MAF orchestrator) — just drop the `@copilot assign` line and feed the rest as a regular prompt.

---

## Got stuck?

- **Lab 1** covers the most common setup pitfalls (CLI auth, skill discovery, model selection).
- The skill files under `.github/skills/` are your reference manual — open them whenever the Coding Agent's output references an API you don't recognize.
- Each lab README includes a "Common mistakes" section near the bottom.

Let's get started → [Lab 1 — Fundamentals](lab-01-fundamentals/README.md).
