using GitHub.Copilot.SDK;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.GitHub.Copilot;

string model = Environment.GetEnvironmentVariable("GITHUB_COPILOT_MODEL") ?? "gpt-5.5";

Console.WriteLine("[ZavaShop AI Bootstrap]");
Console.WriteLine($"  Model:    {model}");
Console.WriteLine($"  CLI:      copilot");
Console.WriteLine();

if (model != "gpt-5.5")
{
    Console.Error.WriteLine($"[FAIL] GITHUB_COPILOT_MODEL is '{model}', expected 'gpt-5.5'. Edit the workshop .env or export the var.");
    return 2;
}

try
{
    string cliPath = Environment.GetEnvironmentVariable("COPILOT_CLI_PATH") ?? "/opt/homebrew/bin/copilot";
    if (!File.Exists(cliPath))
    {
        Console.Error.WriteLine($"[FAIL] Copilot CLI not found at '{cliPath}'. Set COPILOT_CLI_PATH to your installed copilot binary.");
        return 4;
    }

    await using CopilotClient copilotClient = new(new CopilotClientOptions
    {
        CliPath = cliPath,
    });
    await copilotClient.StartAsync();

    SessionConfig sessionConfig = new()
    {
        OnPermissionRequest = PermissionHandler.ApproveAll,
        Model = model,
    };

    AIAgent agent = copilotClient.AsAIAgent(
        sessionConfig,
        true,
        "zavashop-hello",
        "ZavaShopHello",
        "ZavaShop AI assistant");

    Console.Write("Agent  : ");
    await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(
        "Introduce yourself in two short sentences. Mention that ZavaShop sells beauty and lifestyle products across five regional warehouses, and that you are powered by GitHub Copilot GPT-5.5."))
    {
        Console.Write(update);
    }
    Console.WriteLine();
    Console.WriteLine();
}
catch (FileNotFoundException ex)
{
    Console.Error.WriteLine($"[FAIL] copilot CLI not found: {ex.Message}");
    Console.Error.WriteLine("  Hint: install GitHub Copilot CLI and run 'copilot auth'.");
    return 4;
}

Console.WriteLine("[OK] Lab 1 complete. Proceed to Lab 2.");
return 0;
