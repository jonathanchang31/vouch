"""FastAPI app for the review console.

MVP slice: queue + claim detail + approve/reject + audit timeline. No
WebSocket, no Bearer auth — those land alongside the HTTP transport (#1)
and multi-dim scopes (#2). Localhost-only by default.

The web layer is intentionally thin: every approve/reject goes through
``vouch.proposals.approve`` / ``vouch.proposals.reject`` so the audit log
is identical regardless of whether the action came from the CLI or the UI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import audit as audit_mod
from .. import proposals as proposals_mod
from ..models import ProposalStatus
from ..storage import ArtifactNotFoundError, KBStore, discover_root

_MODULE_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _MODULE_DIR / "templates"
_STATIC_DIR = _MODULE_DIR / "static"


def _is_review_event(name: str) -> bool:
    """The audit log carries every mutation; the timeline only shows
    review-gate decisions (approve / reject) and claim lifecycle moves."""
    if name.startswith("proposal.") and name.endswith((".approve", ".reject")):
        return True
    return name in {"claim.supersede", "claim.contradict",
                    "claim.archive", "claim.confirm"}


def _whoami() -> str:
    """Reviewer identity. Without the Bearer-auth layer from #1 this falls
    back to the same env var the CLI uses, so audit-log attribution stays
    consistent across surfaces."""
    return os.environ.get("VOUCH_AGENT", "web-reviewer")


def _proposal_preview(payload: dict[str, Any]) -> str:
    """One-line preview shown in the queue. Mirrors the CLI's `pending` output."""
    for key in ("text", "title", "name"):
        value = payload.get(key)
        if value:
            return str(value).strip().splitlines()[0][:160]
    return "—"


def build_app(kb_root: str | None = None) -> FastAPI:
    """FastAPI app bound to a KB root. ``kb_root`` defaults to the nearest
    ``.vouch/`` discovered by walking up from ``cwd``."""
    start = Path(kb_root).resolve() if kb_root else None
    # Resolve once at construction so every request hits the same store.
    # discover_root walks up looking for .vouch/ — the same behavior as
    # every other vouch CLI command. Failing here means a clearer error
    # than a 500 on the first request.
    root = discover_root(start)
    store = KBStore(root)

    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    app = FastAPI(title="vouch review-ui", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "kb": str(store.root),
            "pending": len(store.list_proposals(ProposalStatus.PENDING)),
        }

    @app.get("/", response_class=HTMLResponse)
    def queue(request: Request) -> Any:
        pending = store.list_proposals(ProposalStatus.PENDING)
        items = [
            {
                "id": p.id,
                "kind": p.kind.value,
                "proposed_by": p.proposed_by,
                "proposed_at": p.proposed_at.isoformat(timespec="seconds"),
                "preview": _proposal_preview(p.payload),
            }
            for p in pending
        ]
        return templates.TemplateResponse(
            request,
            "queue.html",
            {"items": items, "count": len(items)},
        )

    @app.get("/claim/{proposal_id}", response_class=HTMLResponse)
    def claim_detail(request: Request, proposal_id: str) -> Any:
        try:
            pr = store.get_proposal(proposal_id)
        except ArtifactNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return templates.TemplateResponse(
            request,
            "claim.html",
            {
                "proposal": pr.model_dump(mode="json"),
                "preview": _proposal_preview(pr.payload),
            },
        )

    @app.post("/approve/{proposal_id}")
    def approve(proposal_id: str, reason: str | None = Form(default=None)) -> Any:
        try:
            proposals_mod.approve(
                store, proposal_id, approved_by=_whoami(), reason=reason
            )
        except (proposals_mod.ProposalError, ArtifactNotFoundError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return RedirectResponse(url="/", status_code=303)

    @app.post("/reject/{proposal_id}")
    def reject(proposal_id: str, reason: str = Form(...)) -> Any:
        if not reason.strip():
            raise HTTPException(status_code=400, detail="reason is required")
        try:
            proposals_mod.reject(
                store, proposal_id, rejected_by=_whoami(), reason=reason
            )
        except (proposals_mod.ProposalError, ArtifactNotFoundError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return RedirectResponse(url="/", status_code=303)

    @app.get("/audit", response_class=HTMLResponse)
    def audit(request: Request, limit: int = 100) -> Any:
        events = list(audit_mod.read_events(store.kb_dir))
        events.reverse()  # newest first
        filtered = [e for e in events if _is_review_event(e.event)][:limit]
        rows = [
            {
                "id": e.id,
                "event": e.event,
                "actor": e.actor,
                "object_ids": e.object_ids,
                "at": e.created_at.isoformat(timespec="seconds"),
                "reason": e.data.get("reason"),
            }
            for e in filtered
        ]
        return templates.TemplateResponse(
            request,
            "audit.html",
            {"rows": rows, "count": len(rows)},
        )

    @app.get("/api/pending")
    def api_pending() -> JSONResponse:
        pending = store.list_proposals(ProposalStatus.PENDING)
        return JSONResponse(
            [
                {
                    "id": p.id,
                    "kind": p.kind.value,
                    "proposed_by": p.proposed_by,
                    "preview": _proposal_preview(p.payload),
                }
                for p in pending
            ]
        )

    return app
