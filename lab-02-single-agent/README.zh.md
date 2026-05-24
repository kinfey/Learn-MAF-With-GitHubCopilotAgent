# 实验 2 — 单 Agent：ZavaShop 产品顾问

> 预计耗时：45 分钟。**你的角色是驱动 Copilot Coding Agent —— 而不是亲手敲代码。**
>
> **学习目标**：通过构建一个产品顾问，练习 MAF 的**函数工具、会话与流式响应**。两种技术栈下,GitHub Copilot SDK 都担任运行时 —— Python 使用 `GitHubCopilotAgent` + `@tool`,C# 使用 `CopilotClient.AsAIAgent` + `AIFunctionFactory.Create` —— 由 Coding Agent 按照你通过 `target_language` 指定的语言完成实现。

## ZavaShop 业务背景

ZavaShop 当前面向客户的对话只有约 60% 的产品问题能用预设话术回答。零售团队希望上一个 AI **产品顾问**,能基于实时商品目录回答真实问题:

> "你们有没有 30 美元以下的红色哑光口红?"  
> "SKN-027 和 SKN-030 有什么区别?"  
> "我是油性皮肤 —— 推荐哪款粉底?"

你将把这位顾问构建成一个带有三个函数工具的 `GitHubCopilotAgent`,所有工具都从 `data/zava_catalog.json` 读取数据。

## 本实验涉及的 Microsoft Agent Framework 概念

| 概念 | 代码中的含义 | Microsoft Learn |
| --- | --- | --- |
| **函数工具 (Function Tools)** | 暴露给 LLM 的普通函数 —— Python 用 `@tool` + Pydantic 类型参数;C# 用 `AIFunctionFactory.Create(myFn)` 并读取 `[Description]` 特性。由 LLM 决定何时调用哪一个。 | [工具概览](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) · [函数工具](https://learn.microsoft.com/en-us/agent-framework/agents/tools/function-tools) |
| **Agent 会话 (Session)** | 跨多次运行复用的对话状态容器。Python:`agent.create_session()`,然后在每次 `agent.run` 调用时传 `session=session`。C#:`await agent.CreateSessionAsync()` 返回一个 `AgentSession`,后续传回去。同一思路,两套接口。 | [会话](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/session) |
| **流式响应** | 按 token 流式返回回复。Python:`async for chunk in agent.run(..., stream=True)`。C#:`await foreach (var update in agent.RunStreamingAsync(...))`。 | [Agent 类型](https://learn.microsoft.com/en-us/agent-framework/agents/) |

## 如何完成本实验

本实验**由自定义 Coding Agent 驱动**,不需要你手写 Prompt。[`PROMPT.md`](PROMPT.md) 中的 `target_language` 指令决定 Coding Agent 交付哪种技术栈。

1. 在你 fork 的仓库里开一个 Issue(或 `@copilot` 评论)并**粘贴 [`PROMPT.md`](PROMPT.md) 的全部内容**。第一行指派自定义 Agent;`target_language` 那一行选择 `python`、`csharp` 或 `both`。
2. Coding Agent 会:
   - 加载 [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md) 配置文件 —— 其中同时包含**两种语言**的标准模式;Agent 只会读取与 `target_language` 匹配的那一节。
   - 仅读取匹配当前语言的技能(`agent-framework-githubcopilot-py` 或 `agent-framework-githubcopilot-csharp`)以及共享的 `zavashop-context`。**不会**读取 workflow 或 AG-UI 相关技能。
   - 生成交付物 —— Python 文件放在实验目录下,C# 项目放在 `csharp/` 子目录下。
   - 提交 PR。你来审阅、按所选语言运行 verify、合并。

| 层级 | 角色 / API / 任务所在位置 |
| --- | --- |
| 角色(HOW) | [`.github/agents/zava-single-agent-builder.md`](../.github/agents/zava-single-agent-builder.md)(同时包含 Python 与 C# 章节) |
| API 参考(Python) | [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md)、[`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) |
| API 参考(C#) | [`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md)、[`zavashop-context`](../.github/skills/zavashop-context/SKILL.md) |
| 任务(WHAT + 哪种语言) | [`PROMPT.md`](PROMPT.md) |

## 你将学到什么

- 用你选择的语言定义函数工具:Python 的 `@tool` + Pydantic,或 C# 的 `AIFunctionFactory.Create` + `[Description]` 特性。
- 把工具接入由 Copilot 提供运行时的 Agent,并以流式方式返回回复。
- 用 `agent.create_session()` / `await agent.CreateSessionAsync()` 维持多轮对话上下文。
- 理解 Agent 的 *instructions* 如何影响 LLM 的规划 —— 哪怕本轮没有任何工具被调用。

## 自定义 Agent + 技能(由 [`PROMPT.md`](PROMPT.md) 指定)

- **自定义 Agent**:[`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md) —— 角色配置文件中编码了相关约定,以及 Python 和 C# 两种语言下的标准实现模式。
- **Agent 会读取的技能**:与语言匹配的 MAF 技能(`agent-framework-githubcopilot` 的 `-py` 或 `-csharp` 变体) + [`zavashop-context`](../.github/skills/zavashop-context/SKILL.md)(商品目录 schema、SKU 规则;与语言无关)。

## 交付物

Coding Agent 会根据 `target_language` 在 `lab-02-single-agent/` 内创建以下其中一种布局。当 `target_language: both` 时,**两种**目录都会被创建。

### Python (`target_language: python`)

```
lab-02-single-agent/
├── README.md            (本文件 — 已存在)
├── PROMPT.md            (用于 Copilot Coding Agent 的提示词 — 已存在)
├── requirements.txt
├── product_advisor.py   ← Agent 及其工具
└── verify.py            ← 脚本化验收测试
```

### C# / .NET (`target_language: csharp`)

```
lab-02-single-agent/
└── csharp/
    ├── ProductAdvisor/
    │   ├── ProductAdvisor.csproj      # Microsoft.NET.Sdk,net10.0
    │   ├── Program.cs                  # CopilotClient + AsAIAgent + 3 个工具
    │   ├── CatalogTools.cs             # 带 [Description] 特性的静态方法
    │   └── Models.cs                   # 商品目录行的 record 类型
    └── Verify/
        ├── Verify.csproj
        └── Program.cs                  # 三轮对话的验收测试
```

`ProductAdvisor.csproj` 引用 `GitHub.Copilot.SDK`、`Microsoft.Agents.AI`、`Microsoft.Agents.AI.GitHub.Copilot`、`Microsoft.Extensions.AI`(全部使用 `--prerelease`)。三个工具实现为 `CatalogTools` 上的静态方法,通过 `tools: [AIFunctionFactory.Create(CatalogTools.SearchProducts), AIFunctionFactory.Create(CatalogTools.GetProductDetails), AIFunctionFactory.Create(CatalogTools.RecommendAlternatives)]` 传给 `CopilotClient.AsAIAgent(...)`。完整模式见 [`zava-single-agent-builder`](../.github/agents/zava-single-agent-builder.md)。

## 验收标准

Coding Agent 必须满足以下每一项。它生成的 verify 脚本(Python 用 `verify.py`,C# 用 `csharp/Verify/Program.cs`)必须用所选语言自动校验第 4–7 项。

1. 恰好**三个**函数工具(两种语言下形状一致):
   - `search_products` / `SearchProducts(query, category?, maxPriceUsd?)`,返回商品目录行列表。
   - `get_product_details` / `GetProductDetails(sku)`,命中时返回该行,未命中时返回**字符串字面量** `"NOT_FOUND: <sku>"`(参见 `zavashop-context`)。
   - `recommend_alternatives` / `RecommendAlternatives(sku, maxResults=3)`,返回列表。
2. 工具只能从 `data/zava_catalog.json` 读取数据。禁止硬编码 SKU。C# 中应在启动时反序列化一次(例如 `JsonSerializer.Deserialize` 到 `record CatalogRow(...)` 数组)。
3. Agent 在程序作用域内只构造一次。Python:在 `async with` 内 `GitHubCopilotAgent(instructions=..., tools=[...])`。C#:`await using CopilotClient` + `client.AsAIAgent(ownsClient: true, name, instructions, tools)`。
4. 多轮对话:同一个会话至少跨三轮被复用。Python:同一个 `agent.create_session()`。C#:同一个由 `await agent.CreateSessionAsync()` 返回的 `AgentSession`。第二轮必须引用第一轮中建立的信息。
5. 脚本能处理 *"你们有没有 30 美元以下的红色哑光口红?"*,回答**必须**提到 `LIP-001` 和 `$24`。
6. 脚本能处理 *"SKN-027 和 SKN-030 有什么区别?"*,回答必须同时提到两个 SKU,以及 *night*(对应 SKN-027)和 *vitamin C*(对应 SKN-030)。
7. 脚本能处理 *"推荐一个价格相近、可替代 FRG-015 的产品。"*,回答必须提到 `FRG-009`。
8. 三轮都通过子串校验时 verify 脚本退出码为 0;否则为非 0。

## 运行方式

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

通过的一次运行会打印三轮带标签的对话,最后输出 `[OK] Lab 2 complete.`。

## 常见错误

| 现象 | 原因 |
| --- | --- |
| Agent 编造了商品目录里不存在的 SKU | 工具返回了空列表;instructions 没有规定"只能根据工具输出回答" |
| 第 2 轮丢失上下文 | 每轮都开了新会话 —— Python:要传 `session=session`;C#:要把 `session` 传给 `RunAsync` |
| `search_products` / `SearchProducts` 返回了全部商品 | 缺少筛选逻辑 —— 仔细看商品目录的过滤条件 |
| 工具遇到非法 SKU 抛异常 | 应该返回 `"NOT_FOUND: <sku>"` 字符串,绝不抛异常(参见 `zavashop-context`) |
| C#:还原时报 `NU1102` | 忘了加 `--prerelease`;预览版本只在 prerelease 渠道里 |
| C#:工具 schema 缺少字段 | 给每个参数加 `[Description("...")]`,这样 `AIFunctionFactory.Create` 才能生成有用的 schema |

完成了? → [实验 3 — MCP](../lab-03-mcp/README.md)
