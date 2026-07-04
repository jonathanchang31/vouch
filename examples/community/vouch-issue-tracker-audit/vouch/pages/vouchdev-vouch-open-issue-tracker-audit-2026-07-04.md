---
id: vouchdev-vouch-open-issue-tracker-audit-2026-07-04
title: vouchdev/vouch open-issue tracker audit — 2026-07-04
type: report
status: draft
claims:
- vouchdev-vouch-issue-100-feat-richer-scopes-on-claim-source-
- vouchdev-vouch-issue-166-bundle-import-can-overwrite-the-aud
- vouchdev-vouch-issue-168-critical-agent-transport-allows-cro
- vouchdev-vouch-issue-189-richer-scopes-on-claim-source-per-v
- vouchdev-vouch-issue-54-epic-make-vouch-friendlier-and-more-
- vouchdev-vouch-issue-76-crystallize-bypasses-the-review-gate
- vouchdev-vouch-issue-78-kb-context-returns-archived-supersed
- vouchdev-vouch-issue-80-import-check-accepts-bundles-whose-m
- vouchdev-vouch-issue-81-claim-model-has-no-min-evidence-vali
- vouchdev-vouch-issue-92-retrieve-ignores-retrieval-backends-
- vouchdev-vouch-issue-93-feat-vouch-approve-batch-for-scripta
- vouchdev-vouch-issue-94-feat-http-transport-for-vouch-serve-
- vouchdev-vouch-issue-95-vouch-serve-should-fail-clearly-when
entities: []
sources: []
tags: []
metadata: {}
created_at: '2026-07-04T06:17:24.368089Z'
updated_at: '2026-07-04T06:17:24.368096Z'
---
## Method

Every open issue in `vouchdev/vouch` (93 at audit time) was cross-referenced
against `git log --grep` on `upstream/main` and `upstream/test` for a commit
mentioning that issue number, then spot-checked by reading the relevant
source file directly (not just trusting the commit message). Issues already
linked from an in-flight open PR were excluded up front, since those aren't
stale — they're just not merged yet.

## Findings

| Issue | Title | Status found |
|---|---|---|
| [#54](https://github.com/vouchdev/vouch/issues/54) | epic: make vouch friendlier | partially fixed (CLI-output track), open |
| [#76](https://github.com/vouchdev/vouch/issues/76) | crystallize bypasses review gate | fixed, open |
| [#78](https://github.com/vouchdev/vouch/issues/78) | kb.context returns archived/superseded claims | fixed, open |
| [#80](https://github.com/vouchdev/vouch/issues/80) | import_check accepts bundles missing manifest files | fixed, open |
| [#81](https://github.com/vouchdev/vouch/issues/81) | Claim model has no min-evidence validator | fixed, open |
| [#92](https://github.com/vouchdev/vouch/issues/92) | _retrieve ignores retrieval.backends config | fixed, open |
| [#93](https://github.com/vouchdev/vouch/issues/93) | vouch approve --batch | fixed, open |
| [#94](https://github.com/vouchdev/vouch/issues/94) | HTTP transport for vouch serve | fixed, open |
| [#95](https://github.com/vouchdev/vouch/issues/95) | vouch serve fails unclearly with no KB | fixed, open |
| [#100](https://github.com/vouchdev/vouch/issues/100) | richer scopes VEP | VEP drafted only, open |
| [#189](https://github.com/vouchdev/vouch/issues/189) | richer scopes implementation | genuinely open, unclaimed |
| [#166](https://github.com/vouchdev/vouch/issues/166) | bundle import can overwrite audit log | fixed + merged (PR #183), open |
| [#168](https://github.com/vouchdev/vouch/issues/168) | cross-agent approval bypass | **still unfixed**, security-relevant |

11 of these 13 issues describe bugs or features that are already resolved in
code but left open on GitHub — likely because merges to non-default branches
(or squash-merge commits) don't trigger GitHub's auto-close. One (#189) is a
genuinely open, unclaimed implementation gap behind a drafted VEP. One (#168)
is a real, unfixed, security-relevant bug with a maintainer review already on
record (from a prior closed PR) describing exactly what a correct fix needs
to do.

## Why this matters for contributors

Before picking an open issue to work on in this repo, check whether it's
already fixed upstream — `git log --oneline -E --grep="#<N>([^0-9]|$)"
upstream/main upstream/test` takes seconds and avoids a wasted or duplicate
PR. This KB is the evidence trail for one pass of that check; see each
claim's citation for the exact commit, code, or review comment behind it.
