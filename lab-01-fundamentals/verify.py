"""Lab 1 verification — bring up a minimal ZavaShop GitHubCopilotAgent on GPT-5.5.

Runs an agent that introduces itself as the ZavaShop AI assistant, streams the
response token-by-token, and asserts that the configured model is gpt-5.5.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the workshop root (one directory up from this lab).
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MODEL = os.environ.get("GITHUB_COPILOT_MODEL", "")
SKILLS_DIR = ROOT / ".github" / "skills"


def banner() -> None:
    skills = sorted(p.name for p in SKILLS_DIR.glob("*") if (p / "SKILL.md").exists())
    print("[ZavaShop AI Bootstrap]")
    print(f"  Model:    {MODEL or '(unset!)'}")
    print(f"  CLI:      {os.environ.get('GITHUB_COPILOT_CLI_PATH', 'copilot')}")
    print(f"  Skills:   {len(skills)} found under .github/skills/")
    for name in skills:
        print(f"    - {name}")
    print()


def assert_environment() -> None:
    problems: list[str] = []
    if MODEL != "gpt-5.5":
        problems.append(
            f"GITHUB_COPILOT_MODEL is '{MODEL}', expected 'gpt-5.5'. "
            "Edit the workshop .env file."
        )
    if not SKILLS_DIR.exists():
        problems.append(f"Skills directory missing: {SKILLS_DIR}")
    if problems:
        print("[FAIL] Pre-flight checks failed:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(2)


async def run_hello_agent() -> None:
    # Imported lazily so import errors surface after the banner.
    from agent_framework.github import GitHubCopilotAgent

    agent = GitHubCopilotAgent(
        instructions=(
            "You are the ZavaShop AI assistant. "
            "Introduce yourself in two short sentences. Mention that ZavaShop "
            "sells beauty and lifestyle products across five regional "
            "warehouses, and that you are powered by GitHub Copilot GPT-5.5."
        ),
    )

    async with agent:
        print("Agent  : ", end="", flush=True)
        async for chunk in agent.run("Please introduce yourself.", stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print("\n")


async def main() -> None:
    banner()
    assert_environment()
    try:
        await run_hello_agent()
    except ModuleNotFoundError as e:
        print(f"[FAIL] Missing dependency: {e}")
        print("  Hint: uv pip install 'agent-framework-github-copilot --pre'")
        sys.exit(3)
    except FileNotFoundError as e:
        print(f"[FAIL] copilot CLI not found: {e}")
        print("  Hint: install GitHub Copilot CLI and run 'copilot auth'.")
        sys.exit(4)

    print("[OK] Lab 1 complete. Proceed to Lab 2.")


if __name__ == "__main__":
    asyncio.run(main())
