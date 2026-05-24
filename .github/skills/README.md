# Skills Used by This Workshop

This folder contains the **agent skills** that GitHub Copilot Coding Agent loads when working on workshop tasks. They are the API reference manuals for Microsoft Agent Framework + GitHub Copilot SDK across **Python and C# (.NET 10)**.

## Bundled Skills

### Python (`-py`)

| Skill | Description |
| --- | --- |
| [`agent-framework-githubcopilot-py`](agent-framework-githubcopilot-py/SKILL.md) | Build local `GitHubCopilotAgent` agents (Microsoft Agent Framework Python SDK) backed by the GitHub Copilot CLI. Covers sessions, permissions, MCP servers, function tools. |
| [`agent-framework-workflows-py`](agent-framework-workflows-py/SKILL.md) | Build Microsoft Agent Framework Workflows in Python: executors, edges, Sequential / Concurrent / Handoff / GroupChat / Magentic orchestration builders, checkpointing, HITL. |
| [`agent-framework-agui-py`](agent-framework-agui-py/SKILL.md) | Host MAF agents/workflows behind AG-UI HTTP/SSE with `add_agent_framework_fastapi_endpoint`; consume servers from Python with `AGUIChatClient`. |

### C# / .NET (`-csharp`)

| Skill | Description |
| --- | --- |
| [`agent-framework-githubcopilot-csharp`](agent-framework-githubcopilot-csharp/SKILL.md) | Build local GitHub Copilot–backed agents using the Microsoft Agent Framework for .NET (`Microsoft.Agents.AI.GitHub.Copilot`). Covers `CopilotClient.AsAIAgent`, `SessionConfig`, permission handlers, `AgentSession`, MCP servers, function tools via `AIFunctionFactory.Create`, streaming with `RunStreamingAsync`. |
| [`agent-framework-workflows-csharp`](agent-framework-workflows-csharp/SKILL.md) | Build deterministic multi-step workflows with `Microsoft.Agents.AI.Workflows`. Covers `WorkflowBuilder`, `Executor<TIn, TOut>`, `IWorkflowContext`, fan-out/fan-in, conditional edges, shared state, streaming, checkpoint/resume, sequential / concurrent / handoff / group chat / Magentic orchestration. |
| [`agent-framework-agui-csharp`](agent-framework-agui-csharp/SKILL.md) | Build AG-UI servers and clients with `Microsoft.Agents.AI.AGUI` + `Microsoft.Agents.AI.Hosting.AGUI.AspNetCore`. Covers `app.MapAGUI(...)`, `AGUIChatClient`, frontend tool rendering, predictive state updates, in-memory session storage, `DelegatingAIAgent`. |

### Domain (language-neutral)

| Skill | Description |
| --- | --- |
| [`zavashop-context`](zavashop-context/SKILL.md) | ZavaShop domain — SKU format, warehouse codes, order states, currency conventions, sample data locations. |

## How the Coding Agent Picks a Skill

When you assign an issue to `@copilot` (or post a `PROMPT.md` payload), Copilot Coding Agent:

1. Reads the prompt text + the repo's `.github/copilot-instructions.md`.
2. Reads the `target_language` directive in PROMPT.md (`python`, `csharp`, or `both`).
3. Scans skill `description` frontmatter fields.
4. Loads the matching `SKILL.md` files into context — picking the `-py` or `-csharp` variant per `target_language`.
5. Follows the instructions inside.

You don't need to mention skills by name — but the workshop's `PROMPT.md` files do, to make grading reliable.

## Updating the Skills

The six MAF skills track upstream `agent-framework` versions. To refresh:

```bash
# If you have gh skill (GitHub CLI 2.90+)
gh skill update --all

# Or manually copy newer versions from the source skill repo
```

Don't edit the bundled `SKILL.md` files in-place — the Coding Agent treats them as reference material, and ad-hoc edits will drift them away from the underlying SDK.

## Adding a New Skill

If you need to teach the Coding Agent something specific to your fork (an internal API, a custom orchestrator, etc.), follow the [GitHub Copilot skill docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills):

```
.github/skills/your-skill-name/
├── SKILL.md
└── (optional supporting files)
```

Frontmatter must include `name` and `description`. Keep the description specific so the Coding Agent only loads the skill when relevant. If your skill is language-specific, suffix the name with `-py` or `-csharp` and call that out in the description.
