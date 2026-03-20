#!/usr/bin/env python
"""Probe Abel CAP server verbs with no third-party dependencies."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://cap.abel.ai"
CAP_VERSION = "0.2.2"
GLOBAL_OPTIONS = {
    "--base-url": True,
    "--api-key": True,
    "--env-file": True,
    "--pick-fields": True,
    "--compact": False,
}
COMMANDS = {
    "capabilities",
    "observe",
    "neighbors",
    "paths",
    "markov-blanket",
    "intervene-do",
    "traverse-parents",
    "traverse-children",
    "validate-connectivity",
    "abel-markov-blanket",
    "counterfactual-preview",
    "intervene-time-lag",
    "verb",
    "route",
}


def _load_env_file(path: str) -> None:
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _resolve_base_url(value: str | None) -> str:
    return (
        value
        or os.getenv("CAP_BASE_URL")
        or os.getenv("ABEL_CAP_BASE_URL")
        or DEFAULT_BASE_URL
    ).strip()


def _cap_endpoint(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid base URL: {base_url!r}")
    path = parsed.path.rstrip("/")
    if path.endswith("/api/v1/cap") or path.endswith("/cap"):
        endpoint_path = path or "/cap"
    elif path in ("", "/", "/api", "/api/v1"):
        endpoint_path = "/cap"
    elif path.endswith("/echo"):
        endpoint_path = f"{path}/api/v1/cap"
    else:
        endpoint_path = f"{path}/cap"
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, endpoint_path, "", "")
    )


def _resolve_headers(api_key: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    token = (
        api_key or os.getenv("CAP_API_KEY") or os.getenv("ABEL_API_KEY") or ""
    ).strip()
    if not token:
        return headers
    if token.lower().startswith("bearer "):
        headers["Authorization"] = token
    else:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _extract_path(obj: Any, path: str) -> tuple[bool, Any]:
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _set_path(obj: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cursor = obj
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    cursor[parts[-1]] = value


def _apply_pick_fields(result: dict[str, Any], pick_fields: str) -> dict[str, Any]:
    fields = [item.strip() for item in pick_fields.split(",") if item.strip()]
    if not fields:
        return result
    out: dict[str, Any] = {}
    for key in ("ok", "status_code", "verb", "request_id"):
        if key in result:
            out[key] = result[key]
    if result.get("ok") is False:
        for key in ("message", "error", "response_payload"):
            if key in result:
                out[key] = result[key]
    for path in fields:
        ok, value = _extract_path(result, path)
        if ok:
            _set_path(out, path, value)
    return out


def _route_to_verb(route: str) -> str:
    normalized = route.strip().strip("/")
    if not normalized:
        raise ValueError("Route alias cannot be empty.")
    if "/" not in normalized:
        return normalized.strip(".")
    return ".".join(segment for segment in normalized.split("/") if segment)


def _build_payload(verb: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "cap_version": CAP_VERSION,
        "request_id": str(uuid.uuid4()),
        "verb": verb,
    }
    if params is not None:
        payload["params"] = params
    return payload


def _json_or_text(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _post_cap(
    base_url: str, verb: str, params: dict[str, Any] | None, headers: dict[str, str]
) -> dict[str, Any]:
    payload = _build_payload(verb, params)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _cap_endpoint(base_url),
        data=data,
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=20.0) as response:
            parsed = _json_or_text(response.read())
            if isinstance(parsed, dict):
                return {"ok": True, "status_code": response.status, **parsed}
            return {"ok": True, "status_code": response.status, "response": parsed}
    except urllib.error.HTTPError as exc:
        parsed = _json_or_text(exc.read())
        message = str(exc)
        error: dict[str, Any] | None = None
        if isinstance(parsed, dict):
            error_payload = parsed.get("error")
            if isinstance(error_payload, dict):
                error = error_payload
                message = error_payload.get("message") or message
            elif isinstance(parsed.get("message"), str):
                message = parsed["message"]
        return {
            "ok": False,
            "status_code": exc.code,
            "message": message,
            "error": error,
            "response_payload": parsed,
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status_code": -1,
            "message": str(exc.reason),
            "error": None,
            "response_payload": {},
        }


def _call_verb(
    args: argparse.Namespace, verb: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    return _post_cap(
        _resolve_base_url(args.base_url),
        verb,
        params,
        _resolve_headers(args.api_key),
    )


def _cmd_capabilities(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(args, "meta.capabilities")


def _cmd_observe(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(args, "observe.predict", {"target_node": args.target_node})


def _cmd_neighbors(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "graph.neighbors",
        {
            "node_id": args.node_id,
            "scope": args.scope,
            "max_neighbors": args.max_neighbors,
        },
    )


def _cmd_paths(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "graph.paths",
        {
            "source_node_id": args.source_node_id,
            "target_node_id": args.target_node_id,
            "max_paths": args.max_paths,
        },
    )


def _cmd_markov_blanket(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "graph.markov_blanket",
        {
            "node_id": args.node_id,
            "max_neighbors": args.max_neighbors,
        },
    )


def _cmd_intervene_do(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "intervene.do",
        {
            "treatment_node": args.treatment_node,
            "treatment_value": args.treatment_value,
            "outcome_node": args.outcome_node,
        },
    )


def _cmd_traverse_parents(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "traverse.parents",
        {
            "node_id": args.node_id,
            "top_k": args.top_k,
        },
    )


def _cmd_traverse_children(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "traverse.children",
        {
            "node_id": args.node_id,
            "top_k": args.top_k,
        },
    )


def _cmd_validate_connectivity(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "extensions.abel.validate_connectivity",
        {"variables": args.variables},
    )


def _cmd_abel_markov_blanket(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "extensions.abel.markov_blanket",
        {"target_node": args.target_node},
    )


def _cmd_counterfactual_preview(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "extensions.abel.counterfactual_preview",
        {
            "intervene_node": args.intervene_node,
            "intervene_time": args.intervene_time,
            "observe_node": args.observe_node,
            "observe_time": args.observe_time,
            "intervene_new_value": args.intervene_new_value,
        },
    )


def _cmd_intervene_time_lag(args: argparse.Namespace) -> dict[str, Any]:
    return _call_verb(
        args,
        "extensions.abel.intervene_time_lag",
        {
            "treatment_node": args.treatment_node,
            "treatment_value": args.treatment_value,
            "outcome_node": args.outcome_node,
            "horizon_steps": args.horizon_steps,
            "model": args.model,
        },
    )


def _cmd_verb(args: argparse.Namespace) -> dict[str, Any]:
    params = json.loads(args.params_json) if args.params_json else None
    if params is not None and not isinstance(params, dict):
        raise ValueError("--params-json must decode to a JSON object.")
    return _call_verb(args, args.verb_name, params)


def _cmd_route(args: argparse.Namespace) -> dict[str, Any]:
    params = json.loads(args.params_json) if args.params_json else None
    if params is not None and not isinstance(params, dict):
        raise ValueError("--params-json must decode to a JSON object.")
    return _call_verb(args, _route_to_verb(args.route_name), params)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe Abel CAP server verbs as atomic operations."
    )
    default_env = str(Path(__file__).resolve().parents[1] / ".env.skills")
    parser.add_argument(
        "--base-url",
        default="",
        help=f"CAP server base URL (default: {DEFAULT_BASE_URL}).",
    )
    parser.add_argument("--api-key", default="", help="Bearer token or raw API key.")
    parser.add_argument(
        "--env-file",
        default=default_env,
        help=f"Optional env file path (default: {default_env})",
    )
    parser.add_argument(
        "--pick-fields",
        default="",
        help="Comma-separated dot paths to keep from response root.",
    )
    parser.add_argument(
        "--compact", action="store_true", help="Print compact single-line JSON."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("capabilities", help="Call meta.capabilities.").set_defaults(
        func=_cmd_capabilities
    )

    observe = sub.add_parser("observe", help="Call observe.predict.")
    observe.add_argument("target_node")
    observe.set_defaults(func=_cmd_observe)

    neighbors = sub.add_parser("neighbors", help="Call graph.neighbors.")
    neighbors.add_argument("node_id")
    neighbors.add_argument(
        "--scope", choices=("parents", "children"), default="parents"
    )
    neighbors.add_argument("--max-neighbors", type=int, default=5)
    neighbors.set_defaults(func=_cmd_neighbors)

    paths = sub.add_parser("paths", help="Call graph.paths.")
    paths.add_argument("source_node_id")
    paths.add_argument("target_node_id")
    paths.add_argument("--max-paths", type=int, default=3)
    paths.set_defaults(func=_cmd_paths)

    blanket = sub.add_parser("markov-blanket", help="Call graph.markov_blanket.")
    blanket.add_argument("node_id")
    blanket.add_argument("--max-neighbors", type=int, default=10)
    blanket.set_defaults(func=_cmd_markov_blanket)

    intervene_do = sub.add_parser("intervene-do", help="Call intervene.do.")
    intervene_do.add_argument("treatment_node")
    intervene_do.add_argument("treatment_value", type=float)
    intervene_do.add_argument("--outcome-node", required=True)
    intervene_do.set_defaults(func=_cmd_intervene_do)

    traverse_parents = sub.add_parser("traverse-parents", help="Call traverse.parents.")
    traverse_parents.add_argument("node_id")
    traverse_parents.add_argument("--top-k", type=int, default=10)
    traverse_parents.set_defaults(func=_cmd_traverse_parents)

    traverse_children = sub.add_parser(
        "traverse-children", help="Call traverse.children."
    )
    traverse_children.add_argument("node_id")
    traverse_children.add_argument("--top-k", type=int, default=10)
    traverse_children.set_defaults(func=_cmd_traverse_children)

    validate = sub.add_parser(
        "validate-connectivity", help="Call extensions.abel.validate_connectivity."
    )
    validate.add_argument(
        "variables", nargs="+", help="At least two variable node IDs."
    )
    validate.set_defaults(func=_cmd_validate_connectivity)

    abel_blanket = sub.add_parser(
        "abel-markov-blanket", help="Call extensions.abel.markov_blanket."
    )
    abel_blanket.add_argument("target_node")
    abel_blanket.set_defaults(func=_cmd_abel_markov_blanket)

    cf_preview = sub.add_parser(
        "counterfactual-preview", help="Call extensions.abel.counterfactual_preview."
    )
    cf_preview.add_argument("--intervene-node", required=True)
    cf_preview.add_argument("--intervene-time", required=True)
    cf_preview.add_argument("--observe-node", required=True)
    cf_preview.add_argument("--observe-time", required=True)
    cf_preview.add_argument("--intervene-new-value", required=True, type=float)
    cf_preview.set_defaults(func=_cmd_counterfactual_preview)

    time_lag = sub.add_parser(
        "intervene-time-lag", help="Call extensions.abel.intervene_time_lag."
    )
    time_lag.add_argument("treatment_node")
    time_lag.add_argument("treatment_value", type=float)
    time_lag.add_argument("--outcome-node", required=True)
    time_lag.add_argument("--horizon-steps", type=int, default=24)
    time_lag.add_argument("--model", default="linear")
    time_lag.set_defaults(func=_cmd_intervene_time_lag)

    generic_verb = sub.add_parser(
        "verb", help="Call an arbitrary CAP verb with optional JSON params."
    )
    generic_verb.add_argument("verb_name")
    generic_verb.add_argument(
        "--params-json", default="", help="JSON object passed as params."
    )
    generic_verb.set_defaults(func=_cmd_verb)

    generic_route = sub.add_parser(
        "route", help="Call an arbitrary Abel route alias with optional JSON params."
    )
    generic_route.add_argument("route_name")
    generic_route.add_argument(
        "--params-json", default="", help="JSON object passed as params."
    )
    generic_route.set_defaults(func=_cmd_route)

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv

    prefix: list[str] = []
    suffix: list[str] = []
    command_seen = False
    i = 0
    while i < len(argv):
        token = argv[i]
        if not command_seen and token in COMMANDS:
            command_seen = True
            suffix.append(token)
            i += 1
            continue

        if command_seen and token in GLOBAL_OPTIONS:
            prefix.append(token)
            if GLOBAL_OPTIONS[token]:
                if i + 1 >= len(argv):
                    raise ValueError(f"Missing value for {token}")
                prefix.append(argv[i + 1])
                i += 2
            else:
                i += 1
            continue

        if command_seen:
            suffix.append(token)
        else:
            prefix.append(token)
        i += 1

    return prefix + suffix


def main() -> int:
    parser = _build_parser()
    raw_argv = sys.argv[1:]
    try:
        argv = _normalize_argv(raw_argv)
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "status_code": -1,
                    "message": str(exc),
                    "error": None,
                    "response_payload": {},
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    args = parser.parse_args(argv)
    _load_env_file(args.env_file)

    try:
        result = args.func(args)
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "status_code": -1,
            "message": str(exc),
            "error": None,
            "response_payload": {},
        }

    result = _apply_pick_fields(result, args.pick_fields)

    if args.compact:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("ok") is False:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
