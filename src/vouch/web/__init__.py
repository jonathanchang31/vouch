"""Browser-based review console for vouch.

The web layer is a *viewport* over the existing kb.* surface — every action
(approve, reject) goes through the same ``vouch.proposals`` / ``vouch.storage``
code path as the CLI, so the audit log is identical regardless of surface.

The dependencies (fastapi, jinja2) live behind the ``[web]`` extra so the
base install stays light. ``vouch review-ui`` produces an actionable
``ImportError`` line if the extra is missing.
"""

from __future__ import annotations


def _require_web_extra() -> None:
    """Fail with a clean message if fastapi/jinja2 aren't installed."""
    missing: list[str] = []
    try:
        import fastapi  # noqa: F401
    except ImportError:
        missing.append("fastapi")
    try:
        import jinja2  # noqa: F401
    except ImportError:
        missing.append("jinja2")
    if missing:
        raise ImportError(
            "vouch review-ui needs the [web] extra. "
            "Install with: pip install 'vouch-kb[web]'  "
            f"(missing: {', '.join(missing)})"
        )


def create_app(kb_root: str | None = None):  # type: ignore[no-untyped-def]
    """Build the FastAPI app for a given KB root. Lazy-imports the web stack."""
    _require_web_extra()
    from .server import build_app

    return build_app(kb_root)


__all__ = ["create_app"]
