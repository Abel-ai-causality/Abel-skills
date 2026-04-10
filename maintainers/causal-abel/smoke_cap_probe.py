#!/usr/bin/env python3
"""Maintainer smoke runner for the rendered causal-abel CAP probe."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILL_ROOT = REPO_ROOT / "dist" / "local" / "causal-abel"
DEFAULT_ASSETS = (
    "BTCM",
    "RIOT",
    "CAN",
    "PFLT",
    "LFST",
    "CMPS",
)

QUERY_EXPECTATIONS: tuple[dict[str, Any], ...] = (
    {
        "query": "consumer price index",
        "mode": "lexical",
        "expected_prefix": ("CPI",),
        "required_nodes": (),
    },
    {
        "query": "consumer price index",
        "mode": "semantic",
        "expected_prefix": ("CPI",),
        "required_nodes": (),
    },
    {
        "query": "consumer price index",
        "mode": "hybrid",
        "expected_prefix": ("CPI",),
        "required_nodes": ("inflationRate",),
    },
    {
        "query": "10 year treasury yield",
        "mode": "hybrid",
        "expected_prefix": (
            "treasuryRateYear10",
            "PFLT.price",
            "PFLT.volume",
        ),
        "required_nodes": (),
    },
    {
        "query": "gross domestic product",
        "mode": "hybrid",
        "expected_prefix": ("GDP",),
        "required_nodes": ("realGDP",),
    },
    {
        "query": "bitcoin mining stocks",
        "mode": "hybrid",
        "expected_prefix": (
            "BTCM.price",
            "BTCM.volume",
            "RIOT.price",
            "RIOT.volume",
            "industrialProductionTotalIndex",
        ),
        "required_nodes": (),
    },
    {
        "query": "consumer stress",
        "mode": "hybrid",
        "expected_prefix": (
            "LFST.price",
            "LFST.volume",
            "CMPS.price",
            "CMPS.volume",
            "commercialBankInterestRateOnCreditCardPlansAllAccounts",
        ),
        "required_nodes": (),
    },
)


def build_cap_probe_command(skill_root: Path, probe_args: Sequence[str]) -> list[str]:
    return [
        "python3",
        str(skill_root / "scripts" / "cap_probe.py"),
        "--compact",
        *probe_args,
    ]


def extract_variable_node_ids(payload: dict[str, Any]) -> list[str]:
    result = payload.get("result")
    if not isinstance(result, dict):
        return []

    variables = result.get("variables")
    if not isinstance(variables, list):
        return []

    out: list[str] = []
    for item in variables:
        if not isinstance(item, dict):
            continue
        node_id = item.get("node_id")
        if isinstance(node_id, str) and node_id:
            out.append(node_id)
    return out


def evaluate_ranked_nodes(
    actual: Sequence[str],
    *,
    expected_prefix: Sequence[str] = (),
    required_nodes: Sequence[str] = (),
) -> list[str]:
    failures: list[str] = []
    if expected_prefix:
        actual_prefix = list(actual[: len(expected_prefix)])
        expected_prefix_list = list(expected_prefix)
        if actual_prefix != expected_prefix_list:
            failures.append(
                f"expected prefix {expected_prefix_list!r}, got {actual_prefix!r}"
            )

    missing_required = [node for node in required_nodes if node not in actual]
    if missing_required:
        failures.append(f"missing required nodes {missing_required!r}")

    return failures


def _run_cap_probe(skill_root: Path, probe_args: Sequence[str]) -> dict[str, Any]:
    command = build_cap_probe_command(skill_root, probe_args)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    raw_output = (completed.stdout or completed.stderr).strip()
    try:
        payload = json.loads(raw_output) if raw_output else {}
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "status_code": -1,
            "message": "cap_probe.py returned non-JSON output",
            "raw_output": raw_output,
        }

    return {
        "command": command,
        "exit_code": completed.returncode,
        "payload": payload,
        "stderr": (completed.stderr or "").strip(),
    }


def _run_query_checks(skill_root: Path, top_k: int) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for case in QUERY_EXPECTATIONS:
        probe_args = [
            "verb",
            "extensions.abel.query_node",
            "--params-json",
            json.dumps(
                {
                    "search": case["query"],
                    "search_mode": case["mode"],
                    "top_k": top_k,
                },
                ensure_ascii=False,
            ),
        ]
        execution = _run_cap_probe(skill_root, probe_args)
        payload = execution["payload"]
        variable_node_ids = extract_variable_node_ids(payload)
        failures = []
        if execution["exit_code"] != 0 or payload.get("ok") is not True:
            failures.append(payload.get("message") or "query probe failed")
        failures.extend(
            evaluate_ranked_nodes(
                variable_node_ids,
                expected_prefix=case["expected_prefix"],
                required_nodes=case["required_nodes"],
            )
        )
        checks.append(
            {
                "query": case["query"],
                "mode": case["mode"],
                "command": execution["command"],
                "exit_code": execution["exit_code"],
                "status_code": payload.get("status_code"),
                "ok": payload.get("ok"),
                "variable_node_ids": variable_node_ids,
                "failures": failures,
            }
        )
    return checks


def _run_observe_checks(skill_root: Path, assets: Sequence[str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for asset in assets:
        execution = _run_cap_probe(skill_root, ["observe-dual", asset])
        payload = execution["payload"]
        price_payload = payload.get("price_observe")
        volume_payload = payload.get("volume_observe")
        failures = []
        if execution["exit_code"] != 0 or payload.get("ok") is not True:
            failures.append(payload.get("message") or "observe-dual failed")
        checks.append(
            {
                "asset": asset,
                "command": execution["command"],
                "exit_code": execution["exit_code"],
                "ok": payload.get("ok"),
                "recommended_primary_anchor": payload.get("recommended_primary_anchor"),
                "price_ok": isinstance(price_payload, dict) and price_payload.get("ok") is True,
                "price_message": price_payload.get("message") if isinstance(price_payload, dict) else None,
                "volume_ok": isinstance(volume_payload, dict) and volume_payload.get("ok") is True,
                "volume_message": volume_payload.get("message") if isinstance(volume_payload, dict) else None,
                "failures": failures,
            }
        )
    return checks


def _connected_pairs(
    skill_root: Path,
    assets: Sequence[str],
    *,
    max_connected_pairs: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    pairs: list[dict[str, Any]] = []
    failures: list[str] = []

    for source in assets:
        for target in assets:
            if source == target:
                continue
            execution = _run_cap_probe(
                skill_root,
                ["paths", f"{source}.price", f"{target}.price", "--max-paths", "1"],
            )
            payload = execution["payload"]
            result = payload.get("result") if isinstance(payload, dict) else None
            if execution["exit_code"] != 0 or payload.get("ok") is not True:
                failures.append(
                    f"paths {source}.price -> {target}.price failed: "
                    f"{payload.get('message') or 'unknown error'}"
                )
                continue
            if not isinstance(result, dict) or result.get("connected") is not True:
                continue
            pairs.append(
                {
                    "source": source,
                    "target": target,
                    "path_count": result.get("path_count"),
                }
            )
            if len(pairs) >= max_connected_pairs:
                return pairs, failures

    return pairs, failures


def _run_intervention_checks(
    skill_root: Path,
    connected_pairs: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    for pair in connected_pairs:
        source = pair["source"]
        target = pair["target"]
        intervene_do = _run_cap_probe(
            skill_root,
            [
                "intervene-do",
                f"{source}.price",
                "0.05",
                "--outcome-node",
                f"{target}.price",
                "--max-paths",
                "1",
            ],
        )
        intervene_lag = _run_cap_probe(
            skill_root,
            [
                "intervene-time-lag",
                f"{source}.price",
                "0.05",
                f"{target}.price",
                "--horizon-steps",
                "24",
                "--model",
                "linear",
            ],
        )

        do_payload = intervene_do["payload"]
        lag_payload = intervene_lag["payload"]
        lag_result = lag_payload.get("result") if isinstance(lag_payload, dict) else None

        failures: list[str] = []
        if intervene_do["exit_code"] != 0 or do_payload.get("ok") is not True:
            failures.append(do_payload.get("message") or "intervene-do failed")
        if intervene_lag["exit_code"] != 0 or lag_payload.get("ok") is not True:
            failures.append(lag_payload.get("message") or "intervene-time-lag failed")

        lag_reachable = None
        lag_path_count = None
        lag_effect_support = None
        if isinstance(lag_result, dict):
            lag_reachable = lag_result.get("reachable")
            lag_path_count = lag_result.get("path_count")
            lag_effect_support = lag_result.get("effect_support")

        if lag_reachable is False and lag_effect_support == "no_structural_path":
            warnings.append(
                f"{source}.price -> {target}.price is connected in graph.paths "
                "but intervene_time_lag reported no_structural_path"
            )

        checks.append(
            {
                "source": source,
                "target": target,
                "path_count": pair.get("path_count"),
                "intervene_do_ok": do_payload.get("ok"),
                "intervene_do_effect": (
                    do_payload.get("result", {}).get("effect")
                    if isinstance(do_payload.get("result"), dict)
                    else None
                ),
                "intervene_time_lag_ok": lag_payload.get("ok"),
                "intervene_time_lag_reachable": lag_reachable,
                "intervene_time_lag_path_count": lag_path_count,
                "intervene_time_lag_effect_support": lag_effect_support,
                "failures": failures,
            }
        )

    return checks, warnings


def _build_report(
    skill_root: Path,
    assets: Sequence[str],
    top_k: int,
    max_connected_pairs: int,
) -> dict[str, Any]:
    query_checks = _run_query_checks(skill_root, top_k)
    observe_checks = _run_observe_checks(skill_root, assets)
    connected_pairs, path_failures = _connected_pairs(
        skill_root,
        assets,
        max_connected_pairs=max_connected_pairs,
    )
    intervention_checks, warnings = _run_intervention_checks(skill_root, connected_pairs)

    failure_count = (
        sum(bool(item["failures"]) for item in query_checks)
        + sum(bool(item["failures"]) for item in observe_checks)
        + len(path_failures)
        + sum(bool(item["failures"]) for item in intervention_checks)
    )

    return {
        "skill_root": str(skill_root),
        "query_checks": query_checks,
        "observe_checks": observe_checks,
        "connected_pairs": connected_pairs,
        "path_failures": path_failures,
        "intervention_checks": intervention_checks,
        "warnings": warnings,
        "summary": {
            "query_failures": sum(bool(item["failures"]) for item in query_checks),
            "observe_failures": sum(bool(item["failures"]) for item in observe_checks),
            "path_failures": len(path_failures),
            "intervention_failures": sum(
                bool(item["failures"]) for item in intervention_checks
            ),
            "warning_count": len(warnings),
            "failure_count": failure_count,
        },
    }


def _print_human_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"Skill root: {report['skill_root']}")
    print("")
    print("Query checks:")
    for item in report["query_checks"]:
        status = "PASS" if not item["failures"] else "FAIL"
        nodes = ", ".join(item["variable_node_ids"][:5]) or "(none)"
        print(f"  [{status}] {item['query']} ({item['mode']}): {nodes}")
        for failure in item["failures"]:
            print(f"    - {failure}")

    print("")
    print("Observe checks:")
    for item in report["observe_checks"]:
        status = "PASS" if not item["failures"] else "FAIL"
        print(
            "  "
            f"[{status}] {item['asset']}: anchor={item['recommended_primary_anchor']} "
            f"price_ok={item['price_ok']} volume_ok={item['volume_ok']}"
        )
        for failure in item["failures"]:
            print(f"    - {failure}")

    print("")
    print("Intervention checks:")
    if not report["intervention_checks"]:
        print("  (no connected pairs found)")
    for item in report["intervention_checks"]:
        status = "PASS" if not item["failures"] else "FAIL"
        print(
            "  "
            f"[{status}] {item['source']}.price -> {item['target']}.price "
            f"paths={item['path_count']} "
            f"do_ok={item['intervene_do_ok']} "
            f"lag_reachable={item['intervene_time_lag_reachable']} "
            f"lag_support={item['intervene_time_lag_effect_support']}"
        )
        for failure in item["failures"]:
            print(f"    - {failure}")

    if report["path_failures"] or report["warnings"]:
        print("")
    if report["path_failures"]:
        print("Path failures:")
        for failure in report["path_failures"]:
            print(f"  - {failure}")
    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    print("")
    print(
        "Summary: "
        f"{summary['failure_count']} failures, {summary['warning_count']} warnings"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run maintainer smoke checks against the rendered causal-abel cap_probe.py."
    )
    parser.add_argument(
        "--skill-root",
        default=str(DEFAULT_SKILL_ROOT),
        help="Rendered skill root to probe. Defaults to dist/local/causal-abel.",
    )
    parser.add_argument(
        "--asset",
        action="append",
        default=[],
        help="Asset ticker to include in observe/intervention smoke checks. Repeatable.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="top_k sent to query_node probes.",
    )
    parser.add_argument(
        "--max-connected-pairs",
        type=int,
        default=8,
        help="Maximum connected price pairs to carry into intervention checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of the human-readable summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = Path(args.skill_root).expanduser().resolve()
    assets = tuple(args.asset) if args.asset else DEFAULT_ASSETS

    if not skill_root.exists():
        raise SystemExit(f"Skill root not found: {skill_root}")
    if not (skill_root / "scripts" / "cap_probe.py").exists():
        raise SystemExit(f"cap_probe.py not found under: {skill_root / 'scripts'}")

    report = _build_report(
        skill_root,
        assets,
        args.top_k,
        args.max_connected_pairs,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human_report(report)

    return 1 if report["summary"]["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
