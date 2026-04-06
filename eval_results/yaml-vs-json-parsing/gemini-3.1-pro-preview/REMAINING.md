# gemini-3.1-pro-preview eval status

## Completed (22/28)
All 14 YAML evals and JSON evals 1-8 are done with output files.

## Remaining (6 evals — all JSON format)
- eval-9-json (spec merging)
- eval-10-json (deep nesting mutations)
- eval-11-json (alphabetical key sorting)
- eval-12-json (schema deletion+ref repair)
- eval-13-json (format-specific annotations)
- eval-14-json (cross-format conversion)

## How to run the remaining evals
The runner script at `/tmp/yaml-vs-json-eval/run_gemini_pro.sh` has skip logic — it will
automatically skip any eval that already has a non-empty output file. Just run:

```bash
cd /tmp/yaml-vs-json-eval && bash run_gemini_pro.sh
```

If quota hits again, wait a few minutes and rerun. The script stops on quota errors
so no work is lost.

After all 28 evals complete, grade with:
```bash
python3 eval_experiments/yaml-vs-json-parsing/scripts/programmatic_grade.py \
  eval_results/yaml-vs-json-parsing/gemini-3.1-pro-preview
```

Then update `eval_experiments/yaml-vs-json-parsing/README.md` with the results.

## Partial results (22 evals)
Current grading: 144/146 assertions passed (98.6%)
- YAML: 100% (all 14 evals)
- JSON (evals 1-8 only): 1 failure — missing trailing period in eval-2-json summary string
