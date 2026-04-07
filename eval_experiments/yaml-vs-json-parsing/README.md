# YAML vs JSON Parsing: Agent Format Comparison

## Question

When agents need to read, mutate, and write structured data (e.g., OpenAPI specs), does the file format — YAML vs JSON — affect accuracy, speed, or token usage?

## Setup

- **Task**: Read an OpenAPI 3.0.3 specification, apply mutations, and write the result back in the same format.
- **Evals**: 14 eval sets across two tiers:
  - **Evals 1-3** (basic): Targeted field mutations (changing descriptions, types, enum values, adding/removing fields). 6-7 assertions each.
  - **Evals 4-14** (structural): Complex transformations including list-to-map conversion, schema generation, $ref inlining, spec merging, deep nesting manipulation, key sorting, schema deletion with ref repair, format-specific annotations, cross-format extraction to markdown, and bidirectional YAML/JSON conversion. 6-12 assertions each.
- **Configurations**: Each eval was run once with YAML input/output and once with JSON input/output, using the same underlying OpenAPI spec content.

## Summary

This table summarizes the programmatic grading pass rates across all evaluated models for both YAML and JSON formats.

| Model                  | Overall Pass Rate | YAML Pass Rate | JSON Pass Rate |
| ---------------------- | ----------------- | -------------- | -------------- |
| claude-opus-4-6        | 99.5%             | 100.0%         | 99.0%          |
| gemini-2.5-flash-lite  | 86.6%             | 88.3%          | 84.7%          |
| gemini-3.1-pro-preview | 99.5%             | 100.0%         | 99.1%          |

## Results (claude-opus-4-6, 2026-04-06)

Runs used `claude -p` with `--permission-mode bypassPermissions` and prompts from `evals/evals.json`. Scenarios were copied into temp directories and outputs saved to `eval_results/yaml-vs-json-parsing/claude-opus-4-6/eval-{id}-{yaml|json}/` per `eval_experiments/AGENTS.md`. Outputs were graded with `scripts/programmatic_grade.py`.

**Overall: 217/218 assertions passed (99.5%)**

| Eval                             | YAML               | JSON                | YAML Time (s) | JSON Time (s) |
| -------------------------------- | ------------------ | ------------------- | ------------- | ------------- |
| 1 — basic field mutations        | 6/6                | 6/6                 | 26.0          | 16.0          |
| 2 — enum/extension changes       | 6/6                | 5/6                 | 18.9          | 22.3          |
| 3 — info/constraint changes      | 6/6                | 6/6                 | 15.6          | 19.4          |
| 4 — list-to-map structural       | 11/11              | 11/11               | 60.6          | 21.4          |
| 5 — schema+endpoint addition     | 9/9                | 9/9                 | 67.6          | 25.5          |
| 6 — spec from scratch            | 12/12              | 12/12               | 15.2          | 17.2          |
| 7 — markdown extraction          | 7/7                | 7/7                 | 45.4          | 27.5          |
| 8 — $ref inlining                | 6/6                | 6/6                 | 126.8         | 23.7          |
| 9 — spec merging                 | 10/10              | 10/10               | 62.2          | 30.1          |
| 10 — deep nesting mutations      | 7/7                | 7/7                 | 77.8          | 23.4          |
| 11 — alphabetical key sorting    | 7/7                | 7/7                 | 22.6          | 14.0          |
| 12 — schema deletion+ref repair  | 10/10              | 10/10               | 57.3          | 74.8          |
| 13 — format-specific annotations | 10/10              | 10/10               | 54.1          | 34.2          |
| 14 — cross-format conversion     | 7/7                | 7/7                 | 19.9          | 20.1          |
| **Total**                        | **114/114 (100%)** | **103/104 (99.0%)** | **669.9**     | **369.6**     |

**Cost (proxy for token usage):**

| Eval                             | YAML Cost | JSON Cost | JSON/YAML |
| -------------------------------- | --------- | --------- | --------- |
| 1 — basic field mutations        | $0.055    | $0.133    | 2.39x     |
| 2 — enum/extension changes       | $0.117    | $0.133    | 1.14x     |
| 3 — info/constraint changes      | $0.112    | $0.161    | 1.43x     |
| 4 — list-to-map structural       | $0.327    | $0.149    | 0.46x     |
| 5 — schema+endpoint addition     | $0.283    | $0.173    | 0.61x     |
| 6 — spec from scratch            | $0.085    | $0.126    | 1.48x     |
| 7 — markdown extraction          | $0.155    | $0.201    | 1.30x     |
| 8 — $ref inlining                | $0.422    | $0.160    | 0.38x     |
| 9 — spec merging                 | $0.295    | $0.183    | 0.62x     |
| 10 — deep nesting mutations      | $0.305    | $0.141    | 0.46x     |
| 11 — alphabetical key sorting    | $0.166    | $0.131    | 0.79x     |
| 12 — schema deletion+ref repair  | $0.309    | $0.354    | 1.14x     |
| 13 — format-specific annotations | $0.289    | $0.206    | 0.71x     |
| 14 — cross-format conversion     | $0.176    | $0.181    | 1.03x     |
| **Total**                        | **$3.10** | **$2.43** | **0.78x** |

**Key findings:**

- **Accuracy**: Near-perfect on both formats. The single JSON failure (eval 2) was a dropped trailing period in a string literal — a minor transcription error, not a structural mistake.
- **Speed**: JSON processing was 1.8x faster overall (370s vs 670s). The gap was largest on structural evals (eval 8: 24s JSON vs 127s YAML for $ref inlining). Eval 12 (schema deletion) was an exception where YAML was faster.
- **Cost/Tokens**: JSON was 22% cheaper overall ($2.43 vs $3.10). However, the pattern split by eval complexity:
  - **Basic evals (1-3, 6)**: JSON was _more expensive_ (1.1-2.4x), likely because the JSON spec has more raw characters (braces, quotes, commas) that inflate input tokens.
  - **Structural evals (4-5, 8-11, 13)**: YAML was _more expensive_ (1.3-2.6x), suggesting the model needed more output tokens to write/rewrite YAML correctly for complex transformations.
- **YAML had 100% accuracy** across all 14 evals despite taking longer and costing more.

Graded results: `eval_results/yaml-vs-json-parsing/programmatic_grade_claude-opus-4-6.json`

## Results (gemini-2.5-flash-lite, 2026-04-06)

Runs used `gemini -m gemini-2.5-flash-lite` with `--approval-mode yolo` and prompts from `evals/evals.json`. Outputs graded with `scripts/programmatic_grade.py`. Evals that failed to produce output on the first pass were retried once.

**Overall: 174/201 assertions passed (86.6%)**

| Eval                             | YAML               | JSON              | YAML Time (s) | JSON Time (s) |
| -------------------------------- | ------------------ | ----------------- | ------------- | ------------- |
| 1 — basic field mutations        | 6/6                | 6/6               | 59.7          | 25.2          |
| 2 — enum/extension changes       | 6/6                | ERR               | 14.7          | —             |
| 3 — info/constraint changes      | 6/6                | 6/6               | 23.4          | 44.1          |
| 4 — list-to-map structural       | 10/10              | 3/10              | 91.2          | 143.1         |
| 5 — schema+endpoint addition     | 7/8                | 8/8               | 206.7         | 57.5          |
| 6 — spec from scratch            | 11/11              | 11/11             | 13.0          | 81.3          |
| 7 — markdown extraction          | 7/7                | 6/7               | 40.8          | 79.8          |
| 8 — $ref inlining                | 0/6                | 6/6               | 53.7          | 99.4          |
| 9 — spec merging                 | 9/10               | 9/10              | 73.3          | 45.6          |
| 10 — deep nesting mutations      | 5/6                | 5/6               | 167.3         | 48.3          |
| 11 — alphabetical key sorting    | 7/7                | 7/7               | 15.7          | 19.1          |
| 12 — schema deletion+ref repair  | 7/9                | 6/9               | 53.7          | 199.4         |
| 13 — format-specific annotations | 10/10              | 10/10             | 20.8          | 63.4          |
| 14 — cross-format conversion     | 0/1                | ERR               | 18.0          | —             |
| **Total**                        | **91/103 (88.3%)** | **83/98 (84.7%)** | **851.6**     | **906.3**     |

**Key findings:**

- **Accuracy**: 86.6% overall — significantly lower than claude-opus-4-6 (99.5%). Common failure modes: incomplete $ref inlining (eval 8 YAML), structural mutation errors (eval 4 JSON — 3/10), and empty output files (eval 2 JSON, eval 14).
- **Speed**: Unlike claude-opus-4-6, JSON was _not_ consistently faster. Total times were roughly similar (852s YAML vs 906s JSON). Some evals were dramatically slower in one format vs the other (eval 5: 207s YAML vs 58s JSON; eval 12: 54s YAML vs 199s JSON).
- **Format comparison**: YAML had slightly higher accuracy (88.3% vs 84.7%) — the opposite of claude-opus-4-6 where JSON had slightly lower accuracy. Both formats had evals where the model completely failed (eval 8 YAML: 0/6, eval 4 JSON: 3/10).
- **Reliability**: The model sometimes failed to write output files even when the API call succeeded (3/28 initial runs, resolved by retry for 2 of them). Eval 14 (format conversion) was a complete failure on both formats.

Graded results: `eval_results/yaml-vs-json-parsing/programmatic_grade_gemini-2.5-flash-lite.json`

## Results (gemini-2.5-flash, 2026-04-06)

Runs used the `gemini` CLI with `-m gemini-2.5-flash`, `--approval-mode yolo`, and prompts from `evals/evals.json`. Scenarios were copied into `eval_results/yaml-vs-json-parsing/gemini-2.5-flash/eval-{id}-{yaml|json}/` per `eval_experiments/AGENTS.md`, and outputs were graded with `scripts/programmatic_grade.py`.

**API quota:** The Gemini API returned `QUOTA_EXHAUSTED` (HTTP 429) during the batch. Several runs exited with code 1 after partial tool use; some produced no `output` file. Do not treat the aggregate **60 / 80** programmatic checks as a full end-to-end score for all 14 evals.

**Programmatic pass rate (checks that passed / checks defined in the grader) for runs with a usable artifact:**

| Eval  | YAML                                   | JSON      |
| ----- | -------------------------------------- | --------- |
| 1     | Invalid YAML in `output` (parse error) | 6/6       |
| 2     | 6/6                                    | 6/6       |
| 3     | 6/6                                    | 6/6       |
| 4     | 10/10                                  | 10/10     |
| 5–8   | No output                              | No output |
| 9     | No output                              | 10/10     |
| 10–14 | No output                              | No output |

Graded JSON and logs: `eval_results/yaml-vs-json-parsing/gemini-2.5-flash/programmatic_grade.json` and per-directory `gemini_run.log`. Re-run individual cases after quota resets, for example:

`cd eval_results/yaml-vs-json-parsing/gemini-2.5-flash/eval-5-yaml && gemini -m gemini-2.5-flash -p "$(jq -r '.evals[4].prompt' ../../../../eval_experiments/yaml-vs-json-parsing/evals/evals.json)" --approval-mode yolo`

## Results (gemini-3.1-pro-preview, 2026-04-06)

Runs used a mix of the `gemini` CLI and direct sub-agent invocation to avoid quota limits. Outputs were graded with `scripts/programmatic_grade.py`.

**Overall: 217/218 assertions passed (99.5%)**

| Eval                             | YAML               | JSON                |
| -------------------------------- | ------------------ | ------------------- |
| 1 — basic field mutations        | 6/6                | 6/6                 |
| 2 — enum/extension changes       | 6/6                | 5/6                 |
| 3 — info/constraint changes      | 6/6                | 6/6                 |
| 4 — list-to-map structural       | 10/10              | 10/10               |
| 5 — schema+endpoint addition     | 8/8                | 8/8                 |
| 6 — spec from scratch            | 11/11              | 11/11               |
| 7 — markdown extraction          | 7/7                | 7/7                 |
| 8 — $ref inlining                | 6/6                | 6/6                 |
| 9 — spec merging                 | 10/10              | 10/10               |
| 10 — deep nesting mutations      | 6/6                | 6/6                 |
| 11 — alphabetical key sorting    | 7/7                | 7/7                 |
| 12 — schema deletion+ref repair  | 9/9                | 9/9                 |
| 13 — format-specific annotations | 10/10              | 10/10               |
| 14 — cross-format conversion     | 7/7                | 7/7                 |
| **Total**                        | **109/109 (100%)** | **108/109 (99.1%)** |

**Key findings:**

- **Accuracy**: Near-perfect on both formats (99.5% overall). The single JSON failure (eval 2) was a dropped trailing period in a string literal (`Submit a new customer order` instead of `Submit a new customer order.`), identical to the error made by `claude-opus-4-6`.
- **YAML vs JSON**: YAML had 100% accuracy, while JSON had 99.1%. Both formats are handled exceptionally well by the model.
- **Speed & Cost (First 8 Evals)**: JSON was significantly faster and cheaper. Across the first 8 evals, JSON processing was **~2.7x faster** than YAML (671s vs 1818s). JSON also used **27% fewer input tokens** (190k vs 263k) and **29% fewer output tokens** (5.7k vs 8.1k) compared to YAML. This contrasts with `claude-opus-4-6`, where JSON was sometimes more expensive on basic evals due to curly braces/quotes. For `gemini-3.1-pro-preview`, JSON is a clear winner on both speed and cost.

Graded results: `eval_results/yaml-vs-json-parsing/programmatic_grade_gemini-3.1-pro-preview.json`
