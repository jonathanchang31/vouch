"""`vouch new` — scaffold typed page/entity proposals (issue #330)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from vouch.cli import cli
from vouch.models import ProposalKind, ProposalStatus
from vouch.storage import KBStore


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> KBStore:
    s = KBStore.init(tmp_path)
    monkeypatch.chdir(s.root)
    return s


def _declare_kinds(store: KBStore, kinds: dict[str, Any]) -> None:
    cfg = yaml.safe_load(store.config_path.read_text())
    assert isinstance(cfg, dict)
    cfg["page_kinds"] = kinds
    store.config_path.write_text(yaml.safe_dump(cfg))


def test_new_decision_page_stubs_frontmatter(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "decision", "--title", "pick X"])
    assert res.exit_code == 0, res.output
    proposal_id = res.output.strip()
    pr = store.get_proposal(proposal_id)
    assert pr.kind == ProposalKind.PAGE
    assert pr.status == ProposalStatus.PENDING
    assert pr.payload["type"] == "decision"
    assert pr.payload["title"] == "pick X"
    assert pr.payload["metadata"] == {}


def test_new_person_entity(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "person", "--name", "alice-example"])
    assert res.exit_code == 0, res.output
    pr = store.get_proposal(res.output.strip())
    assert pr.kind == ProposalKind.ENTITY
    assert pr.payload["type"] == "person"
    assert pr.payload["name"] == "alice-example"


def test_new_field_prefill_parsed_as_yaml(store: KBStore) -> None:
    _declare_kinds(store, {"meeting-notes": {"required_fields": ["attendees", "date"]}})
    runner = CliRunner()
    res = runner.invoke(
        cli,
        [
            "new",
            "meeting-notes",
            "--title",
            "Sync",
            "--field",
            "attendees=[alice-example, bob-example]",
            "--field",
            "date=2026-07-01",
        ],
    )
    assert res.exit_code == 0, res.output
    pr = store.get_proposal(res.output.strip())
    assert pr.payload["metadata"]["attendees"] == ["alice-example", "bob-example"]
    assert pr.payload["metadata"]["date"] == "2026-07-01"


def test_new_dry_run_writes_nothing(store: KBStore) -> None:
    _declare_kinds(store, {"meeting-notes": {"required_fields": ["attendees"]}})
    runner = CliRunner()
    res = runner.invoke(
        cli,
        ["new", "meeting-notes", "--title", "Sync", "--dry-run"],
    )
    assert res.exit_code == 0, res.output
    assert "missing required fields: attendees" in res.output
    assert store.list_proposals(ProposalStatus.PENDING) == []


def test_new_dry_run_json(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(
        cli,
        ["new", "decision", "--title", "pick X", "--dry-run", "--json"],
    )
    assert res.exit_code == 0, res.output
    body = json.loads(res.output)
    assert body["dry_run"] is True
    assert body["target"] == "page"
    assert body["kind"] == "decision"
    assert body["title"] == "pick X"
    assert "proposal_id" in body
    assert store.list_proposals(ProposalStatus.PENDING) == []


def test_new_collision_decision_defaults_to_page(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "decision", "--title", "pick Y"])
    assert res.exit_code == 0, res.output
    pr = store.get_proposal(res.output.strip())
    assert pr.kind == ProposalKind.PAGE


def test_new_collision_decision_entity_flag(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(
        cli,
        ["new", "decision", "--entity", "--name", "pick-z"],
    )
    assert res.exit_code == 0, res.output
    pr = store.get_proposal(res.output.strip())
    assert pr.kind == ProposalKind.ENTITY
    assert pr.payload["type"] == "decision"


def test_new_project_routes_to_entity(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "project", "--name", "vouch-example"])
    assert res.exit_code == 0, res.output
    pr = store.get_proposal(res.output.strip())
    assert pr.kind == ProposalKind.ENTITY
    assert pr.payload["type"] == "project"


def test_new_unknown_kind_lists_known(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "not-a-kind", "--title", "X"])
    assert res.exit_code != 0, res.output
    assert "unknown kind" in res.output
    assert "decision" in res.output
    assert "person" in res.output


def test_new_required_citations_reminder_in_body(store: KBStore) -> None:
    _declare_kinds(store, {"cited": {"required_citations": True}})
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "cited", "--title", "needs cites", "--dry-run"])
    assert res.exit_code == 0, res.output
    assert "citations required" in res.output
    assert "citation_reminder" not in res.output or "citations: required" in res.output


def test_new_pending_not_approved(store: KBStore) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "concept", "--title", "draft page"])
    assert res.exit_code == 0, res.output
    assert len(store.list_pages()) == 0
    pending = store.list_proposals(ProposalStatus.PENDING)
    assert len(pending) == 1
