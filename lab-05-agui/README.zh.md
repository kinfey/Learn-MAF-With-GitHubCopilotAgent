# Lab 5 — AGUI：托管的 Coding Agent UI

> 预计用时：75 分钟。**由 Copilot Coding Agent 驱动。**>
> **学习目标**：通过把 Lab 4 的工作流暴露为 HTTP/SSE 端点（加 API-Key 闸门），践行 MAF 的 **AG-UI 集成 + 混合工具执行**。GitHub Copilot SDK 仍然驱动 Agent 本身；Coding Agent 同时写服务端与客户端；你决定哪些工具跑在哪一侧。用 [`PROMPT.md`](PROMPT.md) 里的 `target_language` 选语言：Python 走 FastAPI + `add_agent_framework_fastapi_endpoint`；C# 走 ASP.NET Core（`Microsoft.NET.Sdk.Web`）+ `AddAGUI()` + `MapAGUI(...)`，同样以 GitHub Copilot SDK 为模型后背。
## ZavaShop 故事

Lab 4 的零售工作流在命令行下能跑，但运营团队整天泡在浏览器里。他们想要一个聊天式的 UI，能做到：

- 用自然语言输入订单（"给 CUST-501 从西雅图仓预留 2 件 LIP-001"）。
- 实时看到工作流一步步执行。
- 在敏感动作（大额预留）前进行批准。

你将用 `add_agent_framework_fastapi_endpoint` 把零售工作流封装成一个 **AG-UI** HTTP/SSE 端点，再用 Python `AGUIChatClient` 写一个交互式客户端。还会加一个 **客户端工具** 来演示 AG-UI 的混合执行模型。

## 本实验涉及的 Microsoft Agent Framework 概念

Lab 5 身处 MAF 的 **Integrations** 层——不引入新的 agent 或 workflow 原语，而是把它们运输到一个协议上。

| 概念 | 在代码中的体现 | Microsoft Learn |
| --- | --- | --- |
| **AG-UI 集成** | 一类一等公民级的 **UI Framework integration**：把任意 `Agent` 或 `Workflow` 暴露在 HTTP/SSE 上，任何 AG-UI 客户端（Python、C#、网页）都能流式消费事件。Python：`add_agent_framework_fastapi_endpoint(app, agent, "/retail", dependencies=[...])`。C#：`builder.Services.AddAGUI()` + `builder.AddAIAgent(name, factory).WithInMemorySessionStore()` + `app.MapAGUI(name, "/retail")`。 | [Integrations](https://learn.microsoft.com/zh-cn/agent-framework/integrations/)（UI Framework integrations） |
| **Workflow-as-Agent on AG-UI** | 为 AG-UI 包装 `Workflow`：每个对话线程都获得新的 workflow 实例和独立状态。Python：`AgentFrameworkWorkflow(workflow_factory=...)`。C#：注册工厂 `builder.AddAIAgent("retail_orchestrator", sp => BuildOrchestrator(sp))`。 | [Workflows overview](https://learn.microsoft.com/zh-cn/agent-framework/workflows/)（`.as_agent()` 模式） |
| **混合工具执行（Hybrid Tools）** | 一部分工具在服务端运行（目录 / 库存 / workflow），另一部分在客户端（`notify_local_user`）。AG-UI 协议自动协商每个调用在哪一侧执行。两语言下模型一致 — 工具注册在哪边，就在哪边跑。 | [Tools Overview](https://learn.microsoft.com/zh-cn/agent-framework/agents/tools/) |
| **集成边界的鉴权** | AG-UI 端点一律放在身份检查后面。Python：FastAPI `Depends(verify_api_key)`。C#：一个 ASP.NET Core middleware 读 `X-API-Key`，不合法就在进入 AG-UI handler 前 `401` 揭雾。 | [Integrations](https://learn.microsoft.com/zh-cn/agent-framework/integrations/) |

## 运行本实验

1. 在你的 fork 里新开一个 Issue（或 `@copilot` 评论），粘贴 [`PROMPT.md`](PROMPT.md) 的全部内容。首行指派 custom agent；`target_language` 那行选 `python` / `csharp` / `both`。
2. Coding Agent 会：
   - 加载 [`zava-agui-engineer`](../.github/agents/zava-agui-engineer.md) profile（同时包含 Python 和 C# 两套范本）。
   - 读与 `target_language` 匹配的 AG-UI skill，加 workflow + Copilot SDK skill 的一小块。
   - 生成语言对应的文件（Python `.py` 放 lab 根目录，C# 项目放 `csharp/`）。
   - 开 PR。你 review，本地跑语言对应的 verify，合并。

| 层 | 角色 / API / 任务住哪里 |
| --- | --- |
| 角色（HOW） | [`.github/agents/zava-agui-engineer.md`](../.github/agents/zava-agui-engineer.md)（Python + C# 范本代码） |
| API 参考（Python） | [`agent-framework-agui-py`](../.github/skills/agent-framework-agui-py/SKILL.md)、[`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md)、[`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) |
| API 参考（C#） | [`agent-framework-agui-csharp`](../.github/skills/agent-framework-agui-csharp/SKILL.md)、[`agent-framework-workflows-csharp`](../.github/skills/agent-framework-workflows-csharp/SKILL.md)、[`agent-framework-githubcopilot-csharp`](../.github/skills/agent-framework-githubcopilot-csharp/SKILL.md) |
| 任务（WHAT + 哪一栈） | [`PROMPT.md`](PROMPT.md) |

## 你会学到什么

- 在一个 AG-UI FastAPI 端点后面托管 `Agent`（和 `Workflow`）。
- 用 `AGUIChatClient` 通过 SSE 把事件流到 Python 客户端。
- 用 `AgentFrameworkWorkflow(workflow_factory=...)` 维护线程级状态。
- 混合工具执行 — 服务端有重工具（目录 / 库存）；客户端有本地工具（`notify_local_user`），在运营人员的终端里运行。
- 用 FastAPI API-Key 依赖保护端点。

## Custom Agent + Skills（由 [`PROMPT.md`](PROMPT.md) 指定）

- **Custom agent**：[`zava-agui-engineer`](../.github/agents/zava-agui-engineer.md) — 角色 profile 包含 server/client/verify 的骨架以及混合执行划分。
- **Agent 会读的 skill**：
  - [`agent-framework-agui-py`](../.github/skills/agent-framework-agui-py/SKILL.md) — 每一节都要看。
  - [`agent-framework-workflows-py`](../.github/skills/agent-framework-workflows-py/SKILL.md) — 只看 **workflow_factory** 模式。
  - [`agent-framework-githubcopilot-py`](../.github/skills/agent-framework-githubcopilot-py/SKILL.md) — 只看 **Tools** 和 **Sessions**。
- **复用前面的实验**：Lab 4 的 `retail_workflow.py`、Lab 2 的 `search_products`（通过 `sys.path` 导入，**不** 重写）。

## 架构

```
┌──────────────────────────────────────┐  HTTP/SSE  ┌────────────────────────────────────────┐
│ server.py                            │ ─────────► │ client.py                              │
│ FastAPI                              │            │ Agent(client=AGUIChatClient(...),      │
│ + add_agent_framework_fastapi_       │ ◄───────── │         tools=[notify_local_user])     │
│   endpoint(app, retail_orchestrator, │            │ + AgentSession 多轮对话                │
│   "/retail", deps=[API key])         │            │ + 流式接收文本块                       │
│ 端口 5100,要求 X-API-Key 头           │            │                                        │
│ 服务端工具：search_products、        │            │ 客户端工具：                           │
│   get_warehouse_stock、              │            │   notify_local_user(msg) — 终端响铃    │
│   run_retail_workflow                │            │   + 打印                               │
└──────────────────────────────────────┘            └────────────────────────────────────────┘
```

- `retail_orchestrator` 是一个 `GitHubCopilotAgent`，它把 Lab 4 的 `build_retail_workflow()` 包成一个工具（`run_retail_workflow(...)`）。
- 服务端工具：读目录、查仓库库存、跑工作流。
- 客户端工具：`notify_local_user(message)` — 每次成功预留时，在 *运营人员本机* 触发。

## 交付物

### Python（`target_language: python`）

```
lab-05-agui/
├── README.md
├── PROMPT.md
├── requirements.txt
├── server.py             ← FastAPI + AG-UI 端点
├── client.py             ← AGUIChatClient + Agent 包装 + 客户端工具
└── verify.py             ← 启动服务、跑脚本化客户端对话、断言
```

### C# / .NET（`target_language: csharp`）

```
lab-05-agui/
└── csharp/
    ├── RetailServer/
    │   ├── RetailServer.csproj   # Microsoft.NET.Sdk.Web；引 Microsoft.Agents.AI.Hosting.AGUI.AspNetCore、
    │   │                         #   Microsoft.Agents.AI.GitHub.Copilot、Microsoft.Agents.AI.Workflows、
    │   │                         #   GitHub.Copilot.SDK；ProjectReference 指向 lab-04 Workflows.csproj
    │   ├── Program.cs            # AddAGUI() + AddAIAgent(...).WithInMemorySessionStore() + ApiKeyMiddleware + MapAGUI
    │   ├── Tools/ServerTools.cs  # 带 [Description] 的静态方法，被包为 AIFunction
    │   └── Middleware/ApiKeyMiddleware.cs
    ├── RetailClient/
    │   ├── RetailClient.csproj   # Microsoft.NET.Sdk；引 Microsoft.Agents.AI.AGUI、Microsoft.Agents.AI
    │   ├── Program.cs            # new AGUIChatClient(httpClient, endpoint).AsAIAgent(name, tools)
    │   └── Tools/NotifyLocalUser.cs # 仅在客户端出现的工具
    └── Verify/
        ├── Verify.csproj         # 引 RetailClient.csproj
        └── Program.cs            # 拉起 RetailServer 子进程、跑脚本化对话、断言、finally 里 kill
```

## .NET / C# 实现

遵循 [`zava-agui-engineer`](../.github/agents/zava-agui-engineer.md)。关键形状：

**服务端 — `RetailServer/Program.cs`**：

```csharp
WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

await using CopilotClient copilotClient = new();
await copilotClient.StartAsync();

builder.Services.AddAGUI();
builder.Services.AddSingleton(copilotClient);

builder.AddAIAgent("retail_orchestrator", sp =>
{
    var copilot = sp.GetRequiredService<CopilotClient>();
    return copilot.AsAIAgent(
        ownsClient: false,
        name: "retail_orchestrator",
        instructions: "You are ZavaShop's retail orchestrator. Use the tools to honor reservations.",
        tools: new[]
        {
            AIFunctionFactory.Create(ServerTools.SearchProducts),
            AIFunctionFactory.Create(ServerTools.GetWarehouseStock),
            AIFunctionFactory.Create(ServerTools.RunRetailWorkflow),
        });
}).WithInMemorySessionStore();

WebApplication app = builder.Build();
app.UseMiddleware<ApiKeyMiddleware>();   // 校验 X-API-Key 是否等于 AG_UI_API_KEY
app.MapAGUI("retail_orchestrator", "/retail");
app.Run("http://127.0.0.1:5100");
```

**服务端工具 — `RetailServer/Tools/ServerTools.cs`** 靠 `[Description(...)]` 给 `AIFunctionFactory.Create(...)` 产生 schema，而 `RunRetailWorkflow` 通过 ProjectReference 调 Lab 4 的工作流：

```csharp
[Description("跳起 Lab 4 零售工作流，返回最终 OrderRecord。")]
public static async Task<OrderRecord> RunRetailWorkflow(
    string customerId, string sku, int quantity, string preferredWarehouse)
{
    Workflow workflow = RetailWorkflow.BuildRetailWorkflow(/* agents */);
    CustomerOrder input = new(customerId, sku, quantity, preferredWarehouse);
    await using StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, input);
    await foreach (WorkflowEvent evt in run.WatchStreamAsync())
    {
        if (evt is OutputEvent<OrderRecord> output) return output.Value;
    }
    throw new InvalidOperationException("工作流未产出 OrderRecord。");
}
```

**客户端 — `RetailClient/Program.cs`** 只在客户端注册并流式接收：

```csharp
using HttpClient httpClient = new() { Timeout = TimeSpan.FromSeconds(60) };
httpClient.DefaultRequestHeaders.Add("X-API-Key", Environment.GetEnvironmentVariable("AG_UI_API_KEY")!);

AGUIChatClient chatClient = new(httpClient, new Uri("http://127.0.0.1:5100/retail"));
AIAgent agent = chatClient.AsAIAgent(
    name: "zava_ops",
    tools: new[] { AIFunctionFactory.Create(NotifyLocalUser.Notify) });   // 仅客户端

AgentSession session = await agent.CreateSessionAsync();
await foreach (string chunk in session.RunStreamingAsync(userMessage))
    Console.Write(chunk);
```

**客户端工具 — `RetailClient/Tools/NotifyLocalUser.cs`**（服务端里不允许存在同名工具）：

```csharp
public static class NotifyLocalUser
{
    [Description("响铃 + 打印 [NOTIFY] 消息。")]
    public static string Notify(string message)
    {
        Console.Write('\a');
        Console.WriteLine($"[NOTIFY] {message}");
        return "OK";
    }
}
```

**Verify — `Verify/Program.cs`** 拉起 `RetailServer` 子进程、轮询端口、跑一轮脚本化对话（调用 `RetailClient` 的库形式），`finally` 中 kill：

```csharp
Process server = Process.Start(new ProcessStartInfo("dotnet", "run --project ../RetailServer")
{
    EnvironmentVariables = { ["AG_UI_API_KEY"] = "test-key-do-not-use-in-prod" },
});
try
{
    await WaitForPortAsync(5100);
    string final = await RunScriptedTurnAsync("请从西雅图仓为 CUST-501 预留 2 件 LIP-001，并在本地通知我……");
    Assert.Matches(@"ZS-[0-9A-F]{8}", final);
    Assert.Contains("LIP-001", final);
    Assert.Contains("WH-SEA", final);
    Assert.Contains("[NOTIFY]", final);
    Console.WriteLine("[OK] Lab 5 complete.");
    return 0;
}
finally { server.Kill(entireProcessTree: true); }
```

## 验收标准

### 服务端（`server.py`）

1. 从 `lab-04-multi-agent-workflow/retail_workflow.py` import `build_retail_workflow`（用 `sys.path`）。
2. 定义服务端 `@tool`：
   - `search_products(query: str) -> list[dict]` — 包一层 Lab 2 的 `search_products`。
   - `get_warehouse_stock(sku: str, warehouse_code: str) -> int | str` — 读 `data/zava_warehouses.json`。
   - `run_retail_workflow(customer_id: str, sku: str, quantity: int, preferred_warehouse: str) -> dict` — 调 Lab 4 的工作流并返回最终输出 dict。
3. 用上述三个工具构造名为 `retail_orchestrator` 的 `GitHubCopilotAgent`。
4. 通过 `add_agent_framework_fastapi_endpoint(app, retail_orchestrator, "/retail", dependencies=[Depends(verify_api_key)])` 挂在 `/retail` 路径。
5. `verify_api_key` 从环境读取 `AG_UI_API_KEY`；未设置时放行并打 warning（dev 模式，见 `agent-framework-agui-py` 技能）。
6. `__main__` 用 `uvicorn.run(app, host="127.0.0.1", port=5100)` 启动。

### 客户端（`client.py`）

7. 定义客户端 `@tool` `notify_local_user(message: str) -> str`：打印 `[NOTIFY] {message}`，前面加一个 `\a` 响铃字符。返回 `"OK"`。
8. 构造 `Agent(name="zava_ops", client=AGUIChatClient(endpoint=..., headers={"X-API-Key": ...}), tools=[notify_local_user])`。
9. 从环境读 `AGUI_SERVER_URL`（默认 `http://127.0.0.1:5100/retail`）和 `AG_UI_API_KEY`。
10. 在交互循环（`while True: input(...)`）中维护同一个 `agent.create_session()`。
11. 把每个响应块流式打到 stdout。

### 自检（`verify.py`）

12. 把 `server.py` 作为子进程启动；轮询 `http://127.0.0.1:5100/retail` 直到就绪。
13. 给服务端和客户端子进程都设 `AG_UI_API_KEY = "test-key-do-not-use-in-prod"`。
14. 在程序里跑一轮（不走交互循环）：
    *"请从西雅图仓为客户 CUST-501 预留 2 件 LIP-001，并在预留完成后本地通知我。"*
15. 断言最终响应文本：
    - 匹配运单号正则 `r"ZS-[0-9A-F]{8}"`。
    - 包含 `LIP-001` 和 `WH-SEA`。
    - 包含字符串 `[NOTIFY]`（证明客户端工具在本机被触发）。
16. 在 `finally:` 中销毁服务子进程。仅当全部通过时退出 0。末行打印 `[OK] Lab 5 complete.`

## 运行

### Python

```bash
cd lab-05-agui
uv pip install -r requirements.txt
export AG_UI_API_KEY=anything-non-empty

# 终端 1
python server.py

# 终端 2
python client.py
```

或者直接：

```bash
python verify.py
```

### C# / .NET

```bash
cd lab-05-agui/csharp
export AG_UI_API_KEY=anything-non-empty

# 终端 1
dotnet run --project RetailServer

# 终端 2
dotnet run --project RetailClient
```

或者直接：

```bash
dotnet run --project Verify
```

## 常见错误

| 现象 | 原因 |
| --- | --- |
| 客户端看不到 `[NOTIFY]` | `notify_local_user` / `NotifyLocalUser.Notify` 没注册到客户端 `Agent` / `chatClient.AsAIAgent(tools: ...)`，或服务端也注册了（必须仅客户端） |
| 客户端 `401` | `X-API-Key` 头没加到 `AGUIChatClient(headers=...)`（Python）或 `httpClient.DefaultRequestHeaders`（C#） |
| 服务端首次请求卡住 | Lab 4 的 workflow 没法引入 — Python：修 `sys.path`。C#：加 `ProjectReference` 指向 `lab-04 Workflows.csproj` |
| 响应流式中断 | HTTP 默认超时 — Python：给 `AGUIChatClient` 传 `timeout=60.0`。C#：`httpClient.Timeout = TimeSpan.FromSeconds(60)` |
| `verify.py` / `Verify/Program.cs` 跑完留下服务进程 | 漏写 `finally:`（Python）或 `finally { server.Kill(entireProcessTree: true); }`（C#）— 手动 kill 掉残留进程 |
| C#：AG-UI 端点访不通 | 漏写 `app.MapAGUI(AgentName, "/retail")`，或注册名大小写不一致 |
| C#：多个客户端共享了同一个 session | 漏写 `.WithInMemorySessionStore()` |

Lab 5 绿了，ZavaShop Coding Agents 工作坊就完成了。

## 反思

跑完 5 个实验后：

1. 对比 Labs 2–5 的 **prompt 体积** 和 **PR diff 体积**。MAF 技能干了多少重活，一目了然。
2. 记下哪些验收标准 Coding Agent 第一次 PR 就过了，哪些需要追加 review 评论。后者就是该再写新技能的地方。
3. 如果可以，把 5 个实验用 **GPT-4o** 或 **Claude Sonnet 4** 重跑一遍 — 同一段 prompt 在别的模型上还能开出能通过的 PR 吗？这就是 prompt 可移植性的实战练习。
