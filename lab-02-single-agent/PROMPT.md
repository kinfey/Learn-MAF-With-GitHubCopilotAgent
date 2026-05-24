# Lab 2 — Task Prompt

> **Paste the content of this file into a GitHub Issue (or `@copilot` comment) in your fork to start the Coding Agent.**

## Assignment

Assign this task to the **`zava-single-agent-builder`** custom agent.

> @copilot assign zava-single-agent-builder to this task

The agent profile lives at [`.github/agents/zava-single-agent-builder.md`](../.github/agents/zava-single-agent-builder.md). It already knows the conventions, the canonical pattern (in **both** languages), and which skills to read. **Do not repeat that here.**

## Language Directive

```
target_language: both
```

Valid values: `python`, `csharp`, or `both`. Edit the line above before pasting into the issue.

- `python` → produce only the Python deliverables and read only `-py` skills.
- `csharp` → produce only the C# deliverables and read only `-csharp` skills.
- `both` → produce both deliverable trees; verify scripts must pass in both languages.

## Goal

Build the **ZavaShop Product Advisor**: a Copilot-backed agent with three function tools backed by `data/zava_catalog.json`, plus a verify script that runs three scripted turns. Python uses `GitHubCopilotAgent` + `@tool`; C# uses `CopilotClient.AsAIAgent` + `AIFunctionFactory.Create`.

## Deliverables (inside `lab-02-single-agent/`)

For `target_language: python` (or `both`):

- `requirements.txt` — only the packages this lab actually needs.
- `product_advisor.py` — the agent module exporting the three tools and a `build_agent()` factory (so Lab 3 can reuse the tools).
- `verify.py` — runs three turns in one session, asserts substrings, exits 0 on full pass.

For `target_language: csharp` (or `both`), under `lab-02-single-agent/csharp/`:

- `ProductAdvisor/ProductAdvisor.csproj` — `Microsoft.NET.Sdk`, `net10.0`, references `GitHub.Copilot.SDK`, `Microsoft.Agents.AI`, `Microsoft.Agents.AI.GitHub.Copilot`, `Microsoft.Extensions.AI` (all `--prerelease`).
- `ProductAdvisor/Program.cs` + `CatalogTools.cs` + `Models.cs` — catalog loaded once at startup; three tools exposed via `AIFunctionFactory.Create`; agent built via `client.AsAIAgent(ownsClient: true, name, instructions, tools)`.
- `Verify/Verify.csproj` + `Verify/Program.cs` — runs three turns in one `AgentSession` (from `await agent.CreateSessionAsync()`), asserts substrings, returns 0 on full pass. Final line: `[OK] Lab 2 complete.`

## Tool signatures (exactly these)

Python:

```python
@tool
def search_products(query: str, category: str | None = None, max_price_usd: float | None = None) -> list[dict]: ...

@tool
def get_product_details(sku: str) -> dict | str: ...   # returns "NOT_FOUND: <sku>" on miss

@tool
def recommend_alternatives(sku: str, max_results: int = 3) -> list[dict]: ...
```

C# (static methods on `CatalogTools`, each parameter decorated with `[Description(...)]`):

```csharp
public static IReadOnlyList<CatalogRow> SearchProducts(string query, string? category = null, double? maxPriceUsd = null);
public static object GetProductDetails(string sku);     // returns CatalogRow or string "NOT_FOUND: <sku>"
public static IReadOnlyList<CatalogRow> RecommendAlternatives(string sku, int maxResults = 3);
```

## Acceptance criteria (every item testable in the verify script)

1. Three tools exist with the signatures above; tools read only from `data/zava_catalog.json`. No hard-coded SKUs.
2. The agent is built once at module/program scope via a `build_agent()` factory (Python) or a single `client.AsAIAgent(...)` call in `Program.cs` (C#), and run inside `async with` / `await using`.
3. The verify script uses **one** session for all three turns (Python `agent.create_session()` / C# `await agent.CreateSessionAsync()`).
4. Turn 1: *"Do you sell a red matte lipstick under $30?"* → reply contains `LIP-001` **and** `$24`.
5. Turn 2: *"What's the difference between SKN-027 and SKN-030?"* → reply contains both SKUs **and** the words `night` and `vitamin C`.
6. Turn 3: *"Tell me an alternative to FRG-015 in a similar price range."* → reply contains `FRG-009`.
7. Verify script exits 0 on full pass, non-zero otherwise. Final line: `[OK] Lab 2 complete.`

## Verification command

Python:

```bash
cd lab-02-single-agent
uv pip install -r requirements.txt
python verify.py
```

C# / .NET:

```bash
cd lab-02-single-agent/csharp
dotnet run --project Verify
```

## PR checklist (paste into the PR body)

- [ ] `target_language` was honoured: only the language(s) listed above were touched.
- [ ] Each acceptance criterion mapped to a line in the verify script(s).
- [ ] No edits outside `lab-02-single-agent/`.
- [ ] Tools never raise/throw; they return `"NOT_FOUND: <sku>"` on misses.
- [ ] `gpt-5.5` is the model that ran (visible in the agent's first chunk or printed banner).
- [ ] Python deliverable present (when applicable): `requirements.txt`, `product_advisor.py`, `verify.py`.
- [ ] C# deliverable present (when applicable): `csharp/ProductAdvisor/*.csproj` + `Program.cs` + `Verify/*.csproj` + `Verify/Program.cs`.