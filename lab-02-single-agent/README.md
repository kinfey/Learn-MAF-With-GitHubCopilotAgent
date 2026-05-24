# Lab 2 — Single Agent: ZavaShop Product Advisor

> Estimated time: 45 minutes. **You drive the Copilot Coding Agent — you don't write the code by hand.**
>
> **Learning goal**: practice MAF's **function tools, sessions, and response streaming** by building a product advisor. The GitHub Copilot SDK provides the runtime in both stacks — Python `GitHubCopilotAgent` + `@tool`, or C# `CopilotClient.AsAIAgent` + `AIFunctionFactory.Create` — the Coding Agent writes the implementation under your direction in the language you pick via `target_language`.

## ZavaShop Story

Customer-facing chat at ZavaShop currently answers ~60% of product questions with canned responses. The retail team wants an AI **Product Advisor** that can answer real questions against the live catalog:

> "Do you sell a red matte lipstick under $30?"  
> "What's the difference between SKN-027 and SKN-030?"  
> "I have oily skin — what foundation do you recommend?"

You will build that advisor as a single `GitHubCopilotAgent` with three function tools, all reading from `data/zava_catalog.json`.
## Microsoft Agent Framework concepts in this lab

| Concept | What it means in code | Microsoft Learn |
| --- | --- | --- |
| **Function Tools** | Plain functions exposed to the LLM — Python via `@tool` + Pydantic-typed parameters, C# via `AIFunctionFactory.Create(myFn)` reading `[Description]` attributes. The LLM decides when to call which one. | [Tools Overview](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) · [Function Tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/function-tools) |
| **Agent Session** | The conversation state container reused across runs. Python: `agent.create_session()` + pass `session=session` to every `agent.run`. C#: `await agent.CreateSessionAsync()` returns an `AgentSession` you pass back in. Same idea, two surfaces. | [Session](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/session) |
| **Streaming responses** | Token-stream the reply. Python: `async for chunk in agent.run(..., stream=True)`. C#: `await foreach (var update in agent.RunStreamingAsync(...))`. | [Agent types](https://learn.microsoft.com/en-us/agent-framework/agents/) |
## Run This Lab

This lab is **driven by a custom Coding Agent**, not by hand-rolling a prompt. The `target_language` directive in [`PROMPT.md`](PROMPT.md) decides which stack the Coding Agent ships.

1. Open an issue (or `@copilot` comment) in your fork and **paste the contents of [`PROMPT.md`](PROMPT.md)**. The first line assigns the custom agent; the `target_language` line picks `python`, `csharp`, or `both`.
2. The Coding Agent will:
   - Load the [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md) profile — it contains canonical patterns for **both** languages; the agent will only read the section matching `target_language`.
   - Read only the skills that match the language (`agent-framework-githubcopilot-py` or `agent-framework-githubcopilot-csharp`), plus the shared `zavashop-context`. It will **not** read workflow or AG-UI skills.
   - Scaffold the deliverables — Python files in the lab folder, C# project under `csharp/`.
   - Open a PR. You review, run the language-appropriate verify, merge.

| Layer | Where the role / API / task lives |
| --- | --- |
| Role (HOW) | [`.github/agents/zava-single-agent-builder.md`](../.github/agents/zava-single-agent-builder.md) (has **both** Python and C# sections) |
| API reference (Python) | [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md), [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) |
| API reference (C#) | [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md), [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) |
| Task (WHAT + which language) | [`PROMPT.md`](PROMPT.md) |

## What You Will Learn

- Defining function tools in your language of choice: Python `@tool` + Pydantic, or C# `AIFunctionFactory.Create` reading `[Description]` attributes.
- Wiring tools into the Copilot-backed agent and streaming the reply.
- Keeping conversation context with `agent.create_session()` / `await agent.CreateSessionAsync()`.
- How the agent's *instructions* shape the LLM's plan even when no tool fires.

## Custom Agent + Skills (set by [`PROMPT.md`](PROMPT.md))

- **Custom agent**: [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md) — the role profile encodes conventions and the canonical pattern in **both** Python and C# sections.
- **Skills the agent will read**: language-matched MAF skill (`-py` or `-csharp` variant of `agent-framework-githubcopilot`) + [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) (catalog schema, SKU rules; language-neutral).

## Deliverable

The Coding Agent creates one of the layouts below inside `lab-02-single-agent/`, depending on `target_language`. With `target_language: both` it creates **both** sub-trees.

### Python (`target_language: python`)

```
lab-02-single-agent/
├── README.md            (this file — already exists)
├── PROMPT.md            (the prompt for Copilot Coding Agent — already exists)
├── requirements.txt
├── product_advisor.py   ← the agent and its tools
└── verify.py            ← scripted acceptance test
```

### C# / .NET (`target_language: csharp`)

```
lab-02-single-agent/
└── csharp/
    ├── ProductAdvisor/
    │   ├── ProductAdvisor.csproj      # Microsoft.NET.Sdk, net10.0
    │   ├── Program.cs                  # CopilotClient + AsAIAgent + 3 tools
    │   ├── CatalogTools.cs             # static methods with [Description] attrs
    │   └── Models.cs                   # record types for catalog rows
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                  # three-turn acceptance test
```

`ProductAdvisor.csproj` references `GitHub.Copilot.SDK`, `Microsoft.Agents.AI`, `Microsoft.Agents.AI.GitHub.Copilot`, `Microsoft.Extensions.AI` (all `--prerelease`). The three tools become static methods on `CatalogTools` and are passed to `CopilotClient.AsAIAgent(...)` as `tools: [AIFunctionFactory.Create(CatalogTools.SearchProducts), AIFunctionFactory.Create(CatalogTools.GetProductDetails), AIFunctionFactory.Create(CatalogTools.RecommendAlternatives)]`. See the canonical pattern in [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md).

## Acceptance Criteria

The Coding Agent must satisfy each item below. The verify script it creates (`verify.py` for Python or `csharp/Verify/Program.cs` for C#) must check items 4–7 automatically in the chosen language.

1. Exactly **three** function tools (same shapes in both languages):
   - `search_products` / `SearchProducts(query, category?, maxPriceUsd?)` returning a list of catalog rows.
   - `get_product_details` / `GetProductDetails(sku)` returning the row or the **literal string** `"NOT_FOUND: <sku>"` on miss (per `zavashop-context`).
   - `recommend_alternatives` / `RecommendAlternatives(sku, maxResults=3)` returning a list.
2. Tools read from `data/zava_catalog.json` only. No hard-coded SKUs. In C#, deserialize once at startup (e.g. `JsonSerializer.Deserialize` into a `record CatalogRow(...)` array).
3. The agent is constructed once at program scope. Python: `GitHubCopilotAgent(instructions=..., tools=[...])` inside `async with`. C#: `await using CopilotClient` + `client.AsAIAgent(ownsClient: true, name, instructions, tools)`.
4. Multi-turn: a single session is reused across at least three turns. Python: same `agent.create_session()`. C#: same `AgentSession` from `await agent.CreateSessionAsync()`. The second turn references information established in the first.
5. The script handles *"Do you sell a red matte lipstick under $30?"* and the answer **must** mention `LIP-001` and `$24`.
6. The script handles *"What's the difference between SKN-027 and SKN-030?"* and the answer mentions both SKUs and the words *night* (for SKN-027) and *vitamin C* (for SKN-030).
7. The script handles *"Tell me an alternative to FRG-015 in a similar price range."* and the answer mentions `FRG-009`.
8. The verify script exits 0 when all three turns satisfy their substring checks; non-zero otherwise.

## Run It

### Python

```bash
cd lab-02-single-agent
uv pip install -r requirements.txt
python verify.py
```

### C# / .NET

```bash
cd lab-02-single-agent/csharp
dotnet run --project Verify
```

A passing run prints three labelled turns followed by `[OK] Lab 2 complete.`

## Common Mistakes

| Symptom | Cause |
| --- | --- |
| Agent invents SKUs not in the catalog | Tool returned an empty list; instructions don't say "answer only from tool output" |
| Turn 2 forgets context | New session every turn — Python: pass `session=session`; C#: pass `session` to `RunAsync` |
| `search_products` / `SearchProducts` returns everything | Missing filter logic — read the catalog filtering carefully |
| Tool raises / throws on bad SKU | Should return `"NOT_FOUND: <sku>"` string, never raise/throw (see `zavashop-context`) |
| C#: `NU1102` on restore | Forgot `--prerelease`; preview versions live on the prerelease channel |
| C#: tool schema missing fields | Add `[Description("...")]` to each parameter so `AIFunctionFactory.Create` emits a useful schema |

Done? → [Lab 3 — MCP](../lab-03-mcp/README.md)
