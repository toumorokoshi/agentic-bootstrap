#!/usr/bin/env python3
"""Programmatically grade OpenAPI mutation outputs for evals 1–3 (yaml-vs-json experiment)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:
    print("Requires PyYAML: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1) from e

EXPECTED = {
    1: {
        "user_desc": "Retrieves a single user by their unique identifier.",
        "limit_desc": "Maximum number of users to return per page.",
    },
    2: {
        "post_orders_summary": "Submit a new customer order.",
        "order_status": [
            "pending",
            "confirmed",
            "in_transit",
            "fulfilled",
            "cancelled",
        ],
    },
    3: {
        "title": "Acme Commerce Platform API",
        "version": "2.0.0",
        "product_id_desc": "The globally unique identifier of the product.",
        "username_min": 5,
        "username_max": 32,
    },
}


def load_spec(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Root must be object, got {type(data)}")
    return data


def has_key_recursive(obj: Any, key: str) -> bool:
    if isinstance(obj, dict):
        if key in obj:
            return True
        return any(has_key_recursive(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(has_key_recursive(v, key) for v in obj)
    return False


def param_by_name(params: list[dict[str, Any]] | None, name: str) -> dict[str, Any] | None:
    if not params:
        return None
    for p in params:
        if p.get("name") == name:
            return p
    return None


def schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def check_eval_1(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    paths = spec.get("paths", {})
    u = paths.get("/users/{userId}", {}).get("get", {})
    d = u.get("description")
    out.append(
        (
            "GET /users/{userId} description",
            d == EXPECTED[1]["user_desc"],
            f"got {d!r}",
        )
    )
    su = schemas(spec).get("User", {})
    props = su.get("properties", {})
    email = props.get("email", {})
    out.append(
        (
            "User.email format email",
        email.get("format") == "email",
        f"format={email.get('format')!r}",
        )
    )
    age = props.get("age", {})
    out.append(
        (
            "User.age type number",
            age.get("type") == "number",
            f"type={age.get('type')!r}",
        )
    )
    ca = props.get("createdAt", {})
    out.append(
        (
            "createdAt type + date-time",
            ca.get("type") == "string" and ca.get("format") == "date-time",
            f"{ca!r}",
        )
    )
    req = su.get("required") or []
    out.append(
        (
            "createdAt in User.required",
            "createdAt" in req,
            f"required={req!r}",
        )
    )
    lu = paths.get("/users", {}).get("get", {})
    lim = param_by_name(lu.get("parameters"), "limit")
    ld = (lim or {}).get("description")
    out.append(
        (
            "GET /users limit description",
            ld == EXPECTED[1]["limit_desc"],
            f"got {ld!r}",
        )
    )
    return out


def check_eval_2(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    paths = spec.get("paths", {})
    post = paths.get("/orders", {}).get("post", {})
    summ = post.get("summary")
    exp = EXPECTED[2]["post_orders_summary"]
    out.append(
        (
            "POST /orders summary exact",
            summ == exp,
            f"got {summ!r} expected {exp!r}",
        )
    )
    oi = schemas(spec).get("OrderItem", {}).get("properties", {}).get("quantity", {})
    out.append(
        (
            "OrderItem.quantity type number",
            oi.get("type") == "number",
            f"type={oi.get('type')!r}",
        )
    )
    out.append(
        (
            "OrderItem.quantity minimum 0.1",
            oi.get("minimum") == 0.1,
            f"minimum={oi.get('minimum')!r}",
        )
    )
    legacy = paths.get("/products/legacy", {}).get("get", {})
    out.append(
        (
            "GET /products/legacy no deprecated",
            not has_key_recursive(legacy, "deprecated"),
            "deprecated found under operation" if has_key_recursive(legacy, "deprecated") else "ok",
        )
    )
    st = schemas(spec).get("Order", {}).get("properties", {}).get("status", {})
    enum = st.get("enum") or []
    exp_e = EXPECTED[2]["order_status"]
    out.append(
        (
            "Order.status enum exact",
            enum == exp_e,
            f"got {enum!r}",
        )
    )
    del_op = paths.get("/users/{userId}", {}).get("delete", {})
    out.append(
        (
            "DELETE /users/{userId} x-internal",
            del_op.get("x-internal") is True,
            f"x-internal={del_op.get('x-internal')!r}",
        )
    )
    return out


def check_eval_3(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    info = spec.get("info", {})
    out.append(
        (
            "info.title",
            info.get("title") == EXPECTED[3]["title"],
            f"got {info.get('title')!r}",
        )
    )
    out.append(
        (
            "info.version",
            info.get("version") == EXPECTED[3]["version"],
            f"got {info.get('version')!r}",
        )
    )
    paths = spec.get("paths", {})
    gpp = paths.get("/products/{productId}", {}).get("get", {})
    params = gpp.get("parameters") or []
    pid = param_by_name(params, "productId")
    pd = (pid or {}).get("description")
    exp = EXPECTED[3]["product_id_desc"]
    out.append(
        (
            "productId parameter description",
            pd == exp,
            f"got {pd!r}",
        )
    )
    un = (
        schemas(spec)
        .get("CreateUserRequest", {})
        .get("properties", {})
        .get("username", {})
    )
    out.append(
        (
            "CreateUserRequest.username minLength",
            un.get("minLength") == EXPECTED[3]["username_min"],
            f"minLength={un.get('minLength')!r}",
        )
    )
    out.append(
        (
            "CreateUserRequest.username maxLength",
            un.get("maxLength") == EXPECTED[3]["username_max"],
            f"maxLength={un.get('maxLength')!r}",
        )
    )
    mn = schemas(spec).get("User", {}).get("properties", {}).get("middleName", {})
    out.append(
        (
            "User.middleName nullable true",
            mn.get("nullable") is True,
            f"nullable={mn.get('nullable')!r}",
        )
    )
    return out


CHECKERS = {1: check_eval_1, 2: check_eval_2, 3: check_eval_3}


CHECKS_PER_EVAL = {1: 6, 2: 6, 3: 6}


def grade_file(path: Path, eval_id: int) -> dict[str, Any]:
    fn = CHECKERS[eval_id]
    nchecks = CHECKS_PER_EVAL[eval_id]
    try:
        spec = load_spec(path)
    except Exception as e:
        return {
            "path": str(path),
            "eval_id": eval_id,
            "error": str(e),
            "passed": 0,
            "failed": nchecks,
            "total": nchecks,
            "pass_rate": 0.0,
            "checks": [
                {
                    "name": "document parses (YAML/JSON)",
                    "passed": False,
                    "detail": str(e),
                }
            ],
        }
    checks = fn(spec)
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    return {
        "path": str(path),
        "eval_id": eval_id,
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": passed / total if total else 0.0,
        "checks": [{"name": n, "passed": ok, "detail": d} for n, ok, d in checks],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "root",
        type=Path,
        help="Directory containing eval-N-yaml and eval-N-json subdirs",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    results: list[dict[str, Any]] = []
    for fmt in ("yaml", "json"):
        for eid in (1, 2, 3):
            sub = root / f"eval-{eid}-{fmt}"
            out = sub / f"output.{fmt}"
            if not out.is_file():
                results.append(
                    {
                        "path": str(out),
                        "eval_id": eid,
                        "format": fmt,
                        "error": "missing file",
                        "pass_rate": 0.0,
                    }
                )
                continue
            g = grade_file(out, eid)
            g["format"] = fmt
            results.append(g)

    passed = sum(
        r.get("passed", 0)
        for r in results
        if "passed" in r and "error" not in r
    )
    total = sum(r.get("total", 0) for r in results if "total" in r)
    yaml_rates = [r["pass_rate"] for r in results if r.get("format") == "yaml" and "pass_rate" in r]
    json_rates = [r["pass_rate"] for r in results if r.get("format") == "json" and "pass_rate" in r]
    summary = {
        "root": str(root),
        "assertions_passed": passed,
        "assertions_total": total,
        "overall_pass_rate": passed / total if total else 0.0,
        "yaml_mean_pass_rate": sum(yaml_rates) / len(yaml_rates) if yaml_rates else None,
        "json_mean_pass_rate": sum(json_rates) / len(json_rates) if json_rates else None,
        "runs": results,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
