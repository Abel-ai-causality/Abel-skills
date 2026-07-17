from __future__ import annotations

from argparse import Namespace
import json
from hashlib import sha256
from pathlib import Path
from urllib.error import URLError

import pytest

from abel_invest.narrative_core.dashboard_payload import build_skill_dashboard_session_bundle
from abel_invest.narrative_core.rendering.session_rendering import render_session
from abel_invest.narrative_core.command_handlers import session as session_handler
from abel_invest.narrative_core import sample_strategy_context as sample_context
from abel_invest.narrative_core.sample_strategy_context import (
    SAMPLE_STRATEGY_CONTEXT_FILENAME,
    SAMPLE_STRATEGY_DIRNAME,
    SAMPLE_STRATEGY_LOOKUP_FILENAME,
    SAMPLE_STRATEGY_SAMPLES_DIRNAME,
    ensure_sample_strategy_context,
    load_available_sample_strategies,
)
from abel_invest.narrative_core.session_lifecycle import init_session_dir


class _Response:
    def __init__(self, payload: object, *, raw: bytes | None = None):
        self._raw = raw if raw is not None else json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None


def _source(path: str, content: str) -> dict:
    return {
        "path": path,
        "content": content,
        "sha256": sha256(content.encode("utf-8")).hexdigest(),
    }


def _sample_item(
    *source_files: dict,
    strategy_id: str = "101",
    source_branch_id: str = "trail-filter",
) -> dict:
    return {
        "strategyId": strategy_id,
        "displayName": f"Historical CVX strategy {strategy_id}",
        "ticker": "CVX",
        "seedContext": {
            "schema": "abel-invest.official-seed-context/v1",
            "handoff_context": {
                "source_branch": {"source_branch_id": source_branch_id},
                "source_round": {
                    "source_round_id": "round-001",
                    "hypothesis": "Graph peers improve the CVX signal",
                },
            },
        },
        "sourceFiles": list(source_files),
    }


def _available_payload(*source_files: dict) -> dict:
    return {
        "items": [_sample_item(*source_files)],
    }


def _session(tmp_path: Path) -> Path:
    session = tmp_path / "research" / "cvx" / "cvx-sample"
    session.mkdir(parents=True)
    return session


def test_available_sample_preserves_context_and_complete_source_tree(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    payload = _available_payload(
        _source("strategy/strategy.py", "from .helper import signal\n"),
        _source("strategy/helper.py", "signal = 1\n"),
        _source("strategy/config/rules.json", '{"window": 20}\n'),
    )
    calls = []

    def opener(request, *, timeout):
        calls.append((request, timeout))
        return _Response({"code": 200, "data": payload, "message": "success"})

    monkeypatch.setenv("ABEL_API_KEY", "test-key")
    monkeypatch.setenv("ABEL_ROUTER_BASE_URL", "https://router.example/base/")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="cvx",
        opener=opener,
        timeout=7,
    )

    assert receipt["status"] == "available"
    assert len(calls) == 1
    request, timeout = calls[0]
    assert request.full_url == (
        "https://router.example/base/api/v1/official-strategy-pool/"
        "sample-strategies?ticker=CVX"
    )
    assert request.get_header("Api-key") == "test-key"
    assert timeout == 7
    sample_dir = session / SAMPLE_STRATEGY_DIRNAME
    first_sample_dir = sample_dir / SAMPLE_STRATEGY_SAMPLES_DIRNAME / "001"
    persisted_receipt = json.loads(
        (sample_dir / SAMPLE_STRATEGY_LOOKUP_FILENAME).read_text(encoding="utf-8")
    )
    assert persisted_receipt["status"] == "available"
    assert persisted_receipt["sample_count"] == 1
    assert (
        json.loads(
            (first_sample_dir / SAMPLE_STRATEGY_CONTEXT_FILENAME).read_text(
                encoding="utf-8"
            )
        )["handoff_context"]["source_round"]["source_round_id"]
        == "round-001"
    )
    assert (first_sample_dir / "strategy/helper.py").read_text(
        encoding="utf-8"
    ) == "signal = 1\n"
    assert (first_sample_dir / "strategy/config/rules.json").is_file()
    assert not list(session.glob(".sample-strategy-*"))

    loaded = load_available_sample_strategies(session)
    assert len(loaded) == 1
    assert loaded[0]["source_dir"] == first_sample_dir / "strategy"


def test_multiple_samples_are_materialized_in_router_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    payload = {
        "items": [
            _sample_item(
                _source("strategy/strategy.py", "FIRST = 1\n"),
                _source("strategy/helper.py", "RANK = 1\n"),
                strategy_id="101",
                source_branch_id="first-branch",
            ),
            _sample_item(
                _source("strategy/strategy.py", "SECOND = 2\n"),
                _source("strategy/helper.py", "RANK = 2\n"),
                strategy_id="202",
                source_branch_id="second-branch",
            ),
        ]
    }
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(payload),
    )

    samples_dir = session / "sample_strategy/samples"
    assert receipt["status"] == "available"
    assert receipt["sample_count"] == 2
    assert (samples_dir / "001/strategy/strategy.py").read_text(
        encoding="utf-8"
    ) == "FIRST = 1\n"
    assert (samples_dir / "002/strategy/helper.py").read_text(
        encoding="utf-8"
    ) == "RANK = 2\n"
    assert [
        sample["context_path"].relative_to(session).as_posix()
        for sample in load_available_sample_strategies(session)
    ] == [
        "sample_strategy/samples/001/seed_context.json",
        "sample_strategy/samples/002/seed_context.json",
    ]


def test_client_omits_router_usage_note_and_preserves_other_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    payload = _available_payload(
        _source("strategy/strategy.py", "pass\n"),
    )
    seed_context = payload["items"][0]["seedContext"]
    seed_context["usage_note"] = "Copy this strategy into a new branch."
    seed_context["future_metadata"] = {"new_field": True}
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(payload),
    )

    persisted = json.loads(
        (
            session
            / "sample_strategy/samples/001"
            / SAMPLE_STRATEGY_CONTEXT_FILENAME
        ).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "available"
    assert "usage_note" not in persisted
    assert persisted["future_metadata"] == {"new_field": True}
    assert persisted["handoff_context"] == seed_context["handoff_context"]


def test_invalid_later_sample_never_publishes_a_partial_available_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    invalid_source = _source("strategy/strategy.py", "SECOND = 2\n")
    invalid_source["sha256"] = "0" * 64
    payload = {
        "items": [
            _sample_item(_source("strategy/strategy.py", "FIRST = 1\n")),
            _sample_item(invalid_source, strategy_id="202"),
        ]
    }
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(payload),
    )

    assert receipt["status"] == "unavailable"
    assert receipt["sample_count"] == 0
    assert not (session / "sample_strategy/samples").exists()


def test_empty_result_is_terminal_not_found_and_does_not_refetch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    calls = 0

    def opener(_request, *, timeout):
        nonlocal calls
        calls += 1
        return _Response({"items": []})

    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    first = ensure_sample_strategy_context(session=session, ticker="CVX", opener=opener)
    second = ensure_sample_strategy_context(
        session=session, ticker="CVX", opener=opener
    )

    assert first["status"] == "not_found"
    assert second == first
    assert calls == 1
    assert first["sample_count"] == 0
    assert load_available_sample_strategies(session) == []
    assert sorted(
        path.name for path in (session / SAMPLE_STRATEGY_DIRNAME).iterdir()
    ) == [SAMPLE_STRATEGY_LOOKUP_FILENAME]


def test_missing_auth_and_request_failure_are_fail_open(
    tmp_path: Path,
    monkeypatch,
) -> None:
    missing_auth_session = _session(tmp_path)
    monkeypatch.delenv("ABEL_API_KEY", raising=False)
    monkeypatch.delenv("CAP_API_KEY", raising=False)
    monkeypatch.delenv("ABEL_AUTH_ENV_FILE", raising=False)

    missing_auth = ensure_sample_strategy_context(
        session=missing_auth_session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: pytest.fail("network should not be called"),
    )

    assert missing_auth["status"] == "unavailable"
    assert missing_auth["reason_code"] == "auth_missing"

    failed_session = tmp_path / "research" / "cvx" / "cvx-request-failed"
    failed_session.mkdir(parents=True)
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    def failed_opener(*_args, **_kwargs):
        raise URLError("offline")

    failed = ensure_sample_strategy_context(
        session=failed_session,
        ticker="CVX",
        opener=failed_opener,
    )

    assert failed["status"] == "unavailable"
    assert failed["reason_code"] == "request_failed"
    assert load_available_sample_strategies(failed_session) == []


def test_shared_auth_file_supplies_api_key_without_copying_it_to_process_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    auth_file = tmp_path / "shared-auth.env"
    auth_file.write_text("ABEL_API_KEY=shared-test-key\n", encoding="utf-8")
    observed_key = ""
    monkeypatch.delenv("ABEL_API_KEY", raising=False)
    monkeypatch.delenv("CAP_API_KEY", raising=False)
    monkeypatch.delenv("ABEL_AUTH_ENV_FILE", raising=False)
    monkeypatch.setenv("ABEL_AUTH_ENV_FILE", str(auth_file))

    def opener(request, *, timeout):
        nonlocal observed_key
        observed_key = request.get_header("Api-key")
        return _Response({"items": []})

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=opener,
    )

    assert receipt["status"] == "not_found"
    assert observed_key == "shared-test-key"


def test_unreadable_shared_auth_path_is_fail_open(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    monkeypatch.delenv("ABEL_API_KEY", raising=False)
    monkeypatch.delenv("CAP_API_KEY", raising=False)
    monkeypatch.setenv("ABEL_AUTH_ENV_FILE", str(tmp_path))

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: pytest.fail("network should not be called"),
    )

    assert receipt["status"] == "unavailable"
    assert receipt["reason_code"] == "auth_missing"


@pytest.mark.parametrize(
    ("opener", "reason_code"),
    [
        (lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()), "timeout"),
        (lambda *_args, **_kwargs: _Response({}, raw=b"{"), "invalid_json"),
    ],
)
def test_transport_and_decode_failures_are_unavailable(
    tmp_path: Path,
    monkeypatch,
    opener,
    reason_code: str,
) -> None:
    session = _session(tmp_path)
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=opener,
    )

    assert receipt["status"] == "unavailable"
    assert receipt["reason_code"] == reason_code


@pytest.mark.parametrize(
    "source_files",
    [
        [_source("../strategy.py", "pass\n")],
        [_source("/tmp/strategy.py", "pass\n")],
        [_source("lookup.json", "{}\n")],
        [_source("seed_context.json", "{}\n")],
        [
            _source("strategy/helper.py", "first\n"),
            _source("strategy/helper.py", "second\n"),
        ],
    ],
)
def test_unsafe_duplicate_or_reserved_source_paths_are_unavailable(
    tmp_path: Path,
    monkeypatch,
    source_files: list[dict],
) -> None:
    session = _session(tmp_path)
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(_available_payload(*source_files)),
    )

    assert receipt["status"] == "unavailable"
    assert receipt["reason_code"] == "invalid_package"
    assert sorted(
        path.name for path in (session / SAMPLE_STRATEGY_DIRNAME).iterdir()
    ) == [SAMPLE_STRATEGY_LOOKUP_FILENAME]


def test_hash_mismatch_never_publishes_available_receipt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    source = _source("strategy/strategy.py", "pass\n")
    source["sha256"] = "0" * 64
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(_available_payload(source)),
    )

    persisted = json.loads(
        (session / SAMPLE_STRATEGY_DIRNAME / SAMPLE_STRATEGY_LOOKUP_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "unavailable"
    assert persisted["status"] == "unavailable"
    assert not (
        session / SAMPLE_STRATEGY_DIRNAME / SAMPLE_STRATEGY_SAMPLES_DIRNAME
    ).exists()


def test_partial_directory_without_receipt_is_replaced_on_next_attempt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = _session(tmp_path)
    partial_dir = session / SAMPLE_STRATEGY_DIRNAME
    partial_dir.mkdir()
    (partial_dir / "stale.txt").write_text("partial", encoding="utf-8")
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    receipt = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(
            _available_payload(_source("strategy/strategy.py", "pass\n"))
        ),
    )

    assert receipt["status"] == "available"
    assert not (partial_dir / "stale.txt").exists()
    assert (partial_dir / "samples/001/strategy/strategy.py").is_file()


def test_only_available_samples_change_agent_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = init_session_dir(
        "CVX",
        "cvx-sample-render",
        tmp_path / "research",
        discover=False,
    )
    before = (session / "agent_context.md").read_text(encoding="utf-8")
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(
            {
                "items": [
                    _sample_item(
                        _source(
                            "strategy/strategy.py",
                            "from .helper import signal\n",
                        ),
                        _source("strategy/helper.py", "signal = 1\n"),
                    ),
                    _sample_item(
                        _source("strategy/strategy.py", "signal = 2\n"),
                        strategy_id="202",
                    ),
                ]
            }
        ),
    )
    render_session(session)

    context = (session / "agent_context.md").read_text(encoding="utf-8")
    readme = (session / "README.md").read_text(encoding="utf-8")
    assert "## Optional Sample Strategies" not in before
    assert "## Optional Sample Strategies" in context
    assert "`sample_strategy/samples/001/seed_context.json`" in context
    assert "`sample_strategy/samples/001/strategy/`" in context
    assert "`sample_strategy/samples/002/seed_context.json`" in context
    assert "`sample_strategy/samples/002/strategy/`" in context
    assert "recorded exploration history before" in context
    assert context.count("recorded exploration history") == 1
    assert "mechanism, input nodes" in context
    assert "not\nready current-session candidates" in context
    assert "do not directly reuse their strategy or\nsource in a current branch" in context
    assert "revalidate them unchanged" in context
    assert "form new hypotheses and strategy\nexpressions" in context
    assert "Optional Sample Strategies" not in readme


def test_available_receipt_is_terminal_and_render_does_not_revalidate_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = init_session_dir(
        "CVX",
        "cvx-sample-snapshot",
        tmp_path / "research",
        discover=False,
    )
    monkeypatch.setenv("ABEL_API_KEY", "test-key")
    first = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: _Response(
            _available_payload(_source("strategy/strategy.py", "pass\n"))
        ),
    )
    (session / "sample_strategy/samples/001/strategy/strategy.py").write_text(
        "# local snapshot remains readable\n",
        encoding="utf-8",
    )

    second = ensure_sample_strategy_context(
        session=session,
        ticker="CVX",
        opener=lambda *_args, **_kwargs: pytest.fail("must not refetch"),
    )
    render_session(session)

    assert second == first
    assert "## Optional Sample Strategies" in (session / "agent_context.md").read_text(
        encoding="utf-8"
    )


def test_init_session_reports_available_context_and_rerenders(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    root = tmp_path / "research"
    monkeypatch.setenv("ABEL_API_KEY", "test-key")

    def materialize(*, session: Path, ticker: str) -> dict:
        return sample_context.ensure_sample_strategy_context(
            session=session,
            ticker=ticker,
            opener=lambda *_args, **_kwargs: _Response(
                _available_payload(_source("strategy/strategy.py", "pass\n"))
            ),
        )

    monkeypatch.setattr(
        session_handler,
        "ensure_sample_strategy_context",
        materialize,
    )

    result = session_handler.handle_init_session(
        Namespace(
            ticker="CVX",
            exp_id="sample-cli",
            root=str(root),
            allow_outside_workspace=True,
            discover=False,
            discover_limit=12,
            backtest_start="2020-01-01",
        )
    )

    session = root / "cvx" / "cvx-sample-cli"
    output = capsys.readouterr().out
    assert result == 0
    assert (
        f"sample_strategy: available (count=1; see {session / 'agent_context.md'})"
        in output
    )
    assert "## Optional Sample Strategies" in (session / "agent_context.md").read_text(
        encoding="utf-8"
    )
    assert not (session / "branches").exists()
    events = (session / "events.tsv").read_text(encoding="utf-8")
    assert events.count("session_created") == 1
    assert "branch_created" not in events
    assert "round_recorded" not in events
    assert json.loads((session / "evidence_ledger.json").read_text(encoding="utf-8"))[
        "rows"
    ] == []
    dashboard = build_skill_dashboard_session_bundle(
        session,
        uploaded_at="2099-01-01T00:00:00+00:00",
    )
    assert dashboard["payload"]["branches"] == []
    assert dashboard["payload"]["rounds"] == []
    assert "sample_strategy" not in json.dumps(dashboard)


def test_unavailable_receipt_does_not_change_generated_agent_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session = init_session_dir(
        "CVX",
        "cvx-no-sample-render",
        tmp_path / "research",
        discover=False,
    )
    before = (session / "agent_context.md").read_text(encoding="utf-8")
    monkeypatch.delenv("ABEL_API_KEY", raising=False)
    monkeypatch.delenv("CAP_API_KEY", raising=False)
    monkeypatch.delenv("ABEL_AUTH_ENV_FILE", raising=False)

    receipt = ensure_sample_strategy_context(session=session, ticker="CVX")
    render_session(session)

    assert receipt["status"] == "unavailable"
    assert (session / "agent_context.md").read_text(encoding="utf-8") == before


def test_experiment_loop_only_routes_to_session_local_guidance() -> None:
    reference = (
        Path(__file__).resolve().parents[2]
        / "skills/abel-invest/references/experiment-loop.md"
    ).read_text(encoding="utf-8")

    assert "follow that\nsession-local section before broader exploration" in reference
    assert "recorded exploration history" not in reference
    assert "continue, adapt, compare, or reject" not in reference
