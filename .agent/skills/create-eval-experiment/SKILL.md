---
name: create-eval-experiment
description: Set up the directory structure and eval configuration for comparing agent performance across 2 or more scenarios. Use this whenever the user wants to A/B test an agent, benchmark prompt strategies, compare tool usage patterns, or set up a structured experiment where different agent configurations run on the same tasks. Trigger even if the user doesn't use the word "eval" — phrases like "compare two approaches", "test which works better", "see if X or Y is better", or "set up a benchmark" are all good signals.
---

# Create Eval Experiment

Generate the directory structure and eval configuration for comparing agent performance across 2 or more scenarios. The output is intended to be consumed by the `eval-and-improve` skill, which runs the experiment and grades the results.

## Requirements

- A target directory (default: `eval_experiments/<experiment-name>/`)
- At least 2 distinct scenarios to compare

## Procedure

### 1. Identify scenarios

Ask the user (or infer from context) what scenarios to compare. A good scenario pair:

- Tests the same task under different conditions (different prompts, tools, formats, or seed files)
- Has a clear hypothesis about what might differ and why
- Produces output that can be independently verified

If the user mentions a vague topic (e.g., "YAML vs JSON"), probe for specifics: what task will the agent perform? what exactly differs between the scenarios?

### 2. Create the experiment directory

Create the root experiment directory at `eval_experiments/<experiment-name>/`, with this layout:

```
<experiment-name>/
├── evals/
│   └── evals.json
├── scenario-a/       ← rename to match actual scenarios
└── scenario-b/
```

### 3. Write the evals file

Create `evals/evals.json`. Each eval case defines a task that will be run against both scenarios. Write at least 2–3 test cases — a single case rarely gives reliable signal about which scenario performs better.

```json
{
  "skill_name": "<experiment-name>",
  "evals": [
    {
      "id": "1",
      "prompt": "<the exact prompt to send to the agent>",
      "expected_output": [
        "1. <first requirement>",
        "2. <second requirement>",
        "3. <third requirement>"
      ],
      "files": []
    }
  ]
}
```

Guidelines for `expected_output`:

- Use a **numbered list**, one verifiable requirement per item
- Each item must be independently checkable against the agent's output files or stdout
- Be specific — avoid vague criteria like "the output looks correct"
- Think about what a grader can check without running the code (e.g., file exists, field has value X, function is named Y)

### 4. Create scenario directories

For each scenario:

1. Create a subdirectory with a descriptive name (e.g. `scenario-json/`, `scenario-yaml/`, `scenario-with-example/`)
2. Populate it with seed content — the starting state the agent will act on:
   - Input data files, starter code, config files, or a scenario-specific prompt prefix
3. Make sure scenarios differ in a meaningful and **isolated** way — if two scenarios are identical, the experiment will not reveal anything

### 5. Explain the handoff

After creating the structure, tell the user:

- Where the experiment was created
- That they can run it with `eval-and-improve`, pointing it at the experiment directory
- Briefly what will happen: the skill runs each eval prompt against each scenario and grades the outputs

## Best Practices

- **Name scenarios descriptively**: `scenario-json/` is clearer than `scenario-a/`
- **Number all lists in expected_output**: agents and graders follow numbered lists more reliably
- **Keep expected outputs atomic**: one verifiable fact per item; don't bundle requirements
- **Write 2–3+ test cases**: more cases give more reliable signal
- **Use `expected_output` as a single string** (newline-separated numbered list), not an array — this matches the schema `eval-and-improve` expects

## Example

See [evals/evals.json](./evals/evals.json) for a prompt used to evaluate this skill itself.

For a well-structured eval output example, see [template/evals/evals.yaml](../../../../template/evals/evals.yaml).
