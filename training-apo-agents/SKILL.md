---
name: training-apo-agents
description: Train LangChain/LangGraph agents using Microsoft Agent-Lightning APO (Automatic Prompt Optimization). Use when user mentions APO training, prompt optimization, agent-lightning, training multi-agent systems, training single agents, or optimizing agent prompts.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# Training LangChain Agents with APO

Train LangChain/LangGraph agents (single or multi-agent swarms) using Microsoft Agent-Lightning's APO algorithm to automatically optimize agent prompts.

## Prerequisites Check

**Before starting APO training, verify you have these three components:**

| Component | Required | Description |
|-----------|----------|-------------|
| **Agent Code** | ✅ | Working LangChain/LangGraph agent that can be invoked with a prompt |
| **Evaluation Criteria** | ✅ | Clear definition of what "good" agent behavior looks like (metrics to optimize) |
| **Training Data** | ✅ | Dataset with input prompts and expected outputs for reward calculation |

### 1. Agent Code
- [ ] Agent runs successfully with test inputs
- [ ] Agent uses system prompts that can be optimized
- [ ] Agent can be rebuilt with different prompts (factory pattern)

### 2. Evaluation Criteria
- [ ] Defined what success looks like (e.g., correct tool calls, accurate output, proper routing)
- [ ] Metrics are measurable and can return a score between 0.0 and 1.0

### 3. Training Data
- [ ] Minimum 10-20 examples for smoke testing
- [ ] Each example has: input prompt + expected outputs for reward calculation

**If any component is missing, complete it first before proceeding with APO training.**

## Quick Start

```bash
# Install
uv add "agentlightning[apo]"

# Run smoke test first
uv run train_multi_agent.py --config small

# Run full training
uv run train_multi_agent.py --config full
```

## Core Concepts

**APO (Automatic Prompt Optimization)** uses "textual gradients" to optimize prompts:
1. Run agent rollouts with current prompts
2. Analyze failures and generate critiques
3. Rewrite prompts based on critiques
4. Keep top performers via beam search

**Key Components:**
- `LitAgent` - Wrapper for your agent that returns rewards
- `PromptTemplate` - Prompts to optimize (engine="f-string")
- `APO` - The optimization algorithm
- `Trainer` - Orchestrates training with parallel runners

## Implementation Workflow

### Step 1: Create Prompt Templates

```python
# training/prompts.py
import agentlightning as agl

AGENT_PROMPT = """You are a helpful assistant. Route users to specialists:
- For bookings -> transfer_to_booking_agent
- For claims -> transfer_to_claims_agent"""

def get_initial_resources() -> dict[str, agl.PromptTemplate]:
    return {
        "agent_prompt": agl.PromptTemplate(
            template=AGENT_PROMPT,
            engine="f-string"
        ),
        # Add more prompts for multi-agent systems...
    }
```

### Step 2: Create Agent Factory

Create a factory function that rebuilds your agent(s) with optimized prompts. Works for both single agents and multi-agent swarms.

**Single Agent:**
```python
# training/agent_factory.py
from langchain.agents import create_agent
import agentlightning as agl

def create_agent_with_prompts(resources: agl.NamedResources):
    """Rebuild agent with optimized prompts."""
    agent_prompt = resources["agent_prompt"].format()

    agent = create_agent(
        name="my_agent",
        model=llm,
        system_prompt=agent_prompt,
        tools=[my_tool_1, my_tool_2]
    )
    return agent.compile(checkpointer=MemorySaver())
```

**Multi-Agent Swarm:**
```python
# training/swarm_factory.py
from langchain.agents import create_agent
from langgraph_swarm import create_swarm, create_handoff_tool
import agentlightning as agl

def create_swarm_with_prompts(resources: agl.NamedResources):
    """Rebuild swarm with optimized prompts."""
    triage_prompt = resources["triage_prompt"].format()
    specialist_prompt = resources["specialist_prompt"].format()

    triage_agent = create_agent(
        name="triage_agent",
        model=llm,
        system_prompt=triage_prompt,
        tools=[create_handoff_tool("specialist_agent", "Transfer for specialized tasks")]
    )

    specialist_agent = create_agent(
        name="specialist_agent",
        model=llm,
        system_prompt=specialist_prompt,
        tools=[my_tool]
    )

    workflow = create_swarm([triage_agent, specialist_agent], default_active_agent="triage_agent")
    return workflow.compile(checkpointer=MemorySaver())
```

### Step 3: Implement Reward Function

Define reward weights explicitly in a dictionary for clarity and easy tuning.

```python
# training/reward.py
from langchain_core.messages import AIMessage

# Explicit reward weights - adjust based on your priorities
REWARD_WEIGHTS = {
    "term_matching": 0.30,      # Output contains expected terms
    "tool_calls": 0.25,         # Correct tools were called
    "agent_routing": 0.30,      # Correct agent sequence (for multi-agent)
    "efficiency": 0.15,         # Step count within bounds
}

def extract_trajectory_info(result: dict) -> dict:
    """Extract trajectory info from agent result."""
    messages = result.get("messages", [])

    # Final output
    final_output = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_output = msg.content
            break

    # Tool calls
    tool_calls = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            tool_calls.extend([tc["name"] for tc in msg.tool_calls])

    # Step count
    step_count = sum(1 for msg in messages if isinstance(msg, AIMessage))

    return {
        "final_output": final_output,
        "tool_calls": tool_calls,
        "step_count": step_count,
    }

def calculate_reward(outputs: dict, reference: dict) -> float:
    """Calculate weighted composite reward."""
    rewards = {}

    # 1. Term matching
    expected_terms = reference.get("expected_terms", [])
    if expected_terms:
        final_output = outputs.get("final_output", "").lower()
        matched = sum(1 for t in expected_terms if t.lower() in final_output)
        rewards["term_matching"] = matched / len(expected_terms)

    # 2. Tool calls
    expected_tools = reference.get("expected_tool_calls", [])
    if expected_tools:
        actual_tools = [t for t in outputs.get("tool_calls", []) if not t.startswith("transfer_to_")]
        matched = sum(1 for t in expected_tools if t in actual_tools)
        rewards["tool_calls"] = matched / len(expected_tools)

    # 3. Agent routing (for multi-agent)
    expected_agents = reference.get("expected_agent_sequence", [])
    if expected_agents:
        agent_sequence = outputs.get("agent_sequence", [])
        exp_idx = 0
        for agent in agent_sequence:
            if exp_idx < len(expected_agents) and agent == expected_agents[exp_idx]:
                exp_idx += 1
        rewards["agent_routing"] = exp_idx / len(expected_agents)

    # 4. Efficiency (step count)
    step_count = outputs.get("step_count", 0)
    min_steps = reference.get("min_steps", 1)
    max_steps = reference.get("max_steps", 10)
    if min_steps <= step_count <= max_steps:
        rewards["efficiency"] = 1.0
    elif step_count < min_steps:
        rewards["efficiency"] = step_count / min_steps if min_steps > 0 else 0.0
    else:
        rewards["efficiency"] = max(0.0, 1.0 - (step_count - max_steps) / max_steps)

    # Calculate weighted sum
    total_weight = 0.0
    weighted_sum = 0.0
    for key, score in rewards.items():
        weight = REWARD_WEIGHTS.get(key, 0.0)
        weighted_sum += score * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0
```

### Step 4: Implement LitAgent

```python
# training/lit_agent.py
import uuid
import agentlightning as agl
from typing import TypedDict

class Task(TypedDict):
    prompt: str
    expected_terms: list[str]
    expected_tool_calls: list[str]
    min_steps: int
    max_steps: int

class MyLitAgent(agl.LitAgent[Task]):
    def __init__(self):
        super().__init__()
        self._initial_resources = get_initial_resources()

    def rollout(self, task: Task, resources: agl.NamedResources, rollout: agl.Rollout) -> float:
        # Merge optimized prompt with fixed prompts
        full_resources = dict(self._initial_resources)
        full_resources.update(resources)

        # Build and run agent
        app = create_agent_with_prompts(full_resources)  # or create_swarm_with_prompts
        thread_id = f"training-{uuid.uuid4()}"

        try:
            result = app.invoke(
                {"messages": [{"role": "user", "content": task["prompt"]}]},
                config={"configurable": {"thread_id": thread_id}}
            )
        except Exception as e:
            print(f"Agent error: {e}")
            return 0.0

        outputs = extract_trajectory_info(result)
        return calculate_reward(outputs, task)
```

### Step 5: Create Training Script

**IMPORTANT for Mac**: Set multiprocessing start method to "fork" BEFORE any other imports.

```python
# train_my_agent.py

# ===== CRITICAL: Must be FIRST before any other imports =====
import multiprocessing
try:
    multiprocessing.set_start_method("fork", force=True)
except RuntimeError:
    pass  # Already set
# ============================================================

import os
import argparse
from dotenv import load_dotenv
from openai import AsyncOpenAI
import agentlightning as agl

from training import get_initial_resources, MyLitAgent, load_dataset

load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true"

def main(config_name: str = "full"):
    config = get_config(config_name)

    # Configure OpenRouter client
    client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    # Configure APO
    algo = agl.APO(
        client,
        beam_width=config.beam_width,
        branch_factor=config.branch_factor,
        beam_rounds=config.beam_rounds,
    )

    # Load dataset
    train_data, val_data = load_dataset(config.dataset_name, config.train_split)

    # Configure Trainer
    trainer = agl.Trainer(
        algorithm=algo,
        n_runners=config.n_runners,
        initial_resources=get_initial_resources(),
        adapter=agl.TraceToMessages(),  # Required for LangChain
    )

    # Run training
    trainer.fit(
        agent=MyLitAgent(),
        train_dataset=train_data,
        val_dataset=val_data,
    )

    # Get optimized prompt
    best_prompt = algo.get_best_prompt()
    print(f"Optimized prompt: {best_prompt.template}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", choices=["small", "full"], default="full")
    args = parser.parse_args()
    main(args.config)
```

## Configuration Presets

| Config | beam_width | branch_factor | beam_rounds | n_runners | Use Case |
|--------|------------|---------------|-------------|-----------|----------|
| small  | 1          | 1             | 1           | 4         | Smoke test |
| full   | 4          | 4             | 3           | 4         | Production |

## Step 6: Smoke Test Workflow

**Before running full training, ALWAYS run a smoke test:**

1. **Confirm with user** that code is ready for smoke test
2. **Run small config**: `uv run train_multi_agent.py --config small`
3. **Verify these pass:**
   - [ ] Training script starts without import errors
   - [ ] Dataset loads successfully
   - [ ] At least one rollout completes
   - [ ] Reward calculation returns valid float (0.0-1.0)
   - [ ] No multiprocessing errors on Mac
   - [ ] Training completes without exceptions
   - [ ] Run evaluation on the optimized prompt output of the smoke test training, logged to langsmith.
4. **Report results** to user before proceeding to full training and seek their explicit approval to proceed to full training.

## Step 7: Full APO Training

**Only proceed after smoke test passes and user approves.**

1. **Run full config**: `uv run train_multi_agent.py --config full`
2. **Monitor training progress**:
   - Check LangSmith traces for rollout quality
   - Watch for reward improvements across beam rounds
   - Note any recurring failures in agent behavior
3. **After training completes**:
   - Save optimized prompts to file
   - Run evaluation on optimized prompts vs baseline
   - Compare metrics: reward scores, tool accuracy, routing correctness
4. **Report results to user**:
   - Summary of optimization rounds
   - Before/after reward comparison
   - Optimized prompt output location

## Dataset Format

Tasks must include inputs and expected outputs:

```python
task = {
    "prompt": "I want to book a flight to Paris",
    "expected_terms": ["flight", "paris"],
    "expected_tool_calls": ["search_flights"],
    "expected_agent_sequence": ["Triage Agent", "Booking Router", "Flight Agent"],  # optional, for multi-agent
    "min_steps": 3,
    "max_steps": 8,
}
```

### Loading from LangSmith (Optional)

You can reuse existing LangSmith datasets for APO training. This is useful when you already have evaluation datasets from agent testing.

```python
# training/dataset_loader.py
from langsmith import Client
from typing import TypedDict

class Task(TypedDict):
    prompt: str
    expected_terms: list[str]
    expected_tool_calls: list[str]
    expected_agent_sequence: list[str]
    min_steps: int
    max_steps: int

def load_dataset_from_langsmith(
    dataset_name: str = "my_eval_dataset",
    train_split: float = 0.7
) -> tuple[list[Task], list[Task]]:
    """Load dataset from LangSmith and split into train/val."""
    client = Client()
    examples = list(client.list_examples(dataset_name=dataset_name))

    # Convert LangSmith examples to APO task format
    tasks = []
    for ex in examples:
        task: Task = {
            "prompt": ex.inputs.get("prompt", ""),
            "expected_terms": ex.outputs.get("expected_terms", []),
            "expected_tool_calls": ex.outputs.get("expected_tool_calls", []),
            "expected_agent_sequence": ex.outputs.get("expected_agent_sequence", []),
            "min_steps": ex.outputs.get("min_steps", 1),
            "max_steps": ex.outputs.get("max_steps", 10),
        }
        tasks.append(task)

    # Split into train/val
    split_idx = int(len(tasks) * train_split)
    train_data = tasks[:split_idx]
    val_data = tasks[split_idx:]

    # Ensure at least 1 example in each set
    if not train_data:
        train_data = tasks[:1]
        val_data = tasks[1:] if len(tasks) > 1 else tasks[:1]
    if not val_data:
        val_data = tasks[-1:]

    print(f"Loaded {len(tasks)} examples: {len(train_data)} train, {len(val_data)} val")
    return train_data, val_data
```

**LangSmith Dataset Schema:**
- `inputs`: Must contain `prompt` field (required)
- `outputs`: Task-specific fields that your reward function needs (varies by use case)

The example above shows outputs for a multi-agent travel system. Your outputs will differ based on what your reward function evaluates. Common patterns:
- **Classification tasks**: `expected_label`, `confidence_threshold`
- **SQL agents**: `expected_query`, `ground_truth_result`
- **RAG agents**: `expected_sources`, `expected_answer_keywords`
- **Tool-use agents**: `expected_tool_sequence`, `expected_parameters`

## Environment Variables

```bash
OPENROUTER_API_KEY=...    # For APO algorithm and agents
LANGSMITH_API_KEY=...     # For dataset loading (optional)
LANGSMITH_TRACING=true    # Enable tracing
```

## File Structure

```
project/
├── training/
│   ├── __init__.py
│   ├── config.py          # TrainingConfig dataclass
│   ├── prompts.py         # Initial PromptTemplates
│   ├── agent_factory.py   # Single agent: create_agent_with_prompts()
│   ├── swarm_factory.py   # Multi-agent: create_swarm_with_prompts()
│   ├── lit_agent.py       # LitAgent implementation
│   ├── reward.py          # REWARD_WEIGHTS dict + calculate_reward()
│   └── dataset_loader.py  # Load from LangSmith
├── train_my_agent.py      # Main training script
└── tests/
    └── test_training.py
```

## Common Issues

| Issue | Solution |
|-------|----------|
| `RuntimeError: context already set` | Move multiprocessing.set_start_method to very top of script |
| Low rewards (< 0.3) | Check tool descriptions, verify routing logic |
| Training timeout | Reduce n_runners, increase rollout_batch_timeout |
| ModuleNotFoundError | Run `uv add "agentlightning[apo]"` |

## References

See [reference/api.md](reference/api.md) for detailed API documentation.

**Agent-Lightning:**
- [Agent-Lightning Docs](https://microsoft.github.io/agent-lightning/stable/)
- [APO Algorithm](https://microsoft.github.io/agent-lightning/stable/algorithm-zoo/apo)
- [LitAgent Interface](https://microsoft.github.io/agent-lightning/stable/tutorials/write-agents)
- [Train First Agent Tutorial](https://microsoft.github.io/agent-lightning/stable/how-to/train-first-agent)
- [Train SQL Agent Example](https://microsoft.github.io/agent-lightning/stable/how-to/train-sql-agent)

**LangChain/LangGraph:**
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangGraph Swarm](https://github.com/langchain-ai/langgraph-swarm-py)
- [LangSmith Datasets](https://docs.smith.langchain.com/evaluation/how_to_guides/datasets)
