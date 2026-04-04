---
name: create-eval-experiment
description: generate the code and structure to perform an experiment for evaluating agent performance between 2 or more scenarios.
---

# Create Eval Experiment

Generate the directory structure and eval configuration for comparing agent performance across 2 or more scenarios.

## Requirements

- A target directory. If not provided, create one under `eval_experiments/<experiment-name>/`.

## Procedure

### 1. Identify scenarios

Ask the user (or infer from context) the specific scenarios to compare. Each scenario becomes a subdirectory under the experiment with its own seed content for the agent.

### 2. Create the experiment directory

Create the root experiment directory, e.g. `eval_experiments/<experiment-name>/`.

### 3. Write the evals file

Create `evals/evals.json` inside the experiment directory. Prefer JSON. Each eval entry must follow this schema exactly.

```json
{
  "evals": [
    {
      "id": "1",
      "prompt": "<the exact prompt to send to the agent for this test case>",
      "expected_outputs": [
        "<first requirement — write as a numbered list, one item per line>",
        "<second requirement>"
      ],
      "files": []
    }
  ]
}
```

Key rules for `expected_outputs`:

- Use a **numbered list**, one requirement per line.
- Each entry must be independently verifiable (checkable against files or prompt output).
- Be specific — avoid vague criteria like "the output looks correct".

### 4. Create scenario directories

For each scenario:

1. Create a subdirectory under the experiment directory (e.g. `scenario-json/`, `scenario-yaml/`).
2. Populate the directory with seed content that represents the starting state for that scenario:
   - Any seed files the agent should operate on (e.g. input data, starter code, config files).
3. Ensure each scenario directory has materially different seed content — otherwise the comparison is not meaningful.

## Best Practices

- **Number all lists**: agents follow numbered lists more reliably than bullet points.
- **Keep expected outputs atomic**: one verifiable fact per item; do not bundle multiple requirements into one line.
- **Prefer JSON**: `evals.json` is preferred over `evals.yaml`.

## Example

See [evals/evals.json](./evals/evals.json) for an example of a prompt used to evaluate this skill itself.

For an example of a well-structured output, see [template/evals/evals.yaml](../../../../template/evals/evals.yaml).
