---
name: eval-and-improve
description: Run evaluations iteratively and improve code within a directory. This skill repeats the eval-and-improvement loop until the user is satisfied.
---

# Eval and Improve

A skill for iteratively running evaluations in a specific directory and
automatically modifying the files to improve the evaluation outputs.

## Requirements

Before starting, ensure you have:

1. The path to the specific directory containing the code and evals.
2. Either an `evals/evals.json` file, or an `evals/evals.yaml` file in that directory.
3. The ability to run subagents.

## Procedure

### 1: find the evals file

Find either the `evals/evals.json` file, or the `evals/evals.yaml` file. Read the contents.

### 2: Start the test loop

Create a sibling directory, `eval_results` to the target directory. All copied
and generated files will be within that directory.

For each test found in evals, do the following:

#### 2a. create the evals directory and write an eval.json file

2a-1: create a directory with the eval test case (e.g. `eval_results/test-1/`). Copy the contents of the repository to that directory.

2a-2: write a file, `eval.json` into the root of the directory. It should contains the data for that specific test case. Use the following as a template:

```json
{
  "prompt": "{include the prompt from the test case in evals.json here}.",
  "expected_output": [
    "1. <first requirement>",
    "2. <second requirement>",
    "3. <third requirement>"
  ],
  "files": []
}
```

### 2b run the eval test case

In a general-purpose sub-agent, run the eval test case in the test case directory, using "prompt" field from `eval.json` as the prompt to run. Do \_not\* modify the prompt - use it as-is, and _do not_ use plan mode: the agent should execute the prompt directly.

Create a file `prompt-output.md` in the test directory with the output of the s

### 2c grade the results

spawn a general-purpose sub-agent with the following prompt. Do _not_ use plan mode:

```
1. read the eval.json file
2. read through the expected output field. itemize the expected output.
3. for each of the expected output, verify whether the files in the directory match the expected results.
    - If the expected output is looking for output in the prompt, check prompt-output.md
    - If the expected output is looking for output in the files, check the files in the directory.
4. Consider and suggest to the *original* directory that would have improved the agent's behavior, since are evaluating the original directory's prompts and code to ensure better generated code. keep a running list of the suggestions to write later.
5. on a scale of 1-10, grade the results and how well it matches the expected output. a 1 implies that the output did not match the desird outcome. a 10 implies a perfect match.
  - only grade the results based on the expected output. Do not grade it based on any other aspect.
  - for each expected output, include a description of whether it was met or not in the summary.
  - be very judgemental and do not rate at a 10 easily.
6. produce a summary of the final results in a file, `eval-results.json`, in the test directory. The eval-results should use the following format:

{
    "grade": 5,
    "summary": "",
    "improvements": "",
}
```

7. on completion, output the path to the `eval-results.json` file.

## 3 aggregate and group the results

To the user, produce a table summarizing the results of the evals. The table should include the following columns:

- test name
- grade
- summary
- improvements

Prompt the user to request next steps.

## 4 apply improvements

If the user requests it, apply the improvements to the original directory.

When improvements are applied:

1. run linting and tests to ensure no regressions were introduced.
2. delete the eval directories created in step 2a.

If the user requested it, return back to Step 2 to perform the loop again.

## Best Practices

When running evaluations and improvements, keep these best practices in mind:

- **Be very judgemental**: do not rate at a 10 easily. Grades should reflect the quality and completeness of the solution.
- **Provide clear evidence**: always point to specific files or lines that justify the grade.
- **Group similar improvements**: to reduce redundant work and make reviews easier for the user.
- **Check for regressions**: always verify that improvements didn't break existing functionality by running tests (if available).
- **Maintain isolation**: always work in separate directories for each test case to avoid side effects.
- **Save results**: ensure the evaluation results are saved in a machine-readable format before proceeding to the next step.
- **Iterate**: do not expect a perfect result on the first try. Use user feedback to refine the approach.

### Agent Principles

When modifying code to improve it, always adhere to the following principles:

- **Prefer functional programming**: keep state separate from logic.
- **Minimize comments**: only add them if the code is not self-explanatory.
- **IO separation**: wrap IO in functions that work on pure data structures.
- **Test data structures**: write unit tests for logic directly, not through IO layers.
- **Composition over inheritance**: build complex behavior by combining simpler parts.
- **Use constants**: avoid hard-coded values for directories or configuration.
- **Minimal logic in helpers**: keeps functions small and easy to test.
