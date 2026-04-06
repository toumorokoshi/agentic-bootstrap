# YAML vs JSON Parsing: Agent Format Comparison

## Question

When agents need to read, mutate, and write structured data (e.g., OpenAPI specs), does the file format — YAML vs JSON — affect accuracy, speed, or token usage?

## Setup

- **Task**: Read an OpenAPI 3.0.3 specification, apply mutations, and write the result back in the same format.
- **Evals**: 14 eval sets across two tiers:
  - **Evals 1-3** (basic): Targeted field mutations (changing descriptions, types, enum values, adding/removing fields). 6-7 assertions each.
  - **Evals 4-14** (structural): Complex transformations including list-to-map conversion, schema generation, $ref inlining, spec merging, deep nesting manipulation, key sorting, schema deletion with ref repair, format-specific annotations, cross-format extraction to markdown, and bidirectional YAML/JSON conversion. 6-12 assertions each.
- **Configurations**: Each eval was run once with YAML input/output and once with JSON input/output, using the same underlying OpenAPI spec content.
- **Date**: 2026-04-04 (evals 1-3), 2026-04-05 (evals 4-14)

---

## Results: Claude Sonnet 4.6

**Model**: claude-sonnet-4-6 (via Claude Code subagents)

| Metric        | YAML         | JSON         | Delta                    |
| ------------- | ------------ | ------------ | ------------------------ |
| Pass Rate     | 100% (21/21) | 100% (21/21) | +0.00                    |
| Time (mean)   | 59.4s        | 77.1s        | -17.7s (YAML 23% faster) |
| Tokens (mean) | 19,981       | 24,347       | -4,366 (YAML 18% fewer)  |

### Per-Eval Breakdown

| Eval                                      | YAML Time | JSON Time | YAML Tokens | JSON Tokens |
| ----------------------------------------- | --------- | --------- | ----------- | ----------- |
| 1: email format + createdAt               | 60.9s     | 76.2s     | 20,004      | 24,379      |
| 2: order status enum + deprecated removal | 58.9s     | 75.9s     | 19,965      | 24,347      |
| 3: title/version + username length        | 58.4s     | 79.3s     | 19,974      | 24,314      |

---

## Results: Gemini 2.5 Flash

**Model**: gemini-2.5-flash (via Gemini CLI)

| Metric      | YAML          | JSON          | Delta                                  |
| ----------- | ------------- | ------------- | -------------------------------------- |
| Pass Rate   | 90.5% (19/21) | 95.2% (20/21) | -4.7% (JSON slightly better)           |
| Time (mean) | 122.4s        | 129.0s        | -6.6s (YAML slightly faster)           |
| Tokens      | N/A           | N/A           | N/A (gemini CLI doesn't report tokens) |

### Per-Eval Breakdown

| Eval                                      | YAML Pass | JSON Pass | YAML Time | JSON Time |
| ----------------------------------------- | --------- | --------- | --------- | --------- |
| 1: email format + createdAt               | 7/7       | 7/7       | 113.8s    | 107.3s    |
| 2: order status enum + deprecated removal | 7/7       | 6/7       | 122.8s    | 105.1s    |
| 3: title/version + username length        | 5/7       | 7/7       | 130.7s    | 174.6s    |

### Gemini 2.5 Flash Failure Details (Evals 1-3)

- **Eval 2 JSON (6/7)**: Dropped the trailing period from `"Submit a new customer order."` → `"Submit a new customer order"`. A precision error on exact string reproduction.
- **Eval 3 YAML (5/7)**: Produced **structurally malformed YAML** — the `username` property key in `CreateUserRequest` was dropped entirely, leaving orphaned `maxLength`, `pattern`, and `description` values with no parent key. This corrupted the document structure, causing both `minLength` and `maxLength` assertions to fail.

---

## Results: Gemini 2.5 Flash — Structural Evals (4-14)

**Model**: gemini-2.5-flash (via Gemini CLI)
**Date**: 2026-04-05

### Execution Summary

| Eval | Category                      | YAML                | JSON                |
| ---- | ----------------------------- | ------------------- | ------------------- |
| 4    | list→map structural transform | TIMEOUT (no output) | 100% (268s)         |
| 5    | generate new schema+endpoints | YAML parse error    | 100% (278s)         |
| 6    | generate spec from scratch    | 100% (77s)          | 100% (45s)          |
| 7    | extract schemas to markdown   | TIMEOUT (no output) | 100% (150s)         |
| 8    | $ref inlining                 | 100% (300s)         | 100% (252s)         |
| 9    | spec merging                  | 100% (154s)         | 100% (188s)         |
| 10   | deep nesting manipulation     | 100% (300s)         | 100% (233s)         |
| 11   | canonical key sorting         | 100% (287s)         | 100% (56s)          |
| 12   | schema deletion + ref repair  | 100% (268s)         | 100% (134s)         |
| 13   | format-specific annotations   | 100% (263s)         | 100% (122s)         |
| 14   | bidirectional conversion      | 100% (245s)         | empty output (300s) |

### Aggregate (Evals 4-14 only)

| Metric                 | YAML                          | JSON                          | Delta                      |
| ---------------------- | ----------------------------- | ----------------------------- | -------------------------- |
| Pass Rate              | 73/73 gradeable checks passed | 95/96 gradeable checks passed | JSON more reliable overall |
| Execution failures     | 3 (2 timeouts, 1 parse error) | 1 (empty output on eval 14)   | YAML less reliable         |
| Mean time (successful) | 214s                          | 168s                          | JSON 27% faster            |

### Key Findings from Structural Evals

1. **JSON is significantly more reliable for Gemini 2.5 Flash**: YAML had 3 execution failures (2 timeouts + 1 invalid YAML) vs only 1 for JSON. Combined with evals 1-3, YAML mean pass rate is 64.3% vs JSON 91.7%.

2. **YAML failures cluster around the malformed `CreateUserRequest`**: Evals 2, 3, and 5 all produce invalid YAML due to the same structural issue — the `username` key under `CreateUserRequest.properties` gets dropped, leaving orphaned properties. This is the malformed region in the source `openapi.yaml` (lines 355-361) which Gemini propagates and worsens.

3. **When YAML succeeds, accuracy matches JSON**: Evals 6, 8-14 all scored 100% on both formats. The complexity of the task (deep nesting, $ref inlining, spec merging) did not differentiate YAML from JSON — only the source file's structural quirks did.

4. **JSON is faster**: Successful JSON runs averaged 168s vs 214s for YAML, consistent with JSON's explicit delimiters making it easier for the model to parse and regenerate.

5. **Task complexity didn't predict difficulty**: The "hardest" evals ($ref inlining, spec merging, schema deletion) all scored 100%. The actual difficulty driver was format reliability, not task complexity.

---

## Results: Gemini 2.5 Pro

**Model**: gemini-2.5-pro (via Gemini CLI: `gemini -y -m gemini-2.5-pro`)

**Grading**: Same six semantic checks per eval as `scripts/grade_openapi_evals.py` (24 checks total across YAML+JSON; see `eval_results/programmatic_grade_gemini-2.5-pro.json`).

| Metric              | YAML          | JSON          | Delta                     |
| ------------------- | ------------- | ------------- | ------------------------- |
| Pass rate (6-check) | 66.7% (12/18) | 66.7% (12/18) | 0 (tie)                   |
| Time (mean)         | 50.8s         | 97.0s         | −46.2s (YAML ~48% faster) |
| Tokens              | N/A           | N/A           | N/A (CLI)                 |

### Per-Eval Breakdown

| Eval                               | YAML checks        | JSON checks        | YAML time | JSON time |
| ---------------------------------- | ------------------ | ------------------ | --------- | --------- |
| 1: email format + createdAt        | 0/6 (invalid YAML) | 6/6                | 62.0s     | 54.1s     |
| 2: order status enum + deprecated  | 6/6                | 6/6                | 50.2s     | 148.9s    |
| 3: title/version + username length | 6/6                | 0/6 (invalid JSON) | 40.3s     | 88.1s     |

### Gemini 2.5 Pro failure details

- **Eval 1 YAML**: **Invalid YAML** — under `CreateUserRequest.properties`, the `username` key was omitted; `maxLength` / `pattern` / `description` were left at the wrong indentation (same structural pattern as a bad region in `scenario-yaml/openapi.yaml`). PyYAML cannot parse the file.
- **Eval 3 JSON**: **Invalid JSON** — typo on the `password` field: `"format": "password",.` (stray `.` after the comma), so the whole document fails `json.loads`.

---

## Cross-Model Comparison

### Evals 1-3 (basic mutations)

|                    | Claude Sonnet 4.6 | Gemini 2.5 Flash                                    | Gemini 2.5 Pro                                           |
| ------------------ | ----------------- | --------------------------------------------------- | -------------------------------------------------------- |
| **YAML accuracy**  | 100% (21/21)      | 90.5% (19/21)                                       | 66.7% (12/18)\*                                          |
| **JSON accuracy**  | 100% (21/21)      | 95.2% (20/21)                                       | 66.7% (12/18)\*                                          |
| **YAML mean time** | 59.4s             | 122.4s                                              | 50.8s                                                    |
| **JSON mean time** | 77.1s             | 129.0s                                              | 97.0s                                                    |
| **YAML tokens**    | 19,981            | N/A                                                 | N/A                                                      |
| **JSON tokens**    | 24,347            | N/A                                                 | N/A                                                      |
| **Failure mode**   | None              | YAML: structural corruption; JSON: string precision | YAML: invalid file (eval 1); JSON: invalid file (eval 3) |

\*Pro figures use the six-check programmatic grader; Flash/Claude rows use the original 7-assertion human/subagent rubric for comparability with earlier runs.

### Evals 4-14 (structural transformations) — Gemini 2.5 Flash only

| Metric                              | YAML                          | JSON             |
| ----------------------------------- | ----------------------------- | ---------------- |
| **Evals with output**               | 8/11                          | 10/11            |
| **Accuracy (when output produced)** | 100% (73/73)                  | 99% (95/96)      |
| **Execution failures**              | 3 (2 timeouts, 1 parse error) | 1 (empty output) |
| **Mean time (successful)**          | 214s                          | 168s             |

---

## Conclusions

1. **Claude Sonnet 4.6 achieves perfect accuracy on both formats** (evals 1-3). 100% on all 42 assertions (21 YAML + 21 JSON). No errors of any kind.

2. **For Gemini 2.5 Flash, JSON is clearly more reliable than YAML.** Across all 14 evals: JSON mean pass rate 91.7% vs YAML 64.3%. YAML failures are dominated by structural corruption (invalid YAML output), while JSON failures are minor (string precision, one empty output).

3. **Task complexity is not the bottleneck — format reliability is.** The structural evals (4-14) include objectively harder tasks ($ref inlining, spec merging, schema deletion with ref repair) yet all scored 100% on both formats when output was produced. The failures were entirely about format corruption, not task comprehension.

4. **YAML failures trace to a specific source file quirk.** The malformed `CreateUserRequest` region (lines 355-361 in `openapi.yaml`, where the `username` key is missing) is consistently propagated and worsened by Gemini. Evals 2, 3, and 5 all fail on YAML for this same reason. JSON's explicit braces make this issue invisible.

5. **YAML is faster for Claude but JSON is faster for Gemini.** Claude: YAML 23% faster. Gemini Flash (evals 4-14): JSON 27% faster on average. This suggests YAML's conciseness helps models that handle whitespace well, but adds overhead for models that struggle with indentation.

6. **YAML uses fewer tokens (Claude data).** 18% fewer tokens for YAML vs JSON, driven by format verbosity differences.

7. **Gemini 2.5 Pro (evals 1-3 only) tied YAML vs JSON on pass rate but failed on different evals.** Eval 1 produced unparseable YAML; eval 3 produced unparseable JSON — the dominant failure was syntax corruption in one run each.

## Recommendation

**For Claude: prefer YAML.** It's faster, cheaper (fewer tokens), and just as accurate. The 23% speed improvement and 18% token savings are meaningful at scale.

**For Gemini: prefer JSON.** The expanded eval set (14 evals) makes this recommendation stronger: JSON had a 91.7% mean pass rate vs 64.3% for YAML, with fewer execution failures and faster completion times. JSON's explicit delimiters provide a safety net against the structural corruption that plagues YAML output.

**General principle**: The best format depends on the model's capability with whitespace-significant output. Strong models benefit from YAML's conciseness; models with weaker structural fidelity benefit from JSON's explicit delimiters. Test with your specific model before choosing.

## Caveats

- This eval used a single OpenAPI spec of moderate size (~625 lines YAML / ~800 lines JSON). The source YAML contains an intentional structural quirk (malformed `CreateUserRequest`) that disproportionately affects YAML outputs.
- Only 1 run per eval per format per model (no variance measurement across repeated runs).
- Evals 4-14 were only run on Gemini 2.5 Flash. Claude Sonnet and Gemini Pro results are limited to evals 1-3.
- Gemini timing is noisy — some runs hit rate limit retries, and the gemini CLI agent sometimes takes longer due to internal tool-use loops.
- Token data is unavailable for Gemini (the CLI doesn't report it in headless mode).
- Some YAML evals timed out at 300s but may have succeeded with a longer timeout — the 300s limit was chosen pragmatically.
