# Lab 1 — 基础知识（Fundamentals）

> 预计用时：30 分钟。**本实验你不需要调用 Coding Agent** — 你只需搭好环境并在你选择的语言中跑一个烟雾测试，确认所有东西都通了。
>
> **学习目标**：第一次接触 **MAF 的 Agent 运行时模型** — 在 **Python** 或 **C# (.NET 10)** 上跟你的首个 Copilot 后端 Agent 见个面。下文会并列走过两个语言的实现，你可以选一种或两种都跑。从 Lab 2 开始，GitHub Copilot SDK 是运行时，Coding Agent 写代码；两者都依赖本实验跑通。

## ZavaShop 故事

在为零售和供应链拼装真正的 Agent 之前，你本机的工具链得先能跟 GitHub Copilot 对话。本实验里你会启动一个最小的 Copilot 后端 Agent，让它自我介绍为 ZavaShop 的 AI 助手 — 运行在 **GPT-5.5** 上。

只要本实验能跑通，后面四个实验也都能跑。如果跑不通，请先在这里修好再继续。

## 本实验涉及的 Microsoft Agent Framework 概念

Lab 1 锚定在后面所有实验都要依赖的基础心智模型。

| 概念 | 含义 | Microsoft Learn |
| --- | --- | --- |
| **Agent vs Workflow** | *Agent* 由 LLM 驱动，运行时自主决定步骤；*Workflow* 是显式定义的步骤图。Lab 2–3 构建 Agent，Lab 4 构建 Workflow，Lab 5 把两者都通过 UI 端点托管。 | [Overview](https://learn.microsoft.com/zh-cn/agent-framework/overview/) |
| **默认 Agent 运行时执行模型** | 标准循环：用户输入 → 模型推理 →（可选）工具调用 → 回复。`GitHubCopilotAgent`（Python）与 `CopilotClient.AsAIAgent`（.NET）是同一个模型的两种具体实现 — 同一个循环、两种语言表达。 | [Agent types](https://learn.microsoft.com/zh-cn/agent-framework/agents/) |
| **`Agent` 基类抽象** | 所有 MAF Agent 共享同一个基类（Python `Agent` / .NET `AIAgent`）— 这让多 Agent 编排、Workflow、AG-UI 都能一视同仁地使用它们。Lab 4、5 会看到回报。 | [Agent types](https://learn.microsoft.com/zh-cn/agent-framework/agents/) |

## 你会学到什么

- GitHub Copilot SDK 如何把本机 `copilot` CLI 接入运行时 — Python 走 `GitHubCopilotAgent`，.NET 走 `CopilotClient.AsAIAgent`。
- `GITHUB_COPILOT_MODEL` 如何把两条路线都钉死在 GPT-5.5。
- `async with agent:`（Python）与 `await using CopilotClient`（.NET）如何管理 CLI 子进程生命周期。
- `.github/skills/` 如何驱动 Labs 2–5 的 GitHub Copilot Coding Agent — 每个 MAF 技能都有 `-py` 和 `-csharp` 两个变体。

## 前置条件

你已经完成 [SETUP.md](../SETUP.md)。具体来说：

- `copilot auth` 已经成功。
- `python -c "import agent_framework.github"` 不报错。
- `.env` 里有 `GITHUB_COPILOT_MODEL=gpt-5.5`。

## 概念（看一遍即可）

```
┌──────────────────────────┐  spawn  ┌──────────────────────────┐
│  Python: GitHubCopilot   │ ──────► │  copilot CLI（子进程）   │
│  Agent(...)              │ ◄────── │  GPT-5.5 走 GH Copilot    │
│  - tools（Python 函数）  │  stdio  │  - 会话、MCP、权限       │
│  - 权限处理器             │         │                          │
└──────────────────────────┘         └──────────────────────────┘
```

- **你写 Python**。SDK 在子进程里跑 `copilot` CLI，并把事件流过来。
- **不用 Azure key，不用 OpenAI key。** 认证由 `copilot auth` 一次性完成，后续复用。
- **Async 优先。** 用 `asyncio.run(main())` 和 `async with agent:`。

完整 API 都在 [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) 里。现在打开它，浏览一下目录 — Labs 2、3 会反复回来翻。

## 你要做什么

1. 把本 README 看完。
2. 在你选择的语言中跑烟雾测试（也可两个都跑）：
   - **Python**：`verify.py` 会构造一个迷你 `GitHubCopilotAgent`，唯一职责就是用 ZavaShop 的身份打招呼。
   - **C# (.NET)**：`csharp/HelloZava/Program.cs` 用 `CopilotClient.AsAIAgent` 做同样的事。
3. 确认 Agent 用的是 **GPT-5.5**（脚本开头会打印当前模型）。
4. 在你的 fork 上启用 GitHub Copilot Coding Agent（Labs 2–5 一次性配置）。

### Python 路线

```bash
cd lab-01-fundamentals
python verify.py
```

预期输出（节选）：

```
[ZavaShop AI Bootstrap]
  Model:    gpt-5.5
  CLI:      copilot
  Skills:   7 found under ../.github/skills/

Agent  : Hello! I am the ZavaShop AI assistant, powered by GPT-5.5 …
        We carry beauty and lifestyle products across five regional warehouses …

[OK] Lab 1 complete. Proceed to Lab 2.
```

### C# / .NET 路线

Lab 附带了一个最小控制台工程 `lab-01-fundamentals/csharp/HelloZava/`：

```
lab-01-fundamentals/csharp/HelloZava/
├── HelloZava.csproj           # Microsoft.NET.Sdk，net10.0，引 GitHub.Copilot.SDK + Microsoft.Agents.AI.GitHub.Copilot
└── Program.cs                 # 代码如下
```

`HelloZava.csproj`：

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

`Program.cs`：

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

跑一下：

```bash
cd lab-01-fundamentals/csharp/HelloZava
dotnet run
```

预期输出与 Python 一致 — 一个由 Copilot 后端 Agent 流式输出的自我介绍。

## 验收标准

- [ ] `verify.py`（Python）**或** `dotnet run --project csharp/HelloZava`（.NET）跑完不抛 traceback。
- [ ] 打印的模型是 `gpt-5.5`。
- [ ] 流式响应里提到了 ZavaShop 和至少一个产品品类。
- [ ] `verify.py` 里的 `.github/skills/` 发现列出了 **7 个** 技能（3 个 Python MAF 技能 + 3 个 C# MAF 技能 + `zavashop-context`）。
- [ ] 你已在 fork 上启用 GitHub Copilot Coding Agent，并把模型设为 GPT-5.5（UI 操作，不做自动校验）。

## 常见错误

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ModuleNotFoundError: agent_framework.github` | Python SDK 没装（或装的时候没加 `--pre`） | `uv pip install "agent-framework-github-copilot --pre"` |
| `error NU1102: Unable to find package Microsoft.Agents.AI...` | .NET 预览包需要 `--prerelease` | 重跑 `dotnet add package <name> --prerelease`；或编辑完 `.csproj` 后跑 `dotnet restore` |
| `error NETSDK1045: The current .NET SDK does not support targeting net10.0` | .NET 10 SDK 未安装 | 装 .NET 10 SDK（见 SETUP.md §1） |
| 在 Python/.NET 里抛 `copilot: command not found` | `copilot` CLI 不在 `PATH` | 重装 GH Copilot CLI；用 `which copilot` 验证 |
| 模型打印成 `gpt-5`（不是 `gpt-5.5`） | `.env` 没加载 | Python：确认装了 `python-dotenv` 且脚本调用 `load_dotenv()`。.NET：在 shell 里先 `export GITHUB_COPILOT_MODEL=gpt-5.5` 再 `dotnet run`，或用 `DotNetEnv` 包 |
| 第一次跑卡住没输出 | 这台机器没跑过 `copilot auth` | 跑一下 `copilot auth` 再重试 |

Lab 1 绿了就继续。→ [Lab 2 — 单 Agent](../lab-02-single-agent/README.zh.md)
