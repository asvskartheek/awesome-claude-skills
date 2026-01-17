# Agent-Lightning APO API Reference

Detailed API documentation for training LangChain agents with Agent-Lightning APO.

## Table of Contents

- [agl.LitAgent](#aglllitagent)
- [agl.PromptTemplate](#aglprompttemplate)
- [agl.APO](#aglapo)
- [agl.Trainer](#agltrainer)
- [agl.TraceToMessages](#agltracetomessages)
- [LangGraph Swarm APIs](#langgraph-swarm-apis)
- [LangSmith Dataset APIs](#langsmith-dataset-apis)

---

## agl.LitAgent

Base class for trainable agents. Extend this to wrap your LangChain agent.

```python
import agentlightning as agl
from typing import TypedDict

class Task(TypedDict):
    prompt: str
    expected_terms: list[str]
    # ... other fields

class MyAgent(agl.LitAgent[Task]):
    def rollout(
        self,
        task: Task,                    # Task dict from dataset
        resources: agl.NamedResources, # Dict of PromptTemplates being optimized
        rollout: agl.Rollout           # Rollout context (for tracing)
    ) -> float:                        # Return reward between 0.0 and 1.0
        ...
```

### Key Points

- Generic type parameter `Task` defines your task structure
- `rollout()` must return a float reward in range [0.0, 1.0]
- `resources` only contains the prompt(s) being optimized
- Store initial resources in `__init__` and merge with optimized ones

---

## agl.PromptTemplate

Represents a prompt that can be optimized by APO.

```python
prompt = agl.PromptTemplate(
    template="You are a {role} assistant...",  # Template string
    engine="f-string"                          # Only "f-string" supported
)

# Format with variables
formatted = prompt.format(role="helpful")

# Access raw template
raw = prompt.template
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `template` | str | The prompt template string |
| `engine` | str | Template engine, must be "f-string" |

---

## agl.APO

Automatic Prompt Optimization algorithm using textual gradients.

```python
from openai import AsyncOpenAI

algo = agl.APO(
    async_openai_client=AsyncOpenAI(),  # Required: AsyncOpenAI client
    gradient_model="openai/gpt-4o",     # Model for computing critiques
    apply_edit_model="openai/gpt-4o",   # Model for applying edits
    diversity_temperature=1.0,           # Temperature for LLM calls
    gradient_batch_size=4,               # Rollouts sampled for gradient
    val_batch_size=16,                   # Validation examples per eval
    beam_width=4,                        # Top prompts kept in beam
    branch_factor=4,                     # Variants generated per prompt
    beam_rounds=3,                       # Optimization rounds
    rollout_batch_timeout=3600.0,        # Max wait time for batch (seconds)
    run_initial_validation=True,         # Validate seed prompt first
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `async_openai_client` | AsyncOpenAI | required | OpenAI-compatible async client |
| `gradient_model` | str | "gpt-4o" | Model for critique generation |
| `apply_edit_model` | str | "gpt-4o" | Model for prompt rewriting |
| `diversity_temperature` | float | 1.0 | Temperature for generation |
| `gradient_batch_size` | int | 4 | Rollouts for gradient computation |
| `val_batch_size` | int | 16 | Validation batch size |
| `beam_width` | int | 4 | Number of prompts to keep |
| `branch_factor` | int | 4 | Variants per prompt |
| `beam_rounds` | int | 3 | Number of optimization rounds |
| `rollout_batch_timeout` | float | 3600.0 | Timeout in seconds |
| `run_initial_validation` | bool | True | Validate before optimization |

### APO Algorithm Flow

1. **Evaluate**: Run rollouts with current prompts
2. **Critique**: Analyze failed rollouts, generate textual gradient
3. **Rewrite**: Apply critique to produce improved prompt
4. **Beam Search**: Keep top `beam_width` prompts
5. **Repeat** for `beam_rounds`

### Methods

```python
# Get the best optimized prompt after training
best_prompt = algo.get_best_prompt()
print(best_prompt.template)
```

---

## agl.Trainer

Orchestrates training with parallel rollout execution.

```python
trainer = agl.Trainer(
    algorithm=algo,                     # APO algorithm instance
    n_runners=8,                        # Parallel rollout runners
    initial_resources={                 # Starting prompts
        "prompt_key": agl.PromptTemplate(...)
    },
    adapter=agl.TraceToMessages(),      # Adapter for trace conversion
)

# Start training
trainer.fit(
    agent=my_agent,                     # LitAgent instance
    train_dataset=train_data,           # List of task dicts
    val_dataset=val_data,               # Validation task dicts
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `algorithm` | APO | The optimization algorithm |
| `n_runners` | int | Number of parallel runners |
| `initial_resources` | dict | Starting PromptTemplate dict |
| `adapter` | TraceToMessages | Trace adapter for LangChain |

---

## agl.TraceToMessages

Adapter that converts LangChain trace spans into OpenAI-compatible messages.

```python
adapter = agl.TraceToMessages()
```

### Purpose

- Converts trace spans to conversation messages
- Reconstructs prompts, completions, tool calls from `gen_ai.*` span attributes
- Required for APO to analyze LangChain agent behavior

---

## LangGraph Swarm APIs

### create_agent

Create a LangChain React agent.

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

agent = create_agent(
    name="agent_name",           # Unique identifier
    model=ChatOpenAI(...),       # LLM instance
    system_prompt="...",         # System prompt (what we optimize)
    tools=[tool1, tool2],        # List of tools
)
```

### create_handoff_tool

Create a tool for agent-to-agent transfer.

```python
from langgraph_swarm import create_handoff_tool

handoff = create_handoff_tool(
    agent_name="target_agent",    # Agent to transfer to
    description="When to use...", # Description for LLM
)
# Returns a tool named "transfer_to_{agent_name}"
```

### create_swarm

Create a multi-agent swarm.

```python
from langgraph_swarm import create_swarm
from langgraph.checkpoint.memory import MemorySaver

workflow = create_swarm(
    [agent1, agent2, agent3],        # List of agents
    default_active_agent="agent1"    # Starting agent
)

# Compile with checkpointer
app = workflow.compile(checkpointer=MemorySaver())

# Invoke
result = app.invoke(
    {"messages": [{"role": "user", "content": "..."}]},
    config={"configurable": {"thread_id": "unique-id"}}
)
```

---

## LangSmith Dataset APIs

### Loading Datasets

```python
from langsmith import Client

client = Client()
examples = list(client.list_examples(dataset_name="my_dataset"))

# Each example has:
# - example.inputs: dict with input fields (must contain "prompt")
# - example.outputs: dict with task-specific expected output fields
```

### Dataset Schema

**Required:**
- `inputs.prompt` - The user query/input for the agent

**Task-Specific Outputs (examples):**
- Multi-agent travel system: `expected_terms`, `expected_tool_calls`, `expected_agent_sequence`, `min_steps`, `max_steps`
- SQL agent: `expected_query`, `ground_truth_result`, `db_id`
- Classification: `expected_label`, `confidence_threshold`
- RAG: `expected_sources`, `expected_answer_keywords`

### Dataset Format for APO

```python
# Convert LangSmith examples to APO task format
# Adapt the outputs mapping to match YOUR reward function's needs
tasks = []
for ex in examples:
    task = {
        "prompt": ex.inputs.get("prompt", ""),  # Required
        # Map your task-specific output fields here:
        "expected_terms": ex.outputs.get("expected_terms", []),
        "expected_tool_calls": ex.outputs.get("expected_tool_calls", []),
        # ... add fields your reward function needs
    }
    tasks.append(task)
```

---

## Configuration Examples

### Small Config (Smoke Test)

```python
SMALL_CONFIG = TrainingConfig(
    gradient_model="openai/gpt-4o",
    apply_edit_model="openai/gpt-4o",
    gradient_batch_size=2,
    val_batch_size=2,
    beam_width=1,
    branch_factor=1,
    beam_rounds=1,
    n_runners=1,  # Single runner for Mac compatibility
    train_split=0.5,
)
```

### Full Config (Production)

```python
FULL_CONFIG = TrainingConfig(
    gradient_model="openai/gpt-4o",
    apply_edit_model="openai/gpt-4o",
    gradient_batch_size=4,
    val_batch_size=4,
    beam_width=4,
    branch_factor=4,
    beam_rounds=3,
    n_runners=4,
    train_split=0.7,
)
```

---

## Reward Weights Reference

Default weights for composite reward calculation:

```python
REWARD_WEIGHTS = {
    "term_matching": 0.30,      # Output contains expected terms
    "tool_calls": 0.25,         # Correct tools were called
    "agent_routing": 0.30,      # Correct agent sequence
    "efficiency": 0.15,         # Step count within bounds
}
```

### Adjusting Weights

- **Increase `term_matching`**: When output correctness is critical
- **Increase `tool_calls`**: When tool usage accuracy matters most
- **Increase `agent_routing`**: For multi-agent routing optimization
- **Increase `efficiency`**: When minimizing steps is important

---

## External References

- [Agent-Lightning Main Docs](https://microsoft.github.io/agent-lightning/stable/)
- [Train First Agent Tutorial](https://microsoft.github.io/agent-lightning/stable/how-to/train-first-agent)
- [APO Algorithm Reference](https://microsoft.github.io/agent-lightning/stable/algorithm-zoo/apo)
- [LitAgent Interface](https://microsoft.github.io/agent-lightning/stable/tutorials/write-agents)
- [LangGraph Swarm GitHub](https://github.com/langchain-ai/langgraph-swarm-py)
- [LangSmith Docs](https://docs.langchain.com/langsmith/)
