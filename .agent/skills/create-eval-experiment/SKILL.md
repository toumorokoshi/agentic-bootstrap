---
name: create-eval-experiment
description: generate the code and structure to perform an experiment for evaluating agent performance between 2 or more scenarios.
---

# Create Eval Experiment

Generate the code and structure to perform an experiment for evaluating agent performance between 2 or more scenarios.

## Requirements

- A directory. If it is not provided by the user, assumed you should create a new directory under `eval_experiments/`

## Procedure

1. Identify the specific scenarios the user would like to compare for evaluating agent performance.
2. create a new directory under `eval_experiments/` for the experiment.
3. add an evals.json into the root of the directory. It should contain one more experiments, matching the eval experiment the user has specified. Evals should be written in the following format:

```json
{
  "evals": [
    {
      "id": "1",
      "prompt": "",
      "expected_outputs": [
        "{replace these with one or more requirements}",
        "{each entry is treated as it's own requirement}",
      ]
  ]
}
```

4. For each scenario that the user would like to create:
   4a. create a new directory under the experiment directory for that scenario.
   4b. create content in that directory that would be necessary to evaluate the performance of the prompt for that specific scenario.

## Example Prompt

See [evals/eval.json](./evals/evals.json)
