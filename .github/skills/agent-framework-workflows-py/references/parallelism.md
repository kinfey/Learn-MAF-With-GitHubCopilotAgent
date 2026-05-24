# Parallelism — Fan-Out / Fan-In, Aggregation, Map-Reduce

## Fan-out / fan-in

Use `add_fan_out_edges(src, [t1, t2, ...])` to dispatch the same message in parallel and `add_fan_in_edges([s1, s2, ...], dst)` to collect a `list[T]` from the sources into one handler.

```python
from agent_framework import (
    Agent, AgentExecutor, AgentExecutorRequest, AgentExecutorResponse,
    Executor, Message, WorkflowBuilder, WorkflowContext, handler,
)
from typing_extensions import Never


class Dispatch(Executor):
    @handler
    async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        await ctx.send_message(AgentExecutorRequest(
            messages=[Message("user", contents=[prompt])],
            should_respond=True,
        ))


class Aggregate(Executor):
    @handler
    async def aggregate(self, results: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]) -> None:
        by_id = {r.executor_id: r.agent_response.text for r in results}
        consolidated = (
            "Consolidated Insights\n=====================\n\n"
            f"Research:\n{by_id.get('researcher','')}\n\n"
            f"Marketing:\n{by_id.get('marketer','')}\n\n"
            f"Legal:\n{by_id.get('legal','')}\n"
        )
        await ctx.yield_output(consolidated)


workflow = (
    WorkflowBuilder(start_executor=Dispatch(id="dispatcher"))
    .add_fan_out_edges(Dispatch(id="dispatcher"), [researcher, marketer, legal])
    .add_fan_in_edges([researcher, marketer, legal], Aggregate(id="aggregator"))
    .build()
)
```

The fan-in handler's input type must be a `list[T]` (or `list[Union[...]]`) matching what the upstream executors emit.

## Aggregating heterogeneous types

Annotate the fan-in input as `list[int | float | str | ...]` to receive different upstream types in the same call:

```python
class Aggregator(Executor):
    @handler
    async def handle(self, results: list[int | float], ctx: WorkflowContext[Never, list[int | float]]):
        await ctx.yield_output(results)

workflow = (
    WorkflowBuilder(start_executor=dispatcher)
    .add_fan_out_edges(dispatcher, [average_executor, sum_executor])
    .add_fan_in_edges([average_executor, sum_executor], aggregator)
    .build()
)
```

## Live streaming across concurrent branches

While branches run, render per-branch output by binding to `event.executor_id`:

```python
buffers = {"researcher": "", "marketer": "", "legal": ""}
completed: set[str] = set()

async for event in workflow.run(prompt, stream=True):
    if event.type == "executor_completed" and event.executor_id in buffers:
        completed.add(event.executor_id)
        render(buffers, completed)
    elif event.type == "output" and isinstance(event.data, AgentResponseUpdate):
        eid = event.executor_id or ""
        if eid in buffers:
            buffers[eid] += event.data.text
            render(buffers, completed)
```

## Map-reduce with file-backed intermediates

For large inputs, partition once in `Split`, write intermediate files in `Map`, group / shuffle in `Shuffle`, sum per partition in `Reduce`, and finalize in `Completion`:

```python
workflow = (
    WorkflowBuilder(start_executor=split)
    .add_fan_out_edges(split, mappers)            # Split  → N mappers
    .add_fan_in_edges(mappers, shuffle)           # mappers → shuffle
    .add_fan_out_edges(shuffle, reducers)         # Shuffle → M reducers
    .add_fan_in_edges(reducers, completion)       # reducers → completion
    .build()
)
```

Pass file paths between stages (not raw payloads) to keep memory bounded. Each mapper/reducer reads its slice from `ctx.get_state(self.id)`.

## Visualization

Install with the `[viz]` extra and a GraphViz binary, then export the topology:

```python
from agent_framework import WorkflowViz

viz = WorkflowViz(workflow)
print(viz.to_mermaid())
print(viz.to_digraph())
svg_path = viz.export(format="svg")               # raises ImportError without the [viz] extra
```

## When to use what

| Need | Pattern |
| --- | --- |
| Same input → many workers, single join | `add_fan_out_edges` + `add_fan_in_edges` |
| Same input → many workers, no join (independent terminals) | `add_fan_out_edges` only |
| Different inputs from one source per branch | One `add_edge` per target, optionally with `target_id` in `ctx.send_message` |
| Heterogeneous result types into one handler | `list[int | float | ...]` annotation on the fan-in handler |
| Functional API (plain async) | `await asyncio.gather(branch1(), branch2(), ...)` inside `@workflow` |
| Big payloads | Store in `ctx.set_state`, pass IDs; or write to disk and pass file paths |
