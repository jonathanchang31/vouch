# Company brain: a team memory that goes through the review gate

vouch can run your team's shared memory — who you work with, what each
project is doing, what you owe people, why you decided things — as typed,
reviewable records. Nothing about this is a separate mode: records are
ordinary pages with a declared kind, every write is a proposal a human
approves, and the audit log keeps the history. What this guide adds is a
set of conventions plus three small tools: an init template, frontmatter
filters, and a daily digest.

## Setup

```sh
vouch init --template company-brain
vouch install-mcp claude-code --tier T4   # slash commands + hooks for agents
```

The template declares seven page kinds in `.vouch/config.yaml` (inspect
them with `vouch schema list`):

| kind | frontmatter | rule |
|---|---|---|
| `contact` | `role` (required), `org`, `email` | a person you work with |
| `org` | `website` | a company or organisation |
| `project-record` | `record_status` (required), `owner` | one project's living record |
| `meeting-notes` | `date`, `attendees` | notes from one meeting |
| `followup` | `due_at`, `followup_status` (required), `owner` | a dated commitment |
| `decision-record` | — | must cite claims/sources |
| `voice` | — | must cite the examples it distills |

Kinds you've already declared are never overwritten, and the template is
idempotent. Extend the set by editing `config.yaml: page_kinds` — a schema
change is a reviewed diff like everything else.

## The conventions

**A person or org is an entity plus a typed page.** `kb_propose_entity`
(type `person` / `company`) pairs with a `contact` / `org` page carrying the
structured frontmatter. Relations (`owned_by`, `relates_to`) link people to
orgs and projects.

**Work is a `project-record`; commitments are `followup` pages.** A followup
carries `due_at` and `followup_status: open`. Closing one is a page-edit
proposal (`slug_hint: <page id>`, `followup_status: done`) — status changes
go through the gate and land in the audit log like any other write.

**Decisions and voice must cite.** The `decision-record` and `voice` kinds
set `required_citations: true`, so the gate rejects an uncited one at both
propose and approve time.

## Querying records

`kb.list_pages` (and the `vouch pages` mirror) filters on kind and
frontmatter — equality plus inclusive bounds that order numbers and ISO
dates correctly:

```sh
vouch pages --kind followup --meta followup_status=open --before due_at=2026-07-10
vouch pages --kind contact --meta org=acme-example --json
```

Deliberately not a query language: equality and bounds on declared fields,
nothing more. The yaml files stay the only source of truth.

## The daily loop

Agents file proposals all day (see the slash commands below). A human
reviews with `vouch review` or `vouch approve <id...>`. The briefing that
tells you where to spend attention:

```sh
vouch digest                 # pending oldest-first, decisions, stale, followups due
vouch digest --format markdown --since 1d
```

It is read-only by construction — safe to run from cron and pipe wherever
the team reads its mornings:

```cron
0 8 * * 1-5  cd /path/to/repo && vouch digest --format markdown > /tmp/kb-digest.md
```

`kb.digest` exposes the same briefing to agents over MCP/JSONL.

## Slash commands (installed with the claude-code adapter)

- `/vouch-ask` — answer from the KB with citations, or say what's missing.
- `/vouch-remember` — register the user's words as a source, propose claims
  citing it.
- `/vouch-record` — file a contact/org/project as entity + typed page.
- `/vouch-followup` — file a dated commitment.
- `/vouch-standup` — narrate `vouch digest`.

Every flow terminates at `kb_propose_*`; none may call `kb_approve`. The
human at the gate decides what the brain believes.

## The honest constraint

A team memory multiplies small writes, so the review queue is the
bottleneck by design: "remember X" is invisible to retrieval until someone
approves it. `vouch digest`, batch approval (`vouch approve a b c`), and
`vouch review` keep the queue moving; if you stop reviewing, the brain
stops learning — that's the deal, and it's what makes the answers
trustworthy.
