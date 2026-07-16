"""Optional official sample strategy context for a new Abel Invest session."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from abel_invest.narrative_core.contracts.constants import DEFAULT_ABEL_ROUTER_BASE_URL
from abel_invest.narrative_core.io import SessionLock, read_env_file_values

SAMPLE_STRATEGY_DIRNAME = "sample_strategy"
SAMPLE_STRATEGY_SAMPLES_DIRNAME = "samples"
SAMPLE_STRATEGY_LOOKUP_FILENAME = "lookup.json"
SAMPLE_STRATEGY_CONTEXT_FILENAME = "seed_context.json"
SAMPLE_STRATEGY_LOOKUP_SCHEMA = "abel-invest.sample-strategy-lookup/v1"
SAMPLE_STRATEGY_ENDPOINT = "/api/v1/official-strategy-pool/sample-strategies"
SAMPLE_STRATEGY_TIMEOUT_SECONDS = 20

_TERMINAL_STATUSES = {"available", "not_found", "unavailable"}
_CLIENT_OWNED_PATHS = {
    SAMPLE_STRATEGY_LOOKUP_FILENAME,
    SAMPLE_STRATEGY_CONTEXT_FILENAME,
}
_IGNORED_SEED_CONTEXT_FIELDS = {"usage_note"}


class SampleStrategyPackageError(ValueError):
    """The router response cannot be materialized completely and safely."""


def ensure_sample_strategy_context(
    *,
    session: Path,
    ticker: str,
    opener=urlopen,
    timeout: int = SAMPLE_STRATEGY_TIMEOUT_SECONDS,
) -> dict:
    """Fetch at most once for a session and always fail open."""

    session = Path(session)
    normalized_ticker = str(ticker or "").strip().upper()
    existing = _load_sample_strategy_receipt(session)
    if existing is not None:
        return existing

    attempted_at = datetime.now(UTC).isoformat()
    api_key = _resolve_api_key()
    if not api_key:
        return _persist_terminal_receipt_safely(
            session=session,
            receipt=_build_receipt(
                ticker=normalized_ticker,
                status="unavailable",
                attempted_at=attempted_at,
                reason_code="auth_missing",
                sample_count=0,
            ),
        )

    try:
        payload = _fetch_sample_strategy(
            ticker=normalized_ticker,
            api_key=api_key,
            opener=opener,
            timeout=timeout,
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise SampleStrategyPackageError("items must be a list")
        if not items:
            return _persist_terminal_receipt_safely(
                session=session,
                receipt=_build_receipt(
                    ticker=normalized_ticker,
                    status="not_found",
                    attempted_at=attempted_at,
                    reason_code=None,
                    sample_count=0,
                ),
            )
        packages = [_parse_package(item) for item in items]
        receipt = _build_receipt(
            ticker=normalized_ticker,
            status="available",
            attempted_at=attempted_at,
            reason_code=None,
            sample_count=len(packages),
        )
        return _materialize_available_packages(
            session=session,
            packages=packages,
            receipt=receipt,
        )
    except HTTPError as exc:
        reason_code = f"http_{exc.code}"
    except TimeoutError:
        reason_code = "timeout"
    except URLError:
        reason_code = "request_failed"
    except (UnicodeDecodeError, json.JSONDecodeError):
        reason_code = "invalid_json"
    except SampleStrategyPackageError:
        reason_code = "invalid_package"
    except OSError:
        reason_code = "local_io_failed"
    except Exception:
        reason_code = "unexpected_error"

    return _persist_terminal_receipt_safely(
        session=session,
        receipt=_build_receipt(
            ticker=normalized_ticker,
            status="unavailable",
            attempted_at=attempted_at,
            reason_code=reason_code,
            sample_count=0,
        ),
    )


def _load_sample_strategy_receipt(session: Path) -> dict | None:
    """Load a completed lookup marker without triggering network work."""

    path = Path(session) / SAMPLE_STRATEGY_DIRNAME / SAMPLE_STRATEGY_LOOKUP_FILENAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("status") not in _TERMINAL_STATUSES:
        return None
    return payload


def load_available_sample_strategies(session: Path) -> list[dict]:
    """Load available context paths without revalidating or refetching them."""

    session = Path(session)
    receipt = _load_sample_strategy_receipt(session)
    if receipt is None or receipt.get("status") != "available":
        return []
    sample_count = receipt.get("sample_count")
    if (
        not isinstance(sample_count, int)
        or isinstance(sample_count, bool)
        or sample_count < 1
    ):
        return []
    samples_dir = session / SAMPLE_STRATEGY_DIRNAME / SAMPLE_STRATEGY_SAMPLES_DIRNAME
    return [
        {
            "rank": rank,
            "context_path": samples_dir
            / f"{rank:03d}"
            / SAMPLE_STRATEGY_CONTEXT_FILENAME,
            "source_dir": samples_dir / f"{rank:03d}" / "strategy",
        }
        for rank in range(1, sample_count + 1)
    ]


def _fetch_sample_strategy(
    *,
    ticker: str,
    api_key: str,
    opener,
    timeout: int,
) -> dict:
    base_url = (
        os.getenv("ABEL_ROUTER_BASE_URL", "").strip()
        or os.getenv("CAP_ROUTER_BASE_URL", "").strip()
        or DEFAULT_ABEL_ROUTER_BASE_URL
    ).rstrip("/")
    url = f"{base_url}{SAMPLE_STRATEGY_ENDPOINT}?{urlencode({'ticker': ticker})}"
    request = Request(
        url,
        headers={"Accept": "application/json", "api-key": api_key},
        method="GET",
    )
    with opener(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise SampleStrategyPackageError("response must be an object")
    if isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload


def _resolve_api_key() -> str:
    token = (os.getenv("ABEL_API_KEY") or os.getenv("CAP_API_KEY") or "").strip()
    if token:
        return token
    auth_file = os.getenv("ABEL_AUTH_ENV_FILE", "").strip()
    if not auth_file:
        return ""
    try:
        values = read_env_file_values(Path(auth_file).expanduser())
    except (OSError, UnicodeDecodeError):
        return ""
    return (values.get("ABEL_API_KEY") or values.get("CAP_API_KEY") or "").strip()


def _parse_package(item: object) -> tuple[dict, list[tuple[PurePosixPath, str, str]]]:
    if not isinstance(item, dict):
        raise SampleStrategyPackageError("sample item must be an object")
    seed_context = item.get("seedContext")
    source_files = item.get("sourceFiles")
    if not isinstance(seed_context, dict):
        raise SampleStrategyPackageError("seedContext must be an object")
    if not isinstance(source_files, list):
        raise SampleStrategyPackageError("sourceFiles must be a list")
    seed_context = {
        key: value
        for key, value in seed_context.items()
        if key not in _IGNORED_SEED_CONTEXT_FIELDS
    }

    parsed: list[tuple[PurePosixPath, str, str]] = []
    seen_paths: set[str] = set()
    for source_file in source_files:
        if not isinstance(source_file, dict):
            raise SampleStrategyPackageError("source file must be an object")
        raw_path = source_file.get("path")
        content = source_file.get("content")
        expected_sha = source_file.get("sha256")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise SampleStrategyPackageError("source path is required")
        if not isinstance(content, str) or not isinstance(expected_sha, str):
            raise SampleStrategyPackageError("source content and sha256 are required")

        relative_path = PurePosixPath(raw_path)
        normalized_path = relative_path.as_posix()
        if (
            relative_path.is_absolute()
            or normalized_path in {"", "."}
            or ".." in relative_path.parts
            or normalized_path in _CLIENT_OWNED_PATHS
            or normalized_path in seen_paths
        ):
            raise SampleStrategyPackageError("source path is unsafe or duplicated")
        actual_sha = sha256(content.encode("utf-8")).hexdigest()
        if actual_sha != expected_sha.strip().lower():
            raise SampleStrategyPackageError("source content hash mismatch")
        seen_paths.add(normalized_path)
        parsed.append((relative_path, content, actual_sha))
    return seed_context, parsed


def _materialize_available_packages(
    *,
    session: Path,
    packages: list[tuple[dict, list[tuple[PurePosixPath, str, str]]]],
    receipt: dict,
) -> dict:
    staging = Path(tempfile.mkdtemp(prefix=".sample-strategy-", dir=session))
    published = False
    try:
        for rank, (seed_context, source_files) in enumerate(packages, start=1):
            package_dir = staging / SAMPLE_STRATEGY_SAMPLES_DIRNAME / f"{rank:03d}"
            _write_json_atomic(
                package_dir / SAMPLE_STRATEGY_CONTEXT_FILENAME,
                seed_context,
            )
            for relative_path, content, expected_sha in source_files:
                destination = package_dir.joinpath(*relative_path.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
                if sha256(destination.read_bytes()).hexdigest() != expected_sha:
                    raise OSError("written source hash mismatch")

        sample_dir = session / SAMPLE_STRATEGY_DIRNAME
        with SessionLock(session):
            existing = _load_sample_strategy_receipt(session)
            if existing is not None:
                return existing
            if sample_dir.exists():
                shutil.rmtree(sample_dir)
            staging.replace(sample_dir)
            published = True
            _write_json_atomic(sample_dir / SAMPLE_STRATEGY_LOOKUP_FILENAME, receipt)
        return receipt
    finally:
        if not published and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _persist_terminal_receipt_safely(*, session: Path, receipt: dict) -> dict:
    try:
        sample_dir = Path(session) / SAMPLE_STRATEGY_DIRNAME
        with SessionLock(Path(session)):
            existing = _load_sample_strategy_receipt(session)
            if existing is not None:
                return existing
            if sample_dir.exists():
                shutil.rmtree(sample_dir)
            sample_dir.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(sample_dir / SAMPLE_STRATEGY_LOOKUP_FILENAME, receipt)
    except Exception:
        pass
    return receipt


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        temp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def _build_receipt(
    *,
    ticker: str,
    status: str,
    attempted_at: str,
    reason_code: str | None,
    sample_count: int,
) -> dict:
    return {
        "schema": SAMPLE_STRATEGY_LOOKUP_SCHEMA,
        "status": status,
        "ticker": ticker,
        "attempted_at": attempted_at,
        "reason_code": reason_code,
        "sample_count": sample_count,
    }
