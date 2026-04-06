#!/usr/bin/env python3
"""Run yaml-vs-json evals 4-14 via Gemini CLI (gemini-2.5-flash)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EVAL_JSON = BASE / "evals" / "evals.json"
GEMINI = "gemini"
MODEL = "gemini-2.5-flash"
RESULTS = BASE / "eval_results" / MODEL


def build_prompt(entry: dict, scenario: Path, out_path: Path, fmt: str) -> str:
    """Rewrite the eval prompt to use absolute file paths."""
    p = entry["prompt"]
    lang = "YAML" if fmt == "yaml" else "JSON"

    # Replace references to the input file with absolute path
    p = p.replace(
        "called `openapi`",
        f"at `{scenario}`",
    )
    p = p.replace(
        "the `openapi` file in this directory",
        f"the file at `{scenario}`",
    )
    # For eval 14, also handle format detection hint
    p = p.replace(
        "If the input is `openapi.yaml` (YAML format)",
        f"If the input is YAML format (the file is at `{scenario}`)",
    )
    p = p.replace(
        "If the input is `openapi.json` (JSON format)",
        f"If the input is JSON format (the file is at `{scenario}`)",
    )

    # Replace output file references with absolute paths
    # Handle specific output filenames first
    out_dir = out_path.parent
    p = p.replace("`output.md`", f"`{out_dir / 'output.md'}`")
    p = p.replace("`output.json`", f"`{out_dir / 'output.json'}`")
    p = p.replace("`output.yaml`", f"`{out_dir / 'output.yaml'}`")

    # Handle generic `output` references (but not the ones already replaced above)
    p = re.sub(
        r'`output`',
        f"`{out_path}`",
        p,
    )

    return p


def run_one(eval_id: int, fmt: str, entry: dict) -> tuple[float, bool]:
    scenario = (
        BASE / "scenario-yaml" / "openapi.yaml"
        if fmt == "yaml"
        else BASE / "scenario-json" / "openapi.json"
    )
    out_dir = RESULTS / f"eval-{eval_id}-{fmt}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine output file based on eval type
    eid = int(entry["id"])
    if eid == 7:
        out_path = out_dir / "output.md"
    elif eid == 14:
        opposite = "json" if fmt == "yaml" else "yaml"
        out_path = out_dir / f"output.{opposite}"
    else:
        out_path = out_dir / f"output.{fmt}"

    prompt = build_prompt(entry, scenario.resolve(), out_path.resolve(), fmt)

    meta = {
        "eval_id": eval_id,
        "eval_name": entry.get("id"),
        "format": fmt,
        "model": MODEL,
        "prompt": prompt,
        "scenario": str(scenario.resolve()),
        "output": str(out_path.resolve()),
    }
    (out_dir / "eval_metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            [GEMINI, "-y", "-m", MODEL, "-p", prompt],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=300,
        )
        elapsed = time.perf_counter() - t0
        returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as e:
        elapsed = time.perf_counter() - t0
        returncode = -1
        stdout = (e.stdout or b"").decode("utf-8", errors="replace")
        stderr = (e.stderr or b"").decode("utf-8", errors="replace") + "\n\nTIMEOUT after 300s"
        print(f"  TIMEOUT after {elapsed:.0f}s", flush=True)

    log_path = out_dir / "gemini_cli.log"
    log_path.write_text(
        f"returncode={returncode}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}",
        encoding="utf-8",
    )
    timing = {
        "duration_seconds": round(elapsed, 3),
        "returncode": returncode,
        "model": MODEL,
    }
    (out_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    ok = returncode == 0 and out_path.is_file()
    return elapsed, ok


def main() -> None:
    data = json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    evals = {e["id"]: e for e in data["evals"]}
    RESULTS.mkdir(parents=True, exist_ok=True)
    summary = []

    eval_ids = list(range(4, 15))
    # Skip already completed runs
    skip = {(4, "yaml"), (4, "json"), (5, "yaml")}
    for eid in eval_ids:
        entry = evals[str(eid)]
        for fmt in ("yaml", "json"):
            if (eid, fmt) in skip:
                print(f"=== eval-{eid}-{fmt} === SKIPPED (already done)", flush=True)
                continue
            print(f"=== eval-{eid}-{fmt} ===", flush=True)
            elapsed, ok = run_one(eid, fmt, entry)
            result = {
                "eval": eid,
                "format": fmt,
                "seconds": round(elapsed, 1),
                "ok": ok,
            }
            summary.append(result)
            print(json.dumps(result), flush=True)
            # Delay between runs to avoid rate limiting
            time.sleep(15)

    (RESULTS / "run_summary_4-14.json").write_text(
        json.dumps(
            {
                "model": MODEL,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "runs": summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("\nDone!", flush=True)


if __name__ == "__main__":
    main()
