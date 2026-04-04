#!/usr/bin/env python3
"""Run yaml-vs-json experiment via Gemini CLI (gemini-2.5-pro)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EVAL_JSON = BASE / "evals" / "evals.json"
GEMINI = "gemini"
MODEL = "gemini-2.5-pro"
RESULTS = BASE / "eval_results" / "gemini-2.5-pro"


def build_prompt(entry: dict, scenario: Path, output: Path, fmt: str) -> str:
    p = entry["prompt"]
    start = p.index("1.")
    end = p.index("Write the mutated spec")
    mutations = p[start:end].strip()
    lang = "YAML" if fmt == "yaml" else "JSON"
    return (
        f"You are given an OpenAPI specification file at {scenario}. "
        f"Read it carefully, then make the following mutations and write the result to {output}:\n\n"
        f"{mutations}\n\n"
        f"Preserve the {lang} format in the output."
    )


def run_one(
    eval_id: int,
    fmt: str,
    entry: dict,
) -> tuple[float, bool]:
    scenario = (
        BASE / "scenario-yaml" / "openapi.yaml"
        if fmt == "yaml"
        else BASE / "scenario-json" / "openapi.json"
    )
    out_dir = RESULTS / f"eval-{eval_id}-{fmt}"
    out_dir.mkdir(parents=True, exist_ok=True)
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
    proc = subprocess.run(
        [
            GEMINI,
            "-y",
            "-m",
            MODEL,
            "-p",
            prompt,
        ],
        cwd=str(BASE),
        capture_output=True,
        text=True,
        timeout=900,
    )
    elapsed = time.perf_counter() - t0
    log_path = out_dir / "gemini_cli.log"
    log_path.write_text(
        f"returncode={proc.returncode}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}",
        encoding="utf-8",
    )
    timing = {
        "duration_seconds": round(elapsed, 3),
        "returncode": proc.returncode,
        "model": MODEL,
    }
    (out_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    ok = proc.returncode == 0 and out_path.is_file()
    return elapsed, ok


def main() -> None:
    data = json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    evals = {e["id"]: e for e in data["evals"]}
    RESULTS.mkdir(parents=True, exist_ok=True)
    summary = []
    for eid in (1, 2, 3):
        entry = evals[str(eid)]
        for fmt in ("yaml", "json"):
            print(f"=== eval-{eid}-{fmt} ===", flush=True)
            elapsed, ok = run_one(eid, fmt, entry)
            summary.append(
                {
                    "eval": eid,
                    "format": fmt,
                    "seconds": round(elapsed, 1),
                    "ok": ok,
                }
            )
            print(json.dumps(summary[-1]), flush=True)

    (RESULTS / "run_summary.json").write_text(
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


if __name__ == "__main__":
    main()
