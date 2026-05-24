# Workshop Setup

> Complete this once before Lab 1. Estimated time: 20–30 minutes (covers both **Python** and **.NET 10**).
>
> Every lab in this workshop can be completed in **Python** or **C# (.NET 10)** — install whichever stack you plan to use (or both). The model backbone (GitHub Copilot CLI + GPT-5.5) is identical for both languages.

## 1. Tooling

| Tool | Version | Why |
| --- | --- | --- |
| Python | 3.10 or newer | Python track of every lab |
| `uv` (or `pip`) | latest | Python package install |
| .NET SDK | **10.0 or newer** | C# track of every lab |
| Node.js | 18+ | MCP servers via `npx` (Lab 3) |
| GitHub Copilot CLI | latest | Powers `GitHubCopilotAgent` (Python) and `CopilotClient` (.NET) |
| GitHub CLI (`gh`) | 2.90+ | Optional, for forking / PRs |

Install on macOS:

```bash
# Python via uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# .NET 10 SDK
brew install --cask dotnet-sdk         # or download from https://dotnet.microsoft.com/download/dotnet/10.0
dotnet --version                       # expect 10.x

# Node
brew install node

# GitHub Copilot CLI (Homebrew formula; also available via npm: npm install -g @github/copilot)
brew install copilot-cli
copilot                               # launch interactive session; run /login on first start

# GitHub CLI (optional)
brew install gh
gh auth login
```

On Linux / Windows, follow each tool's official installer. The cross-platform install scripts:

```bash
curl -fsSL https://gh.io/copilot-install | bash      # GitHub Copilot CLI
curl -fsSL https://dot.net/v1/dotnet-install.sh | bash -s -- --channel 10.0  # .NET 10
```

## 2. Fork & clone the workshop

```bash
gh repo fork microsoft/zavashop-maf-ghc-workshop --clone --remote
cd zavashop-maf-ghc-workshop
```

(or clone whichever fork your instructor pointed you at.)

## 3. Python environment (skip if you only plan to use the C# track)

```bash
uv venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

uv pip install \
  "agent-framework-github-copilot --pre" \
  "agent-framework-core --pre" \
  "agent-framework-ag-ui --pre" \
  "mcp[cli]" \
  fastapi uvicorn httpx python-dotenv
```

If `uv` isn't available, swap `uv pip` for `pip`.

## 3b. .NET environment (skip if you only plan to use the Python track)

The MAF NuGet packages are currently in preview, so every `dotnet add package` in this workshop is invoked with `--prerelease`. To make that the default, drop a `nuget.config` at the repo root (already gitignored):

```bash
dotnet new console -n _smoketest -o /tmp/_smoketest && rm -rf /tmp/_smoketest   # quick sanity check

# Sanity: create + restore a throwaway project that uses every MAF .NET package the labs touch.
mkdir -p /tmp/maf-smoketest && cd /tmp/maf-smoketest
dotnet new console
dotnet add package GitHub.Copilot.SDK --prerelease
dotnet add package Microsoft.Agents.AI --prerelease
dotnet add package Microsoft.Agents.AI.GitHub.Copilot --prerelease
dotnet add package Microsoft.Agents.AI.Workflows --prerelease
dotnet add package Microsoft.Agents.AI.AGUI --prerelease
dotnet add package Microsoft.Agents.AI.Hosting.AGUI.AspNetCore --prerelease
dotnet add package Microsoft.Extensions.AI --prerelease
dotnet add package ModelContextProtocol --prerelease
dotnet restore && cd - && rm -rf /tmp/maf-smoketest
```

If the restore prints "Unable to find package", make sure the public NuGet feed `https://api.nuget.org/v3/index.json` is configured (`dotnet nuget list source`) and that `--prerelease` is on the `add package` calls.

## 4. Configure the model — **GPT-5.5**

Create a `.env` file at the workshop root:

```bash
cat > .env <<'EOF'
GITHUB_COPILOT_MODEL=gpt-5.5
GITHUB_COPILOT_TIMEOUT=120
GITHUB_COPILOT_LOG_LEVEL=info
AGUI_SERVER_URL=http://127.0.0.1:5100/
EOF
```

The Microsoft Agent Framework GitHub Copilot SDK reads `GITHUB_COPILOT_MODEL` to pick the model. Every agent you build in this workshop will run on GPT-5.5.

Pick / verify the model inside the Copilot CLI:

```bash
copilot                    # launch the interactive session
> /model                   # slash command: lists available models, pick GPT-5.5
> /exit
```

You can also override per-invocation with the `--model` flag, e.g. `copilot --model gpt-5.5 -p "..."`. The default model is Claude Sonnet 4.5; for this workshop switch it to **GPT-5.5** (or the latest GPT-5 family model available to your account).

## 5. Verify GitHub Copilot Coding Agent

GitHub Copilot Coding Agent is a separate product from the local Copilot CLI. It's the **cloud agent** that opens PRs against your repo.

1. Go to your fork on github.com.
2. **Settings → Code & automation → Copilot → Coding Agent** → enable.
3. **Settings → Copilot → Model** → choose **GPT-5.5**.
4. Open the **Issues** tab and verify you can assign an issue to `@copilot`.

If you only see GPT-4o / GPT-5, your account doesn't yet have GPT-5.5 — pick the latest available and substitute in the labs.

## 6. Verify the skills are visible

The Coding Agent picks up skills from `.github/skills/`. The workshop ships **seven** (four Python + three C# + one domain skill):

```bash
ls .github/skills/
# agent-framework-agui-csharp/
# agent-framework-agui-py/
# agent-framework-githubcopilot-csharp/
# agent-framework-githubcopilot-py/
# agent-framework-workflows-csharp/
# agent-framework-workflows-py/
# zavashop-context/
```

Each contains a `SKILL.md`. The Coding Agent decides when to load them based on the `description` frontmatter — and it picks the `-py` or `-csharp` variant based on the `target_language` directive in each lab's `PROMPT.md`. You do not need to "activate" them manually.

Optional — sanity-check from inside the Copilot CLI (interactive session):

```
copilot
> /skills                  # lists every skill the CLI discovered (repo + user level)
```

## 7. Verify your local agent works

Run the Lab 1 verification script(s) to confirm CLI + Python and/or .NET wiring:

```bash
# Python track
python lab-01-fundamentals/verify.py

# C# track (run the project that the lab provides; if you haven't completed Lab 1 yet, skip)
dotnet run --project lab-01-fundamentals/csharp/HelloZava
```

Expected output: a streamed message from a Copilot-backed agent introducing itself as the ZavaShop AI assistant. If anything goes wrong, the script prints diagnostic hints — read them carefully and re-run.

## 8. Optional — pre-load test data

Shared data lives in `data/`. The files are tiny and safe to read; no setup is needed. If you'd like to inspect:

```bash
jq '.products | length' data/zava_catalog.json
jq '.warehouses | length' data/zava_warehouses.json
```

## Common setup issues

| Symptom | Fix |
| --- | --- |
| `copilot: command not found` | Re-install GitHub Copilot CLI (`brew install copilot-cli` or `npm install -g @github/copilot`); ensure it's on `PATH`. |
| Auth fails on first launch | Inside the CLI run `/login` again, or set a fine-grained PAT with the "Copilot Requests" permission and export it as `GH_TOKEN`. |
| Model not listed under `/model` | Update Copilot CLI: `brew upgrade copilot-cli` (or `npm update -g @github/copilot`). |
| `ModuleNotFoundError: agent_framework.github` (Python) | Use the `--pre` flag; the package is still in preview. |
| `error NU1102: Unable to find package Microsoft.Agents.AI...` (.NET) | Re-run `dotnet add package <name> --prerelease`. The MAF .NET packages are preview-only. |
| `dotnet: command not found` or `error NETSDK1045: requires net10.0` | Install .NET 10 SDK (`brew install --cask dotnet-sdk` or the official installer). |
| Coding Agent never responds on the issue | Confirm Coding Agent is enabled on the fork (Settings → Copilot). |
| PRs open but use the wrong model | Check Settings → Copilot → Model. Re-trigger by closing/reopening the issue. |
| PR ships Python when you asked for C# (or vice versa) | Check the `target_language:` directive in the lab's `PROMPT.md`. |

Setup done. → [Start Lab 1](lab-01-fundamentals/README.md)
