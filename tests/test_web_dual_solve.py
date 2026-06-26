"""Tests for the dual-solve web runner (the SPA backend)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vouch import dual_solve as ds
from vouch.storage import KBStore
from vouch.web import create_app

pytest.importorskip("fastapi", reason="dual-solve web needs the [web] extra")

from fastapi.testclient import TestClient


@pytest.fixture
def git_kb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> KBStore:
    # dual-solve needs a git repo; the kb lives at its root.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    s = KBStore.init(tmp_path)
    monkeypatch.chdir(s.root)
    return s


def _client(git_kb: KBStore, *, enabled: bool = True) -> TestClient:
    app = create_app(str(git_kb.root), allow_dual_solve=enabled)
    return TestClient(app)


def test_dual_solve_page_renders_when_enabled(git_kb):
    r = _client(git_kb).get("/dual-solve")
    assert r.status_code == 200
    assert "dual-solve-app" in r.text  # the Vue mount point


def test_dual_solve_routes_absent_when_disabled(git_kb):
    r = _client(git_kb, enabled=False).get("/dual-solve")
    assert r.status_code == 404


def _fake_prepare(monkeypatch, *, calls):
    issue = ds.Issue("Fix bug", "body", number=4, url="u")
    cA = ds.Candidate("claude", "vouch-dual/4-fix-bug-claude", Path("/w/claude"),
                      diff="diff --git a/x b/x\n+1\n", sha="s1", ok=True)
    cX = ds.Candidate("codex", "vouch-dual/4-fix-bug-codex", Path("/w/codex"),
                      diff="diff --git a/y b/y\n+2\n", sha="s2", ok=True)

    def fake(store, issue_ref, root, runner, *, claude_effort="high",
             codex_effort="high", autonomy="edit", dry_run=False,
             workdir=None, on_progress=None):
        calls.append({"autonomy": autonomy, "issue_ref": issue_ref})
        if on_progress:
            on_progress("running claude (effort=high)")
        return issue, [cA, cX], {"claude": object(), "codex": object()}

    monkeypatch.setattr("vouch.dual_solve.prepare", fake)
    return issue


def _wait(client, job_id, want, tries=50):
    import time
    for _ in range(tries):
        r = client.get(f"/dual-solve/job/{job_id}")
        if r.status_code == 200 and r.json()["status"] in want:
            return r.json()
        time.sleep(0.02)
    raise AssertionError(f"job never reached {want}: {r.json()}")


def test_run_starts_job_and_reaches_ready(git_kb, monkeypatch):
    calls: list = []
    _fake_prepare(monkeypatch, calls=calls)
    c = _client(git_kb)
    r = c.post("/dual-solve/run", json={"issue_url": "o/n#4"})
    assert r.status_code == 201
    job_id = r.json()["job_id"]
    state = _wait(c, job_id, {"ready"})
    assert [x["engine"] for x in state["candidates"]] == ["claude", "codex"]
    # autonomy is forced to edit regardless of input
    assert calls[0]["autonomy"] == "edit"


def test_run_is_single_flight(git_kb, monkeypatch):
    calls: list = []
    _fake_prepare(monkeypatch, calls=calls)
    c = _client(git_kb)
    first = c.post("/dual-solve/run", json={"issue_url": "o/n#4"})
    assert first.status_code == 201
    # a second run while the first is active is rejected
    second = c.post("/dual-solve/run", json={"issue_url": "o/n#4"})
    assert second.status_code == 409


def test_run_rejects_unparseable_issue(git_kb, monkeypatch):
    calls: list = []
    _fake_prepare(monkeypatch, calls=calls)
    r = _client(git_kb).post("/dual-solve/run", json={"issue_url": "not-an-issue"})
    assert r.status_code == 400


def test_progress_frame_reaches_websocket(git_kb, monkeypatch):
    calls: list = []
    _fake_prepare(monkeypatch, calls=calls)
    c = _client(git_kb)
    with c.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "hello"
        c.post("/dual-solve/run", json={"issue_url": "o/n#4"})
        seen = []
        for _ in range(10):
            frame = ws.receive_json()
            seen.append(frame)
            if frame.get("type") == "dual_solve" and frame.get("event") == "progress":
                break
        assert any(f.get("type") == "dual_solve" and f.get("event") == "progress"
                   for f in seen)
