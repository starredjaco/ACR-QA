"""
Tests for CORE/tasks.py — the Celery task layer.

`CORE/tasks.py` was claimed shipped in v3.3.0 but had 0% coverage as of
Phase 0 (May 6 2026). This test file makes sure the task is wired up,
the success path returns the expected dict shape, and the failure path
re-raises the exception (so Celery surfaces FAILURE state to the caller).

We use `.apply()` (not `.delay()`) so the task runs synchronously in the
test process without ever touching the Redis broker. A nightly
integration test against a real worker can be added later under
`@pytest.mark.integration` if needed.

See `docs/GOD_MODE_PLAN.md` §9.3.2 for the rationale.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from CORE.tasks import celery_app, run_analysis_task


@pytest.fixture(autouse=True)
def _eager_celery():
    """Force Celery into synchronous (eager) mode for the duration of each test.

    Combined with `.apply()` instead of `.delay()` and an in-memory result
    backend, this keeps every assertion in-process — no Redis, no worker,
    no network.
    """
    saved = {
        "always_eager": celery_app.conf.task_always_eager,
        "propagates": celery_app.conf.task_eager_propagates,
        "result_backend": celery_app.conf.result_backend,
        "store_eager": celery_app.conf.task_store_eager_result,
    }
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    # Override the Redis result backend so .get() / .successful() don't reach out.
    celery_app.conf.result_backend = "cache+memory://"
    celery_app.conf.task_store_eager_result = False
    yield
    celery_app.conf.task_always_eager = saved["always_eager"]
    celery_app.conf.task_eager_propagates = saved["propagates"]
    celery_app.conf.result_backend = saved["result_backend"]
    celery_app.conf.task_store_eager_result = saved["store_eager"]


# ── Task registration / config ────────────────────────────────────────────────


def test_task_is_registered_under_canonical_name():
    """The task should be registered as `acrqa.run_analysis` so the FastAPI
    `POST /v1/scans` endpoint can dispatch it by name."""
    assert "acrqa.run_analysis" in celery_app.tasks
    # Celery wraps the function in a Task instance — check identity by name, not object.
    assert celery_app.tasks["acrqa.run_analysis"].name == run_analysis_task.name


def test_celery_app_uses_json_serialization():
    """JSON serialization is required because Celery's pickle default is
    a known RCE vector, and we explicitly opt out of it in CORE/tasks.py."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert "json" in celery_app.conf.accept_content


def test_task_track_started_is_enabled():
    """The FastAPI scan-status endpoint depends on STARTED state being
    visible — without this, polling can only see PENDING / SUCCESS / FAILURE."""
    assert celery_app.conf.task_track_started is True


def test_result_expiry_is_24_hours():
    """Results stay queryable for 24h; tighten if memory becomes an issue."""
    assert celery_app.conf.result_expires == 86400


# ── Success path ──────────────────────────────────────────────────────────────


def test_success_path_returns_completed_status():
    """When the pipeline returns a run_id, the task wraps it in a dict
    with status=completed and propagates run_id + repo_name."""

    class _Stub:
        def __init__(self, target_dir):
            self.target_dir = target_dir

        def run(self, **_kw):
            return 42

    with patch("CORE.main.AnalysisPipeline", side_effect=_Stub):
        result = run_analysis_task.apply(args=("/tmp/whatever",), kwargs={"repo_name": "my-repo"})

    assert result.successful()
    payload = result.get(timeout=5)
    assert payload["status"] == "completed"
    assert payload["run_id"] == 42
    assert payload["repo"] == "my-repo"


def test_success_path_with_tuple_return_extracts_findings_count():
    """Some pipeline paths return (run_id, findings_count) instead of just run_id.
    The task should detect the tuple shape and surface findings_count separately."""

    class _Stub:
        def __init__(self, target_dir):
            self.target_dir = target_dir

        def run(self, **_kw):
            return (7, 25)

    with patch("CORE.main.AnalysisPipeline", side_effect=_Stub):
        result = run_analysis_task.apply(args=("/tmp/whatever",), kwargs={"repo_name": "tuple-repo"})

    payload = result.get(timeout=5)
    assert payload["status"] == "completed"
    assert payload["run_id"] == 7
    assert payload["findings_count"] == 25


def test_none_return_yields_failed_status():
    """The pipeline returns None when rate-limited; the task should
    convert that into a failed-status dict so the caller can see why."""

    class _Stub:
        def __init__(self, target_dir):
            self.target_dir = target_dir

        def run(self, **_kw):
            return None

    with patch("CORE.main.AnalysisPipeline", side_effect=_Stub):
        result = run_analysis_task.apply(args=("/tmp/whatever",))

    payload = result.get(timeout=5)
    assert payload["status"] == "failed"
    assert "Rate limited" in payload["error"]


# ── Failure path ──────────────────────────────────────────────────────────────


def test_pipeline_exception_is_reraised():
    """Exceptions inside the pipeline must propagate so Celery records
    FAILURE state. Swallowing them would leave callers polling forever."""

    class _BoomStub:
        def __init__(self, target_dir):
            self.target_dir = target_dir

        def run(self, **_kw):
            raise RuntimeError("simulated pipeline crash")

    with patch("CORE.main.AnalysisPipeline", side_effect=_BoomStub):
        with pytest.raises(RuntimeError, match="simulated pipeline crash"):
            run_analysis_task.apply(args=("/tmp/whatever",)).get(timeout=5)


# ── Argument plumbing ─────────────────────────────────────────────────────────


def test_kwargs_forwarded_to_pipeline_run():
    """repo_name, pr_number, and limit all flow through to pipeline.run().
    A regression here would silently drop PR numbers (breaking PR comments)
    or limits (causing AI-explanation cost overruns)."""
    captured: dict = {}

    class _CapturingStub:
        def __init__(self, target_dir):
            captured["target_dir"] = target_dir

        def run(self, **kw):
            captured.update(kw)
            return 99

    with patch("CORE.main.AnalysisPipeline", side_effect=_CapturingStub):
        run_analysis_task.apply(
            args=("/tmp/path",),
            kwargs={"repo_name": "my-pr", "pr_number": 123, "limit": 5},
        ).get(timeout=5)

    assert captured["target_dir"] == "/tmp/path"
    assert captured["repo_name"] == "my-pr"
    assert captured["pr_number"] == 123
    assert captured["limit"] == 5
