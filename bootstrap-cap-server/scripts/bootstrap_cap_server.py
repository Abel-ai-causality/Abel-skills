#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


PLACEHOLDERS = {
    "project_name": "__PROJECT_NAME__",
    "package_name": "__PACKAGE_NAME__",
    "server_title": "__SERVER_TITLE__",
    "graph_id": "__GRAPH_ID__",
    "graph_version": "__GRAPH_VERSION__",
    "conformance_level": "__CONFORMANCE_LEVEL__",
    "description": "__DESCRIPTION__",
    "auth_type": "__AUTH_TYPE__",
    "auth_details_expr": "__AUTH_DETAILS_EXPR__",
    "api_key_header": "__API_KEY_HEADER__",
    "runtime_algorithm": "__RUNTIME_ALGORITHM__",
    "mechanism_family": "__MECHANISM_FAMILY__",
    "structural_mechanisms_available": "__STRUCTURAL_MECHANISMS_AVAILABLE__",
    "structural_mechanism_families_expr": "__STRUCTURAL_MECHANISM_FAMILIES_EXPR__",
    "effect_estimation": "__EFFECT_ESTIMATION__",
    "intervention_simulation": "__INTERVENTION_SIMULATION__",
    "assumptions_expr": "__ASSUMPTIONS_EXPR__",
    "reasoning_modes_supported_expr": "__REASONING_MODES_SUPPORTED_EXPR__",
    "disclosure_notes_expr": "__DISCLOSURE_NOTES_EXPR__",
    "auth_notes": "__AUTH_NOTES__",
    "auth_helper": "__AUTH_HELPER__",
    "auth_enforce_call": "__AUTH_ENFORCE_CALL__",
    "graph_ref_notes": "__GRAPH_REF_NOTES__",
    "graph_ref_mode": "__GRAPH_REF_MODE__",
    "graph_ref_helper": "__GRAPH_REF_HELPER__",
    "graph_ref_call": "__GRAPH_REF_CALL__",
    "predictor_notes": "__PREDICTOR_NOTES__",
    "intervention_notes": "__INTERVENTION_NOTES__",
    "test_cap_headers": "__TEST_CAP_HEADERS__",
    "test_graph_context": "__TEST_GRAPH_CONTEXT__",
    "test_expect_observe_predict": "__TEST_EXPECT_OBSERVE_PREDICT__",
    "test_expect_intervene_do": "__TEST_EXPECT_INTERVENE_DO__",
}

BLOCK_START = "[[IF_"
BLOCK_END = "[[END_IF_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a configurable CAP server scaffold from the bundled templates."
    )
    parser.add_argument("project_name", help="Output project folder name.")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Parent directory that will contain the generated project folder.",
    )
    parser.add_argument(
        "--level",
        choices={"1", "2"},
        default="1",
        help="CAP scaffold level to generate.",
    )
    parser.add_argument(
        "--package-name",
        help="Python package name. Defaults to a sanitized form of project_name.",
    )
    parser.add_argument(
        "--server-title",
        help="Human-readable server title. Defaults to title-cased project_name.",
    )
    parser.add_argument(
        "--auth",
        choices={"none", "api-key"},
        default="none",
        help="Authentication mode exposed in the capability card and scaffold.",
    )
    parser.add_argument(
        "--api-key-header",
        default="x-api-key",
        help="Header name used when --auth api-key is selected.",
    )
    parser.add_argument(
        "--graph-ref-mode",
        choices={"none", "optional", "required"},
        default="none",
        help="How the scaffold should treat context.graph_ref.",
    )
    parser.add_argument(
        "--graph-id",
        default="primary",
        help="Supported graph_id when graph_ref validation is enabled.",
    )
    parser.add_argument(
        "--graph-version",
        default="demo-v1",
        help="Supported graph_version when graph_ref validation is enabled.",
    )
    parser.add_argument(
        "--with-paths",
        action="store_true",
        help="Mount graph.paths in the Level 1 scaffold. Ignored for Level 2, where graph.paths is always included.",
    )
    parser.add_argument(
        "--runtime-algorithm",
        default="replace_me",
        help="Initial algorithm string used in provenance and capability metadata.",
    )
    parser.add_argument(
        "--predictor-mode",
        choices={"none", "mounted", "stub"},
        help="How observe.predict should be represented in the generated scaffold. Defaults to mounted.",
    )
    parser.add_argument(
        "--mechanism-family",
        default="replace_me",
        help="Initial mechanism family string used in the Level 2 scaffold.",
    )
    parser.add_argument(
        "--intervention-mode",
        choices={"none", "mounted", "stub"},
        help="How intervene.do should be represented in the generated scaffold. Defaults to mounted for Level 2 and none for Level 1.",
    )
    parser.add_argument(
        "--git-init",
        action="store_true",
        help="Run git init inside the generated project directory after scaffold generation.",
    )
    return parser.parse_args()


def sanitize_package_name(raw: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_").lower()
    if not normalized:
        raise SystemExit("Package name cannot be empty after sanitization.")
    if normalized[0].isdigit():
        normalized = f"cap_{normalized}"
    return normalized


def derive_server_title(project_name: str) -> str:
    words = re.split(r"[-_]+", project_name.strip())
    words = [word for word in words if word]
    if not words:
        raise SystemExit("project_name must contain at least one alphanumeric token.")
    return " ".join(word.capitalize() for word in words)


def resolve_template_root(skill_root: Path, level: str) -> Path:
    template_name = "level1-fastapi" if level == "1" else "level2-fastapi"
    template_root = skill_root / "assets" / "templates" / template_name
    if not template_root.is_dir():
        raise SystemExit(f"Template directory not found: {template_root}")
    return template_root


def build_auth_details_expr(auth: str, api_key_header: str) -> str:
    if auth == "api-key":
        return f'{{"header_name": "{api_key_header}"}}'
    return "{}"


def build_auth_notes(auth: str, api_key_header: str) -> str:
    if auth == "api-key":
        return f"- CAP requests require the `{api_key_header}` header.\n- Update the placeholder key check before production use."
    return "- The scaffold exposes public unauthenticated CAP routes by default."


def build_auth_helper(auth: str, api_key_header: str) -> str:
    if auth != "api-key":
        return ""
    return f'''def require_api_key(request: Request) -> None:
    provided = request.headers.get("{api_key_header}")
    if not provided:
        raise CAPAdapterError(
            "unauthorized",
            "Missing API key.",
            status_code=401,
            details={{"header_name": "{api_key_header}"}},
        )
'''


def build_auth_enforce_call(auth: str) -> str:
    if auth != "api-key":
        return ""
    return "        require_api_key(request)\n"


def build_graph_ref_notes(mode: str, graph_id: str, graph_version: str) -> str:
    if mode == "none":
        return "- The scaffold ignores `context.graph_ref` until multi-graph selection is needed."
    if mode == "optional":
        return (
            f"- The scaffold accepts an optional `context.graph_ref` and validates it against `{graph_id}` / `{graph_version}`.\n"
            "- Remove or widen this validation if the runtime later supports multiple graphs."
        )
    return (
        f"- The scaffold requires `context.graph_ref` on graph and causal verb requests.\n"
        f"- The generated validator currently accepts only `{graph_id}` / `{graph_version}`."
    )


def build_graph_ref_helper(mode: str) -> str:
    if mode == "none":
        return '''def validate_graph_ref(payload) -> None:
    del payload
    return
'''
    required = "True" if mode == "required" else "False"
    return f'''def validate_graph_ref(payload) -> None:
    graph_ref = None if payload.context is None else payload.context.graph_ref
    if graph_ref is None:
        if {required}:
            raise CAPAdapterError(
                "invalid_request",
                "context.graph_ref is required for this CAP server.",
                status_code=400,
                details={{"supported_graph_id": GRAPH_ID, "supported_graph_version": GRAPH_VERSION}},
            )
        return

    if graph_ref.graph_id is not None and graph_ref.graph_id != GRAPH_ID:
        raise CAPAdapterError(
            "invalid_request",
            f"graph_id={{graph_ref.graph_id!r}} is not supported by this CAP server.",
            status_code=400,
            details={{"supported_graph_id": GRAPH_ID}},
        )

    if graph_ref.graph_version is not None and graph_ref.graph_version != GRAPH_VERSION:
        raise CAPAdapterError(
            "invalid_request",
            f"graph_version={{graph_ref.graph_version!r}} is not supported by this CAP server.",
            status_code=400,
            details={{"supported_graph_version": GRAPH_VERSION}},
        )
'''


def build_graph_ref_call(mode: str) -> str:
    if mode == "none":
        return ""
    return "    validate_graph_ref(payload)\n"


def build_test_cap_headers(auth: str, api_key_header: str) -> str:
    if auth == "api-key":
        return f'{{"{api_key_header}": "dev-api-key"}}'
    return "{}"


def build_test_graph_context(mode: str, graph_id: str, graph_version: str) -> str:
    if mode == "none":
        return "None"
    return f'{{"graph_id": "{graph_id}", "graph_version": "{graph_version}"}}'


def resolve_modes(args: argparse.Namespace) -> tuple[str, str, str]:
    predictor_mode = args.predictor_mode or "mounted"
    intervention_mode = args.intervention_mode or ("mounted" if args.level == "2" else "none")

    if args.level == "1" and intervention_mode != "none":
        raise SystemExit("Use --level 2 when generating intervene.do support or intervention adapter stubs.")
    if intervention_mode == "mounted" and predictor_mode != "mounted":
        raise SystemExit(
            "Mounted intervene.do scaffolds require --predictor-mode mounted so the generated surface stays internally consistent."
        )

    conformance_level = "2" if intervention_mode == "mounted" else "1"
    return predictor_mode, intervention_mode, conformance_level


def build_description(conformance_level: str) -> str:
    if conformance_level == "2":
        return "CAP Level 2 scaffold over a user-replaceable runtime adapter."
    return "CAP scaffold over a user-replaceable runtime adapter."


def build_structural_mechanisms_available(intervention_mode: str) -> str:
    return "True" if intervention_mode == "mounted" else "False"


def build_structural_mechanism_families_expr(intervention_mode: str, mechanism_family: str) -> str:
    if intervention_mode == "mounted":
        return repr([mechanism_family])
    return "[]"


def build_effect_estimation(intervention_mode: str) -> str:
    return "True" if intervention_mode == "mounted" else "False"


def build_intervention_simulation(intervention_mode: str) -> str:
    return "True" if intervention_mode == "mounted" else "False"


def build_assumptions_expr(intervention_mode: str) -> str:
    if intervention_mode == "mounted":
        return "[ASSUMPTION_ACYCLICITY, ASSUMPTION_LINEARITY, ASSUMPTION_MECHANISM_INVARIANCE_UNDER_INTERVENTION]"
    return "[ASSUMPTION_ACYCLICITY]"


def build_reasoning_modes_supported_expr(predictor_mode: str, intervention_mode: str) -> str:
    modes = []
    if predictor_mode == "mounted":
        modes.append("REASONING_MODE_OBSERVATIONAL_PREDICTION")
    if intervention_mode == "mounted":
        modes.append("REASONING_MODE_SCM_SIMULATION")
    modes.append("REASONING_MODE_STRUCTURAL_SEMANTICS")
    return "[" + ", ".join(modes) + "]"


def build_disclosure_notes_expr(predictor_mode: str, intervention_mode: str) -> str:
    notes = ["Replace disclosure notes to match the real runtime and access policy."]
    if predictor_mode == "stub":
        notes.append("observe.predict is scaffolded as an adapter TODO and is not mounted yet.")
    elif predictor_mode == "none":
        notes.append("observe.predict is not mounted in this scaffold.")
    if intervention_mode == "stub":
        notes.append("intervene.do is scaffolded as an adapter TODO and is not mounted yet.")
    elif intervention_mode == "none":
        notes.append("intervene.do is not mounted in this scaffold.")
    return repr(notes)


def build_predictor_notes(predictor_mode: str) -> str:
    if predictor_mode == "mounted":
        return "- The scaffold mounts `observe.predict` against the example runtime. Replace it with your own observational predictor."
    if predictor_mode == "stub":
        return "- The scaffold does not mount `observe.predict` yet, but includes a `predict` adapter stub for a future model."
    return "- The scaffold does not mount `observe.predict`."


def build_intervention_notes(intervention_mode: str) -> str:
    if intervention_mode == "mounted":
        return "- The scaffold mounts `intervene.do` against the example runtime. Replace it with your own intervention backend."
    if intervention_mode == "stub":
        return "- The scaffold does not mount `intervene.do` yet, but includes an `intervene` adapter stub for a future SCM, simulator, or service."
    return "- The scaffold does not mount `intervene.do`."


def build_placeholder_values(
    args: argparse.Namespace,
    *,
    predictor_mode: str,
    intervention_mode: str,
    conformance_level: str,
) -> dict[str, str]:
    package_name = sanitize_package_name(args.package_name or args.project_name)
    server_title = args.server_title or derive_server_title(args.project_name)
    return {
        "project_name": args.project_name,
        "package_name": package_name,
        "server_title": server_title,
        "graph_id": args.graph_id,
        "graph_version": args.graph_version,
        "conformance_level": conformance_level,
        "description": build_description(conformance_level),
        "auth_type": "api_key" if args.auth == "api-key" else "none",
        "auth_details_expr": build_auth_details_expr(args.auth, args.api_key_header),
        "api_key_header": args.api_key_header,
        "runtime_algorithm": args.runtime_algorithm,
        "mechanism_family": args.mechanism_family,
        "structural_mechanisms_available": build_structural_mechanisms_available(intervention_mode),
        "structural_mechanism_families_expr": build_structural_mechanism_families_expr(
            intervention_mode, args.mechanism_family
        ),
        "effect_estimation": build_effect_estimation(intervention_mode),
        "intervention_simulation": build_intervention_simulation(intervention_mode),
        "assumptions_expr": build_assumptions_expr(intervention_mode),
        "reasoning_modes_supported_expr": build_reasoning_modes_supported_expr(
            predictor_mode, intervention_mode
        ),
        "disclosure_notes_expr": build_disclosure_notes_expr(predictor_mode, intervention_mode),
        "auth_notes": build_auth_notes(args.auth, args.api_key_header),
        "auth_helper": build_auth_helper(args.auth, args.api_key_header),
        "auth_enforce_call": build_auth_enforce_call(args.auth),
        "graph_ref_notes": build_graph_ref_notes(args.graph_ref_mode, args.graph_id, args.graph_version),
        "graph_ref_mode": args.graph_ref_mode,
        "graph_ref_helper": build_graph_ref_helper(args.graph_ref_mode),
        "graph_ref_call": build_graph_ref_call(args.graph_ref_mode),
        "predictor_notes": build_predictor_notes(predictor_mode),
        "intervention_notes": build_intervention_notes(intervention_mode),
        "test_cap_headers": build_test_cap_headers(args.auth, args.api_key_header),
        "test_graph_context": build_test_graph_context(args.graph_ref_mode, args.graph_id, args.graph_version),
        "test_expect_observe_predict": "True" if predictor_mode == "mounted" else "False",
        "test_expect_intervene_do": "True" if intervention_mode == "mounted" else "False",
    }


def render_text(value: str, *, replacements: dict[str, str], conditions: dict[str, bool]) -> str:
    rendered = value
    for key, token in PLACEHOLDERS.items():
        rendered = rendered.replace(token, replacements[key])
    return render_conditional_blocks(rendered, conditions=conditions)


def render_conditional_blocks(value: str, *, conditions: dict[str, bool]) -> str:
    lines = value.splitlines(keepends=True)
    rendered: list[str] = []
    stack: list[tuple[str, bool]] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(BLOCK_END) and stripped.endswith("]]"):
            condition_name = stripped[len(BLOCK_END) : -2]
            if not stack:
                raise SystemExit(f"Unbalanced {condition_name} markers in template.")
            open_name, _ = stack.pop()
            if open_name != condition_name:
                raise SystemExit(
                    f"Mismatched conditional markers in template: opened {open_name}, closed {condition_name}."
                )
            continue
        if stripped.startswith(BLOCK_START) and stripped.endswith("]]"):
            condition_name = stripped[len(BLOCK_START) : -2]
            if condition_name not in conditions:
                raise SystemExit(f"Unknown template condition: {condition_name}")
            stack.append((condition_name, conditions[condition_name]))
            continue
        if not stack or all(value for _, value in stack):
            rendered.append(line)

    if stack:
        names = ", ".join(name for name, _ in stack)
        raise SystemExit(f"Unclosed conditional markers in template: {names}")

    return "".join(rendered)


def render_tree(
    *,
    template_root: Path,
    destination_root: Path,
    replacements: dict[str, str],
    conditions: dict[str, bool],
) -> None:
    if destination_root.exists():
        raise SystemExit(f"Destination already exists: {destination_root}")

    for source_path in sorted(template_root.rglob("*")):
        relative = source_path.relative_to(template_root)
        rendered_relative = Path(
            render_text(relative.as_posix(), replacements=replacements, conditions=conditions)
        )
        target_path = destination_root / rendered_relative

        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        text = source_path.read_text(encoding="utf-8")
        target_path.write_text(
            render_text(text, replacements=replacements, conditions=conditions),
            encoding="utf-8",
        )


def shlex_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def maybe_git_init(destination_root: Path, enabled: bool) -> bool:
    if not enabled:
        return False
    subprocess.run(["git", "init"], cwd=destination_root, check=True)
    return True


def main() -> None:
    args = parse_args()
    skill_root = Path(__file__).resolve().parent.parent
    project_name = args.project_name.strip()
    if not project_name:
        raise SystemExit("project_name must not be empty.")

    output_dir = Path(args.output_dir).expanduser().resolve()
    destination_root = output_dir / project_name
    template_root = resolve_template_root(skill_root, args.level)
    predictor_mode, intervention_mode, conformance_level = resolve_modes(args)
    include_paths = args.level == "2" or args.with_paths
    conditions = {
        "INCLUDE_PATHS": include_paths,
        "INCLUDE_PREDICTOR": predictor_mode == "mounted",
        "INCLUDE_PREDICTOR_STUB": predictor_mode == "stub",
        "INCLUDE_INTERVENTION": intervention_mode == "mounted",
        "INCLUDE_INTERVENTION_STUB": intervention_mode == "stub",
    }
    replacements = build_placeholder_values(
        args,
        predictor_mode=predictor_mode,
        intervention_mode=intervention_mode,
        conformance_level=conformance_level,
    )

    render_tree(
        template_root=template_root,
        destination_root=destination_root,
        replacements=replacements,
        conditions=conditions,
    )
    git_initialized = maybe_git_init(destination_root, args.git_init)

    package_name = replacements["package_name"]
    print(f"[OK] Generated CAP scaffold at {destination_root}")
    print("Options:")
    print(f"- requested_level={args.level}")
    print(f"- conformance_level={conformance_level}")
    print(f"- auth={args.auth}")
    print(f"- graph_ref_mode={args.graph_ref_mode}")
    print(f"- include_paths={include_paths}")
    print(f"- predictor_mode={predictor_mode}")
    print(f"- intervention_mode={intervention_mode}")
    print(f"- git_init={git_initialized}")
    print("Next steps:")
    print(f"1. cd {shlex_quote(str(destination_root))}")
    print("2. Inspect the generated scaffold and adapt the runtime adapter to your graph.")
    print('3. pip install -e ".[dev]"')
    print("4. uv run pytest")
    print(f"5. uv run uvicorn {package_name}.app:app --reload")


if __name__ == "__main__":
    main()
