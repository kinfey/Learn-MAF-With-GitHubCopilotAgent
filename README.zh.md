# ZavaShop Coding Agents 工作坊
### Microsoft Agent Framework + GitHub Copilot SDK · **Python 与 C# (.NET 10)** — 由 GitHub Copilot Coding Agent（GPT-5.5）驱动

> **学习目标。** 这门工作坊以实战方式带你掌握 **Microsoft Agent Framework（MAF）**。**GitHub Copilot SDK**（Python 位置使用 `GitHubCopilotAgent`，.NET 位置使用 `CopilotClient.AsAIAgent`）作为具体的 Agent 运行时 — 不需要 API key、不需要部署模型 — 让你专注在 MAF 概念本身。**GitHub Copilot Coding Agent** 负责把代码写出来，让你始终扮演*架构师*的角色：设计与评审，而不是当打字员。每个实验都引入 MAF 的一个切片，用 SDK 实现它，由 Coding Agent 交付它。
>
> **一个工作坊，两种语言。** 每个实验都可以选 **Python** 或 **C# (.NET 10)** 任一语言完成 — 模型后端、custom agent、PROMPT.md 验收标准、MAF 概念都完全一致。每个 lab 的 `PROMPT.md` 携带一个 `target_language` 指令（`python` / `csharp` / `both`），告诉 Coding Agent 应该交付哪一栈。

> **实验运作方式。** 每个实验你只需要把一个 **custom agent（可复用的角色，同时会 Python 和 C#）** 指派给一份 **PROMPT.md（具体交付物）**。GitHub Copilot Coding Agent（运行在 GPT-5.5）会接手 — 背后是预装的 Microsoft Agent Framework skill（每种语言一套）作为 API 参考。

> **参考文档**：[About custom agents](https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/cloud-agent/about-custom-agents) · [Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)

---

## ZavaShop 故事

ZavaShop 是一家虚构的全球美妆与生活方式品牌零售商。公司分为两半：

- **零售（Retail）** — 顾客浏览、咨询、下单、跟踪发货。前线坐席需要产品知识、实时库存以及订单系统访问能力。
- **供应链（Supply Chain）** — 采购员预测需求、向供应商下采购单、把库存在五个仓库之间调配，并与零售侧对账。

在 5 个实验中，你将以 ZavaShop 为载体 **学习 Microsoft Agent Framework**，用你选择的 **Python** 或 **C# (.NET 10)** 实现两侧业务的自动化 — **GitHub Copilot SDK** 作为 Agent 运行时，**由你指挥 GitHub Copilot Coding Agent 完成编码**。

---

## 工作坊议程（5 个实验）

| # | 实验 | 学到的 MAF 概念 | 构建方式 | 产出（Python 和/或 C#） |
| --- | --- | --- | --- | --- |
| 1 | [基础知识 — Fundamentals](lab-01-fundamentals/README.zh.md) | Agent 运行时模型、`Agent` 基类抽象 | 手写（1 个 Python 脚本 + 1 个 C# 控制台项目） | 一个 "Hello, ZavaShop" 的 Copilot 后端 Agent |
| 2 | [单 Agent — Product Advisor](lab-02-single-agent/README.zh.md) | 函数工具、`AgentSession`、流式回复 | Coding Agent + `zava-single-agent-builder` | 一个基于 Zava 商品目录的问答 Agent |
| 3 | [MCP — 库存服务](lab-03-mcp/README.zh.md) | Local MCP 工具、工具审批（HITL） | Coding Agent + `zava-mcp-integrator` | 能跨仓库实时查询库存的 Agent |
| 4 | [多 Agent 工作流 — 零售 & 供应链](lab-04-multi-agent-workflow/README.zh.md) | Workflows：executors、edges、Sequential / Concurrent / Handoff | Coding Agent + `zava-workflow-architect` | 两条端到端的零售与供应链工作流 |
| 5 | [AGUI — 托管 Coding Agent UI](lab-05-agui/README.zh.md) | AG-UI 集成、混合工具执行 | Coding Agent + `zava-agui-engineer` | 可供 Web 流式消费的零售工作流前台 |

每个实验的代码相互独立，但概念上层层递进。**MAF 概念** 是你带走的知识；**构建方式** 是载体。每个实验可以独立选 Python 或 C# — 不要求全程坐定一栈。

---

## Microsoft Agent Framework 概念地图

每个实验都锚定在 [Microsoft Agent Framework](https://learn.microsoft.com/zh-cn/agent-framework/) 的一个独立概念切片上。顺序跟官方文档保持一致：先 **agents**，再 **workflows**，最后 **integrations**。每份 lab README 开头都有一张「本实验涉及的 Microsoft Agent Framework 概念」表格 — 在指派 custom agent 之前先看一眼，你就知道 Coding Agent 接下来要练哪一块 MAF 表面。

| Lab | 本 lab 引入的 MAF 概念 | Microsoft Learn |
| --- | --- | --- |
| 1 | Agent 运行时执行模型 · `Agent` 基类抽象 · Agent vs Workflow | [Overview](https://learn.microsoft.com/zh-cn/agent-framework/overview/) · [Agent types](https://learn.microsoft.com/zh-cn/agent-framework/agents/) |
| 2 | **函数工具（Function Tools）** · **`AgentSession`**（多轮） · 流式回复 | [Tools](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/) · [Session](https://learn.microsoft.com/zh-cn/agent-framework/agents/conversations/session) |
| 3 | **Local MCP Tools** · **工具审批（HITL）** · 函数工具与 MCP 工具共存 | [Tools Overview](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/) |
| 4 | **Workflows**：Executors · Edges · WorkflowBuilder · Sequential / Concurrent / Handoff · Agent-as-Executor | [Workflows](https://learn.microsoft.com/zh-cn/agent-framework/workflows/) · [Executors](https://learn.microsoft.com/zh-cn/agent-framework/workflows/executors) · [Edges](https://learn.microsoft.com/zh-cn/agent-framework/workflows/edges) |
| 5 | **AG-UI 集成** · `workflow_factory` 线程状态 · **混合工具执行**（服务端 + 客户端） | [Integrations](https://learn.microsoft.com/zh-cn/agent-framework/integrations/) |

> MAF 的两大能力——**Agents**（LLM 驱动、动态）和 **Workflows**（图驱动、显式）——在 Lab 1 介绍，Lab 2/3 践行 agents，Lab 4 践行 workflows，Lab 5 通过 AG-UI 把两者结合。

---

## 谁在写代码：Custom Agents + Skills + Prompts

本工作坊组合了 GitHub Copilot 的三种定制机制：

### 1. Custom Agents（可复用的角色）

定义在 [`.github/agents/`](.github/agents/README.md)。每个 profile 描述一个专类角色 — 包含职责范围、编码约定、读哪些 skill — 但 **不包含** 具体实验的任务。**每份 profile 同时包含 Python 和 C# (.NET) 两个小节**，被指派的 coding agent 只会读与 PROMPT.md `target_language` 指令匹配的那一段。

| Custom Agent | Lab | 角色 |
| --- | --- | --- |
| [`zava-single-agent-builder`](.github/agents/zava-single-agent-builder.md) | 2 | 一个 Copilot 后端 Agent + 函数工具（Python `@tool` / C# `AIFunctionFactory.Create`） |
| [`zava-mcp-integrator`](.github/agents/zava-mcp-integrator.md) | 3 | MCP 服务器（`FastMCP` / `ModelContextProtocol`）+ 连接它的 Agent |
| [`zava-workflow-architect`](.github/agents/zava-workflow-architect.md) | 4 | MAF Workflow：executor / edge / 编排（Python `@executor` / C# `Executor<TIn,TOut>`） |
| [`zava-agui-engineer`](.github/agents/zava-agui-engineer.md) | 5 | AG-UI 服务端 + 客户端（FastAPI / ASP.NET Core） |

### 2. Skills（API 参考）

定义在 [`.github/skills/`](.github/skills/README.md)。每个 custom agent 声明它要读哪些 skill — Copilot 只加载与语言匹配的 `-py` 或 `-csharp` 变体。

| 技能 | 教 Copilot 怎么做… |
| --- | --- |
| [`agent-framework-githubcopilot-py`](.github/skills/agent-framework-githubcopilot-py/SKILL.md) | 在 Python 中构建 `GitHubCopilotAgent`、管理会话、权限、MCP 服务器 |
| [`agent-framework-workflows-py`](.github/skills/agent-framework-workflows-py/SKILL.md) | 在 Python 中构建 MAF Workflow：executor、edge、编排、HITL |
| [`agent-framework-agui-py`](.github/skills/agent-framework-agui-py/SKILL.md) | 在 Python 中通过 AG-UI HTTP/SSE 托管 Agent/Workflow，并构建客户端 |
| [`agent-framework-githubcopilot-csharp`](.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) | 在 .NET 中通过 `CopilotClient.AsAIAgent` 构建 Copilot 后端 Agent、会话、MCP、函数工具 |
| [`agent-framework-workflows-csharp`](.github/skills/agent-framework-workflows-csharp/SKILL.md) | 在 .NET 中构建 MAF Workflow：`WorkflowBuilder`、`Executor<TIn,TOut>`、扣分/汇聚、流式 |
| [`agent-framework-agui-csharp`](.github/skills/agent-framework-agui-csharp/SKILL.md) | 在 ASP.NET Core 中通过 `MapAGUI` 托管 Agent，用 `AGUIChatClient` 消费，前端工具 |
| [`zavashop-context`](.github/skills/zavashop-context/SKILL.md) | 提供商品目录、仓库地图、订单 schema（语言中立） |

### 3. 任务 Prompts（每个实验的交付物）

每个实验都有一份小的 [`PROMPT.md`](lab-02-single-agent/PROMPT.md)，指明要指派哪个 custom agent、声明 `target_language`（`python` / `csharp` / `both`）并列出交付物 + 验收标准。Prompt 本身 **不重复** 编码约定—那些住在 agent profile 中。

### 实验是这样跑的（端到端）

```
1. 读 lab-NN/README.zh.md                  →  故事、目标、架构（Python + C# 双路讲解）
2. 打开 lab-NN/PROMPT.md                    →  复制全部内容
     ▸ 第一行指派 custom agent
     ▸ target_language 指令选 Python / C# / both
3. 在你 fork 里开 Issue 或 @copilot 评论    →  粘贴 prompt
4. Coding Agent（GPT-5.5）：
     a. 加载 .github/copilot-instructions.md   （仓库默认规则，双语言）
     b. 加载被指派的 custom agent profile      （角色约定）
     c. 只加载与语言匹配的 skill（-py 或 -csharp）
     d. 在 lab-NN/ 里生成代码（Python 文件放 lab 根、C# 文件放 lab-NN/csharp/）
     e. 开 PR
5. 你 review PR，本地跑 verify.py（Python）和/或 dotnet run --project ./csharp/verify（C#），合并
```

所有生成都使用 **GPT-5.5**（Python 和 C# 同一个后端模型），在 Lab 1 中配置一次即可。

---

## 前置条件

开始之前你需要：

- **GitHub 账号**，开通 **Copilot Pro+ / Business / Enterprise**（可使用 Coding Agent）
- **GitHub Copilot CLI**，已安装并完成认证（`copilot auth`）— Lab 1 会做校验
- **Python 路线**：Python 3.10+，配 `uv`（或 `pip`）
- **C# 路线**：**.NET 10 SDK**
- **Node.js 18+**（Lab 3 某些 MCP 服务器会用到）
- 本工作坊仓库的 **Fork**（Coding Agent 只能在你拥有的仓库上工作）

完整步骤见 [SETUP.md](SETUP.md)。

---

## 仓库结构

```
zavashop-maf-ghc-workshop/
├── README.md                        # 英文入口
├── README.zh.md                     # ← 你正在看
├── SETUP.md                         # 环境 + Copilot Coding Agent 配置（Python + .NET）
├── .github/
│   ├── copilot-instructions.md      # 注入到每次 Coding Agent 任务的仓库级指令（双语言）
│   ├── agents/                      # Custom agents（每份 profile 同时包含 Python 和 C# 两个节）
│   │   ├── zava-single-agent-builder.md
│   │   ├── zava-mcp-integrator.md
│   │   ├── zava-workflow-architect.md
│   │   └── zava-agui-engineer.md
│   └── skills/                      # 技能（API 参考，按需加载）
│       ├── agent-framework-githubcopilot-py/
│       ├── agent-framework-workflows-py/
│       ├── agent-framework-agui-py/
│       ├── agent-framework-githubcopilot-csharp/
│       ├── agent-framework-workflows-csharp/
│       ├── agent-framework-agui-csharp/
│       └── zavashop-context/
├── data/                            # 共享样本数据 — Python 与 C# 都读同一份 JSON
│   ├── zava_catalog.json
│   ├── zava_warehouses.json
│   └── zava_orders.sample.json
├── lab-01-fundamentals/             # 环境 + verify（不调用 Coding Agent）
│   ├── verify.py                    # Python 烟雾测试
│   └── csharp/HelloZava/            # C# 烟雾测试（.csproj + Program.cs）
├── lab-02-single-agent/             # README + PROMPT → zava-single-agent-builder
│   └── csharp/                      # target_language=csharp 时的 C# 产出
├── lab-03-mcp/                      # README + PROMPT → zava-mcp-integrator
├── lab-04-multi-agent-workflow/     # README + PROMPT → zava-workflow-architect
└── lab-05-agui/                     # README + PROMPT → zava-agui-engineer
```

---

## 全工作坊统一约定

- **Python 包名** — `agent-framework-github-copilot`、`agent-framework-core`、`agent-framework-ag-ui`，以及 MCP 服务器用的 `mcp`。
- **Python 导入** — `from agent_framework.github import GitHubCopilotAgent`、`from agent_framework import Agent, Workflow, WorkflowBuilder, tool, executor`、`from agent_framework.ag_ui import ...`。
- **.NET NuGet 包**（全部使用 `--prerelease`）— `GitHub.Copilot.SDK`、`Microsoft.Agents.AI`、`Microsoft.Agents.AI.GitHub.Copilot`、`Microsoft.Agents.AI.Workflows`、`Microsoft.Agents.AI.AGUI`、`Microsoft.Agents.AI.Hosting.AGUI.AspNetCore`、`Microsoft.Extensions.AI`、`ModelContextProtocol`。
- **.NET 项目 SDK** — 控制台/类库用 `Microsoft.NET.Sdk`；AG-UI 服务端与 MCP HTTP 服务端用 `Microsoft.NET.Sdk.Web`。目标框架 `net10.0`，`Nullable=enable`，`ImplicitUsings=enable`。
- **模型** — `GITHUB_COPILOT_MODEL=gpt-5.5`（写在 `.env` 里，两路 SDK 都会读取）。
- **业务数据** — 每个实验的工具都从 `data/zava_*.json` 读取。**不要改动数据文件**，工具要去适配 schema。Python 和 C# 读同一份 JSON。
- **编码风格** — async 优先。Python：`async with agent:` / `async with client:`。C#：`await using CopilotClient ...` / `await using StreamingRun ...`。
- **验收** — 每个实验的 README 末尾都有 checklist。Coding Agent 要用 `verify.py`（Python）或 `dotnet run --project ./csharp/verify`（C#）自检，你在 PR review 里把关。

---

## 如何与 Copilot Coding Agent 配合使用

1. **Fork** 本仓库。Coding Agent 只能在你自己的仓库上工作。
2. 在 fork 上 **启用 Copilot Coding Agent**：仓库 Settings → Code & automation → Copilot → 启用。
3. 把 **模型设为 GPT-5.5**（在 Copilot 设置里）。
4. **每个实验**（从 Lab 2 开始），新开一个 Issue 或 `@copilot` 评论，粘贴 `lab-NN/PROMPT.md` 的内容。首行指派 custom agent；`target_language` 指令选 Python 或 C#。
5. **Review** Coding Agent 开的 PR。本地跑 `python verify.py`（Python）和/或 `dotnet run --project ./csharp/verify`（C#），对照验收标准，再合并。

> 为什么拆成 custom agents + skills + prompts 三层？三个原因：
> 1. **可复用** — 像 `zava-workflow-architect` 这样的角色能应用于 *任何* workflow 任务、*任何* 语言，不仅限 Lab 4。
> 2. **职责聪焦** — Copilot 只加载被指派 agent 需要的 skill（且只加载 `-py` 或 `-csharp` 变体），上下文窗口不浪费。
> 3. **学习清晰度** — 你会看清楚什么东西属于 *角色*（HOW）、什么属于 *skill*（API）、什么属于 *prompt*（WHAT + 哪种语言）、什么属于 *仓库指令*（默认值）。这些是 Coding Agent 定制的四个机制。

如果你想直接看代码长什么样，每份 PROMPT.md 也都是一份适用于任意 Agent（Claude Code、Cursor、你自己的 MAF 编排器）的合法任务描述 — 只需去掉 `@copilot assign` 那一行，把剩下的当常规 prompt 提交即可。

---

## 卡住了？

- **Lab 1** 覆盖了最常见的踩坑（CLI 认证、技能发现、模型选择）。
- `.github/skills/` 下的技能文件就是你的 API 参考手册 — Coding Agent 输出里出现你看不懂的 API 时随时翻。
- 每个实验的 README 底部都有 "常见错误（Common mistakes）" 小节。

开搞 → [Lab 1 — 基础知识](lab-01-fundamentals/README.zh.md)。
