# Lab 2 — 单 Agent：ZavaShop Product Advisor

> 预计用时：45 分钟。**你来指挥 Copilot Coding Agent — 你不亲自写代码。**
>
> **学习目标**：通过构建产品顾问，践行 MAF 的 **函数工具、会话、流式回复**。两条路线的运行时都是 GitHub Copilot SDK — Python 走 `GitHubCopilotAgent` + `@tool`，C# 走 `CopilotClient.AsAIAgent` + `AIFunctionFactory.Create` — Coding Agent 在你的指挥下，以 `target_language` 选定的语言完成实现。

## ZavaShop 故事

目前 ZavaShop 的客服聊天里约 60% 的产品问题用罐头回复糊弄过去了。零售团队想要一个 AI **Product Advisor**，能基于真实商品目录回答真问题：

> "你们有 30 美元以下的红色哑光口红吗？"  
> "SKN-027 和 SKN-030 有什么区别？"  
> "我是油皮 — 推荐什么粉底？"

你将把这个顾问构造成一个 `GitHubCopilotAgent`，配上三个函数工具，都从 `data/zava_catalog.json` 读取。

## 本实验涉及的 Microsoft Agent Framework 概念

| 概念 | 在代码中的体现 | Microsoft Learn |
| --- | --- | --- |
| **函数工具（Function Tools）** | 暴露给 LLM 的普通函数 — Python 用 `@tool` + Pydantic 类型；C# 用 `AIFunctionFactory.Create(myFn)` 读取 `[Description]` 特性。由 LLM 决定何时调用哪一个。 | [Tools Overview](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/) · [Function Tools](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/function-tools) |
| **Agent 会话** | 多轮复用的对话状态。Python：`agent.create_session()` + 每轮传 `session=session`。C#：`await agent.CreateSessionAsync()` 返回 `AgentSession`，传回去。同一个概念，两个接口。 | [Session](https://learn.microsoft.com/zh-cn/agent-framework/agents/conversations/session) |
| **流式回复** | 逐 token 流式输出。Python：`async for chunk in agent.run(..., stream=True)`。C#：`await foreach (var update in agent.RunStreamingAsync(...))`。 | [Agent types](https://learn.microsoft.com/zh-cn/agent-framework/agents/) |

## 运行本实验

本实验由一个 **custom Coding Agent** 驱动，不需要你手写 prompt。[`PROMPT.md`](PROMPT.md) 里的 `target_language` 指令决定 Coding Agent 交哪一栈。

1. 在你的 fork 里新开一个 Issue（或 `@copilot` 评论），**粘贴 [`PROMPT.md`](PROMPT.md) 的全部内容**。首行指派 custom agent；`target_language` 那行选 `python` / `csharp` / `both`。
2. Coding Agent 会：
   - 加载 [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md) profile — 里面同时包含 **Python 和 C#** 两个节，只读与 `target_language` 匹配的那一段。
   - 只读跟语言匹配的 skill（`agent-framework-githubcopilot-py` 或 `agent-framework-githubcopilot-csharp`）+ 共享的 `zavashop-context`。**不读** workflow / AG-UI skill。
   - 生成交付物 — Python 文件放 lab 根目录，C# 项目放 `csharp/`。
   - 开 PR。你 review，本地跑语言对应的 verify，合并。

| 层 | 角色 / API / 任务住哪里 |
| --- | --- |
| 角色（HOW） | [`.github/agents/zava-single-agent-builder.md`](../.github/agents/zava-single-agent-builder.md)（同时包含 Python 和 C# 两个节） |
| API 参考（Python） | [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md)、[`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) |
| API 参考（C#） | [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md)、[`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) |
| 任务（WHAT + 哪一栈） | [`PROMPT.md`](PROMPT.md) |

## 你会学到什么

- 用你选择的语言定义函数工具：Python `@tool` + Pydantic，或 C# `AIFunctionFactory.Create` 读 `[Description]`。
- 把工具接到 Copilot 后端 Agent，并流式输出回复。
- 用 `agent.create_session()`（Python）或 `await agent.CreateSessionAsync()`（C#）维护对话上下文。
- 即使没有工具被触发，Agent 的 *instructions* 也会塑造 LLM 的规划。

## Custom Agent + Skills（由 [`PROMPT.md`](PROMPT.md) 指定）

- **Custom agent**：[`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md) — 角色 profile 中同时包含 Python 和 C# 的范本代码。
- **Agent 会读的 skill**：与语言匹配的 MAF skill（`agent-framework-githubcopilot` 的 `-py` 或 `-csharp` 变体）+ [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md)（目录 schema、SKU 规则；语言中立）。

## 交付物

Coding Agent 会根据 `target_language` 在 `lab-02-single-agent/` 里产出下面之一；选 `both` 时两棵都生成。

### Python（`target_language: python`）

```
lab-02-single-agent/
├── README.md            （本文件 — 已存在）
├── PROMPT.md            （给 Copilot Coding Agent 的提示词 — 已存在）
├── requirements.txt
├── product_advisor.py   ← Agent 和它的工具
└── verify.py            ← 脚本化验收测试
```

### C# / .NET（`target_language: csharp`）

```
lab-02-single-agent/
└── csharp/
    ├── ProductAdvisor/
    │   ├── ProductAdvisor.csproj      # Microsoft.NET.Sdk, net10.0
    │   ├── Program.cs                  # CopilotClient + AsAIAgent + 3 个工具
    │   ├── CatalogTools.cs             # 带 [Description] 的静态方法
    │   └── Models.cs                   # 目录行的 record 类型
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                  # 三轮验收测试
```

`ProductAdvisor.csproj` 引用 `GitHub.Copilot.SDK`、`Microsoft.Agents.AI`、`Microsoft.Agents.AI.GitHub.Copilot`、`Microsoft.Extensions.AI`（全部 `--prerelease`）。三个工具是 `CatalogTools` 的静态方法，通过 `tools: [AIFunctionFactory.Create(CatalogTools.SearchProducts), AIFunctionFactory.Create(CatalogTools.GetProductDetails), AIFunctionFactory.Create(CatalogTools.RecommendAlternatives)]` 传给 `CopilotClient.AsAIAgent(...)`。范本代码见 [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md)。

## 验收标准

Coding Agent 必须满足下列每条。它生成的 verify 脚本（Python 的 `verify.py` 或 C# 的 `csharp/Verify/Program.cs`）必须用选定语言自动验证第 4–7 条。

1. 恰好 **三个** 函数工具（两种语言同型）：
   - `search_products` / `SearchProducts(query, category?, maxPriceUsd?)` 返回目录行列表。
   - `get_product_details` / `GetProductDetails(sku)` 返回行或 **字符串** `"NOT_FOUND: <sku>"`（遵循 `zavashop-context`）。
   - `recommend_alternatives` / `RecommendAlternatives(sku, maxResults=3)` 返回列表。
2. 工具只从 `data/zava_catalog.json` 读取。不允许硬编码 SKU。C# 中启动时一次反序列化（例如 `JsonSerializer.Deserialize` 成 `record CatalogRow(...)` 数组）。
3. Agent 在程序作用域构造一次。Python：`GitHubCopilotAgent(instructions=..., tools=[...])` 在 `async with` 内。C#：`await using CopilotClient` + `client.AsAIAgent(ownsClient: true, name, instructions, tools)`。
4. 多轮：同一个会话至少复用 3 轮。Python：同一个 `agent.create_session()`。C#：同一个 `AgentSession`（`await agent.CreateSessionAsync()`）。第二轮要引用第一轮建立的信息。
5. 脚本要处理 *"你们有 30 美元以下的红色哑光口红吗？"*，回答 **必须** 提到 `LIP-001` 和 `$24`。
6. 脚本要处理 *"SKN-027 和 SKN-030 有什么区别？"*，回答需提到两个 SKU、出现 *night*（对应 SKN-027）和 *vitamin C*（对应 SKN-030），大小写不敏感。
7. 脚本要处理 *"给我推荐一款和 FRG-015 价位相近的替代品。"*，回答必须提到 `FRG-009`。
8. verify 脚本三轮 substring 检查全通过时退出码 0；否则非 0。

## 运行

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

跑通后会按顺序打印三轮带标签的对话，最后输出 `[OK] Lab 2 complete.`

## 常见错误

| 现象 | 原因 |
| --- | --- |
| Agent 编出目录里没有的 SKU | 工具返回了空列表；instructions 没写"只能基于工具结果回答" |
| 第二轮丢上下文 | 每轮都新建 session — Python：传 `session=session`；C#：把 `session` 传给 `RunAsync` |
| `search_products` / `SearchProducts` 把所有商品都返回 | 过滤逻辑漏了 — 仔细读目录过滤代码 |
| 工具对错误 SKU 抛异常 | 应该返回 `"NOT_FOUND: <sku>"` 字符串，永远不要抛（见 `zavashop-context`） |
| C#：restore 报 `NU1102` | 忘了 `--prerelease`；预览版本在预览频道 |
| C#：工具 schema 缺字段 | 给每个参数加 `[Description("...")]`，让 `AIFunctionFactory.Create` 输出有用的 schema |

完成了？→ [Lab 3 — MCP](../lab-03-mcp/README.zh.md)
