# Custom Agents — ZavaShop Workshop

Custom agents are reusable **roles** that GitHub Copilot Coding Agent can assume for a task. Each agent profile is a Markdown file with YAML frontmatter (`name`, `description`) plus a prompt body that defines the role's scope, conventions, and which skills to load.

This workshop's four custom agents each speak **Python and C# (.NET 10)** — every profile contains parallel "Python variant" and "C# variant" canonical-pattern sections. The per-lab `PROMPT.md` directs the agent to one language via a `target_language` directive (`python`, `csharp`, or `both`).

> Docs: [About custom agents](https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/cloud-agent/about-custom-agents)

## Agents in this repo

| Agent | Lab | One-liner | Python skill | C# skill |
| --- | --- | --- | --- | --- |
| [`zava-single-agent-builder`](zava-single-agent-builder.md) | Lab 2 | One agent + function tools | [`agent-framework-githubcopilot-py`](../skills/agent-framework-githubcopilot-py/SKILL.md) | [`agent-framework-githubcopilot-csharp`](../skills/agent-framework-githubcopilot-csharp/SKILL.md) |
| [`zava-mcp-integrator`](zava-mcp-integrator.md) | Lab 3 | MCP server + agent that consumes it | [`agent-framework-githubcopilot-py`](../skills/agent-framework-githubcopilot-py/SKILL.md) | [`agent-framework-githubcopilot-csharp`](../skills/agent-framework-githubcopilot-csharp/SKILL.md) |
| [`zava-workflow-architect`](zava-workflow-architect.md) | Lab 4 | MAF Workflows (executors, edges, orchestration) | [`agent-framework-workflows-py`](../skills/agent-framework-workflows-py/SKILL.md) | [`agent-framework-workflows-csharp`](../skills/agent-framework-workflows-csharp/SKILL.md) |
| [`zava-agui-engineer`](zava-agui-engineer.md) | Lab 5 | AG-UI server + client | [`agent-framework-agui-py`](../skills/agent-framework-agui-py/SKILL.md) | [`agent-framework-agui-csharp`](../skills/agent-framework-agui-csharp/SKILL.md) |

## How a task uses them

```
.github/copilot-instructions.md     ← repo defaults (every task, both languages)
              │
              ▼
lab-NN/PROMPT.md                    ← deliverable + acceptance criteria
                                      + target_language: python | csharp | both
              │  "@copilot assign zava-<role> to this task"
              ▼
.github/agents/zava-<role>.md       ← role conventions + Python variant + C# variant
              │                       (read only the section that matches target_language)
              ▼
.github/skills/<skill>-{py|csharp}/SKILL.md   ← API reference (loaded on demand)
```

The PROMPT says **what** to build and **in which language**. The agent says **how** to build it (with one canonical pattern per language). The skill says **what API to call**. The repo instructions say **what the repo expects from every task**.

## Adding a new custom agent

1. Pick a lowercase, hyphenated name (e.g., `zava-eventing-engineer`).
2. Create `.github/agents/<name>.md` with YAML frontmatter:
   ```yaml
   ---
   name: zava-eventing-engineer
   description: One sentence saying what the role does and when to use it (and when NOT to use it — point at other agents). Mention both Python and C# if the agent supports both.
   ---
   ```
3. In the body, include: **Role**, **Your scope**, **Out of scope (refuse and redirect)**, **Before you write code** (skills list per language), **Conventions** (per language), **Canonical pattern — Python**, **Canonical pattern — C# (.NET)**, **When you finish**.
4. Add a row to the table above (with both skill columns filled in if dual-language).
5. Reference it from a `lab-NN/PROMPT.md` with `@copilot assign <name> to this task` and a `target_language` directive.

Keep agent profiles tight (~150–250 lines including both language variants). The skills should hold the long-form API content; the agent profile only encodes the role.
