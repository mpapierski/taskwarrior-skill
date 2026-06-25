# Quick Operations

Use this file for common agent tasks: capture, list, summarize, annotate, modify, start/stop, complete, delete, and light triage. Load deeper references only when the task goes beyond these recipes.

## Minimal Query Flow

- Use `task export` or filtered export for machine-readable inspection.
- Use `count` for existence/cardinality checks; it exits 0 and prints `0` for no matches.
- Use human reports only when the user wants terminal-style output.

```bash
task +READY export
task project:Repo count
task project:Repo +OVERDUE export
task rc.json.array=0 +READY export
```

Summarize ID, description, project, status, priority, due/scheduled/wait timing, dependency state, and notable tags. Omit UUIDs, timestamps, urgency, and raw JSON unless requested.

## Capture

Keep descriptions short and put detail in annotations. Use `rc.verbose=new-uuid` when durable identity matters.

```bash
task rc.verbose=new-uuid add "Ship release notes" project:Repo.Release priority:H +docs due:friday
task rc.verbose=new-uuid add -- +bug is part of the title
task 4 annotate "Acceptance: release notes cover migration and rollback steps."
```

Use `--` when description text starts with metadata-like tokens. Keep real attributes as separate trailing args.

## Modify And Triage

Prefer narrow ID or UUID filters. Verify when the result matters.

```bash
task 4 modify project:Repo.Backlog +triage scheduled:tomorrow
task 4 annotate "Blocked on API schema review."
task 4 start
task 4 stop
task 4 export
```

For multiple tasks, count/export first and use non-interactive overrides:

```bash
task project:Repo +triage count
task rc.confirmation=off rc.bulk=0 project:Repo +triage modify priority:M
task project:Repo +triage export
```

## Complete, Delete, And Recover

Use `done` and `delete`, not `modify status:completed` or `modify status:deleted`.

```bash
task 4 done
task rc.confirmation=off 4 delete
task rc.confirmation=off undo
```

For bulk done/delete, add `rc.bulk=0` and verify afterward:

```bash
task 1-5 count
task rc.confirmation=off rc.bulk=0 1-5 done
task 1-5 export
```

## Lightweight Modeling

- Use dotted projects for areas or workstreams: `project:Repo`, `project:Repo.Release`.
- Use tags for cross-cutting labels: `+bug`, `+docs`, `+blocked`.
- Use `due` only for real deadlines; use `scheduled` for earliest start and `wait` to hide deferred work.
- Use annotations for links, acceptance criteria, blockers, notes, and decisions.
- Use dependencies only when sequence matters.

```bash
task add "Implement API client" project:Repo.SDK
task add "Wire client into CLI" project:Repo.SDK depends:1
task blocked
task blocking
task unblocked
```

## Load More When Needed

- Exact command construction, quoting, descriptions, import, purge, or write edge cases: `write-commands.md` and `commands-and-syntax.md`.
- Filters, reports, search, custom columns, or no-match behavior: `filters-search-reports.md`.
- Date parsing and date-sensitive work: `dates-and-scheduling.md`.
- Task modeling depth, recurrence, dependencies, urgency, UDAs: `task-modeling.md`.
- Contexts or persistent config: `contexts.md`, `taskrc-configuration.md`, and `agent-runtime-safety.md`.
