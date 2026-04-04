# YAML vs JSON Parsing: Agent Format Comparison

## Question

When agents need to read, mutate, and write structured data (e.g., OpenAPI specs), does the file format — YAML vs JSON — affect accuracy, speed, or token usage?

## Setup

- **Task**: Read an OpenAPI 3.0.3 specification, apply a set of targeted mutations (changing descriptions, types, enum values, adding/removing fields), and write the mutated spec back in the same format.
- **Evals**: 3 distinct mutation sets, each with 7 assertions checking exact correctness.
- **Configurations**: Each eval was run once with YAML input/output and once with JSON input/output, using the same underlying OpenAPI spec content.
- **Date**: 2026-04-04

---

## Results: Claude Sonnet 4.6

**Model**: claude-sonnet-4-6 (via Claude Code subagents)

| Metric | YAML | JSON | Delta |
|--------|------|------|-------|
| Pass Rate | 100% (21/21) | 100% (21/21) | +0.00 |
| Time (mean) | 59.4s | 77.1s | -17.7s (YAML 23% faster) |
| Tokens (mean) | 19,981 | 24,347 | -4,366 (YAML 18% fewer) |

### Per-Eval Breakdown

| Eval | YAML Time | JSON Time | YAML Tokens | JSON Tokens |
|------|-----------|-----------|-------------|-------------|
| 1: email format + createdAt | 60.9s | 76.2s | 20,004 | 24,379 |
| 2: order status enum + deprecated removal | 58.9s | 75.9s | 19,965 | 24,347 |
| 3: title/version + username length | 58.4s | 79.3s | 19,974 | 24,314 |

---

## Results: Gemini 2.5 Flash

**Model**: gemini-2.5-flash (via Gemini CLI)

| Metric | YAML | JSON | Delta |
|--------|------|------|-------|
| Pass Rate | 90.5% (19/21) | 95.2% (20/21) | -4.7% (JSON slightly better) |
| Time (mean) | 122.4s | 129.0s | -6.6s (YAML slightly faster) |
| Tokens | N/A | N/A | N/A (gemini CLI doesn't report tokens) |

### Per-Eval Breakdown

| Eval | YAML Pass | JSON Pass | YAML Time | JSON Time |
|------|-----------|-----------|-----------|-----------|
| 1: email format + createdAt | 7/7 | 7/7 | 113.8s | 107.3s |
| 2: order status enum + deprecated removal | 7/7 | 6/7 | 122.8s | 105.1s |
| 3: title/version + username length | 5/7 | 7/7 | 130.7s | 174.6s |

### Gemini Failure Details

- **Eval 2 JSON (6/7)**: Dropped the trailing period from `"Submit a new customer order."` → `"Submit a new customer order"`. A precision error on exact string reproduction.
- **Eval 3 YAML (5/7)**: Produced **structurally malformed YAML** — the `username` property key in `CreateUserRequest` was dropped entirely, leaving orphaned `maxLength`, `pattern`, and `description` values with no parent key. This corrupted the document structure, causing both `minLength` and `maxLength` assertions to fail.

---

## Results: Gemini 2.5 Pro

**Model**: gemini-2.5-pro (via Gemini CLI: `gemini -y -m gemini-2.5-pro`)

**Grading**: Same six semantic checks per eval as `scripts/grade_openapi_evals.py` (24 checks total across YAML+JSON; see `eval_results/programmatic_grade_gemini-2.5-pro.json`).

| Metric | YAML | JSON | Delta |
|--------|------|------|-------|
| Pass rate (6-check) | 66.7% (12/18) | 66.7% (12/18) | 0 (tie) |
| Time (mean) | 50.8s | 97.0s | −46.2s (YAML ~48% faster) |
| Tokens | N/A | N/A | N/A (CLI) |

### Per-Eval Breakdown

| Eval | YAML checks | JSON checks | YAML time | JSON time |
|------|-------------|-------------|-----------|-----------|
| 1: email format + createdAt | 0/6 (invalid YAML) | 6/6 | 62.0s | 54.1s |
| 2: order status enum + deprecated | 6/6 | 6/6 | 50.2s | 148.9s |
| 3: title/version + username length | 6/6 | 0/6 (invalid JSON) | 40.3s | 88.1s |

### Gemini 2.5 Pro failure details

- **Eval 1 YAML**: **Invalid YAML** — under `CreateUserRequest.properties`, the `username` key was omitted; `maxLength` / `pattern` / `description` were left at the wrong indentation (same structural pattern as a bad region in `scenario-yaml/openapi.yaml`). PyYAML cannot parse the file.
- **Eval 3 JSON**: **Invalid JSON** — typo on the `password` field: `"format": "password",.` (stray `.` after the comma), so the whole document fails `json.loads`.

---

## Cross-Model Comparison

| | Claude Sonnet 4.6 | Gemini 2.5 Flash | Gemini 2.5 Pro |
|---|---|---|---|
| **YAML accuracy** | 100% (21/21) | 90.5% (19/21) | 66.7% (12/18)\* |
| **JSON accuracy** | 100% (21/21) | 95.2% (20/21) | 66.7% (12/18)\* |
| **YAML mean time** | 59.4s | 122.4s | 50.8s |
| **JSON mean time** | 77.1s | 129.0s | 97.0s |
| **YAML tokens** | 19,981 | N/A | N/A |
| **JSON tokens** | 24,347 | N/A | N/A |
| **Failure mode** | None | YAML: structural corruption; JSON: string precision | YAML: invalid file (eval 1); JSON: invalid file (eval 3) |

\*Pro figures use the six-check programmatic grader; Flash/Claude rows use the original 7-assertion human/subagent rubric for comparability with earlier runs.

---

## Conclusions

1. **Claude Sonnet 4.6 achieves perfect accuracy on both formats.** 100% on all 42 assertions (21 YAML + 21 JSON). No errors of any kind.

2. **Gemini 2.5 Flash has errors on both formats, but the YAML error is worse.** The JSON failure was a minor string precision issue (missing period). The YAML failure was a structural corruption that broke the document — a more severe class of error.

3. **YAML is faster for both models.** Claude: 23% faster with YAML. Gemini: ~5% faster with YAML (though noisier due to rate limit retries).

4. **YAML uses fewer tokens (Claude data).** 18% fewer tokens for YAML vs JSON, driven by format verbosity differences. This was remarkably consistent across all evals (stddev < 35 tokens).

5. **YAML's indentation sensitivity is a risk for weaker models.** Gemini's structural YAML failure (dropping a property key) is the kind of error that can't happen in JSON — JSON's explicit delimiters make structure unambiguous. For models that struggle with whitespace-significant formats, JSON may be safer despite being more verbose.

6. **Gemini 2.5 Pro (six-check rerun) tied YAML vs JSON on pass rate but failed on different evals.** Eval 1 produced unparseable YAML; eval 3 produced unparseable JSON — so neither format was universally safer; the dominant failure was **syntax corruption** in one run each, not systematic preference for YAML or JSON.

## Recommendation

**For Claude: prefer YAML.** It's faster, cheaper (fewer tokens), and just as accurate. The 23% speed improvement and 18% token savings are meaningful at scale.

**For Gemini (and potentially other models): JSON may be safer.** While YAML is still slightly faster, Gemini's structural YAML corruption suggests that JSON's explicit delimiters provide a safety net against whitespace/indentation errors. The tradeoff depends on whether you prioritize speed (YAML) or reliability (JSON).

**General principle**: The best format depends on the model's capability. Strong models benefit from YAML's conciseness; weaker models benefit from JSON's structural explicitness.

## Caveats

- This eval used a single OpenAPI spec of moderate size (~625 lines YAML / ~800 lines JSON). Larger or more deeply nested files may show different results.
- Only 1 run per eval per format per model (no variance measurement across repeated runs). The consistency across the 3 different eval prompts is encouraging but not a substitute for repeated trials.
- The mutations tested were straightforward find-and-replace style changes. More complex structural transformations (reordering, merging, splitting) may behave differently.
- Gemini timing is noisy — some runs hit rate limit retries (5s delays), inflating wall time.
- Token data is unavailable for Gemini (the CLI doesn't report it in headless mode).
