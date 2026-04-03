---
name: eval-and-improve
description: Run evaluations iteratively and improve code within a directory. Use this skill whenever the user wants to take a specific directory, run the evals contained within it, and automatically modify files in that directory to fix eval failures. This skill repeats the eval-and-improvement loop until the user is satisfied.
---

# Eval and Improve

A skill for iteratively running evaluations in a specific directory and
automatically modifying the files to improve the evaluation outputs.

## Requirements

Before starting, ensure you have:

1. The path to the specific directory containing the code and evals.
2. Either an `evals/evals.json` file, or an `evals/evals.yaml` file in that directory.
3. The ability to run subagents.

## The Iteration Loop

### 1: find the evals file

Find either the `evals/evals.json` file, or the `evals/evals.yaml` file. Read the contents.

### 2: Start the test loop

For each test found in evals, do the following:

#### 2a. create the evals directory and write an eval.json file

2a-1: create a directory with the eval test case (e.g. `eval_results/test-1/`). Copy the contents of the repository to that directory.

2a-2: write a file, `eval.json` into the root of the directory. It should contains the data for that specific test case. Use the following as a template:

```json
{
  "prompt": "generate a react dashboard.",
  "expected_output": "1. a functional react dashboard is created.",
  "files": []
}
```

### 2b run the eval test case

In a sub-agent, run the eval test case, using "prompt" field from `eval.json` as the prompt to run. Create a file `prompt-output.md` in the test directory with the output of the s

### 2c grade the results

spawn a sub-agent with the following:

```
1. read the eval.json file
2. read through the expected output field. itemize the expected output.
3. for each of the expected output, verify whether the files in the directory match the expected results.
    - If the expected output is looking for output in the prompt, check prompt-output.md
    - If the expected output is looking for output in the files, check the files in the directory.
4. Consider and suggest improvements. keep a running list of the suggestions to write later.
5. on a scale of 1-10, grade the results and how well it matches the expected output. a 1 implies that the output did not match the desird outcome. a 10 implies a perfect match.
  - be very judgemental and do not rate at a 10 easily.
6. produce a summary of the final results in a file, `eval-results.json`, in the test directory. The eval-results should use the following format:

{
    "grade": 5,
    "summary": "",
    "improvements: "",
}
```

## 3 aggregate and group the results

To the user, produce a table summarizing the results of the evals. The table should include the following columns:

- test name
- grade
- summary
- improvements

Prompt the user to request next steps.

## 4 apply improvements

Delete the eval directories created in step 2a.

If the user requests it, apply the improvements to the original directory.

If the user requested it, return back to 2 to perform the loop again.
