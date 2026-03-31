---
name: taskwarrior
description: Manage task lists with Taskwarrior instead of TODO.md, using a repo-local `.taskwarrior` store by default and the bundled `scripts/taskw.py` wrapper to round-trip tasks through `.taskwarrior/tasks.yaml`. Use when capturing, triaging, listing, prioritizing, tagging, annotating, scheduling, sequencing, reporting, or completing work with Taskwarrior; fall back to plain `task ...` only when repo instructions explicitly require the global Taskwarrior config and data.
---

# Taskwarrior

## Overview

Use Taskwarrior as the task system for the current repo. Prefer the repo-local wrapper so the working tree contains a machine-readable task snapshot and does not depend on a handwritten `TODO.md`.

## Requirement

- Require `PyYAML` in the active Python environment for repo-local wrapper usage.
- Invoke the wrapper with the Python interpreter that belongs to the current project or virtualenv.
- Do not assume `uv`, `pip`, `poetry`, or any other package manager unless the repo already uses one.

## Choose Scope

1. Check repo instructions first.
   If `AGENTS.md` or other repo guidance says to use the global Taskwarrior database, use plain `task ...` with no overrides.
2. Default to repo-local storage.
   Run `python scripts/taskw.py ...` from this skill folder, using the project's active Python environment.
3. Keep the repo-local store inside `.taskwarrior/`.
   The wrapper manages `.taskwarrior/taskrc`, `.taskwarrior/data/`, and `.taskwarrior/tasks.yaml`.

## Repo-Local Workflow

- Use `scripts/taskw.py` for all repo-local operations.
- Use the current project's Python environment so `PyYAML` resolves consistently with the rest of the repo tooling.
- The wrapper imports `.taskwarrior/tasks.yaml` before each command, runs Taskwarrior against `.taskwarrior/data/`, then exports the full task set back to `.taskwarrior/tasks.yaml`.
- Taskwarrior itself still imports and exports JSON. The wrapper handles the JSON-to-YAML transcoding so the repo snapshot is easier to review in version control.
- The SQLite database remains persistent, so `undo`, contexts, custom reports, and other Taskwarrior state continue to work across invocations.
- Use `python3 scripts/taskw.py --rebuild ...` only when `.taskwarrior/data/` drifts from the YAML snapshot or after manual edits to `.taskwarrior/tasks.yaml`.
- Do not maintain `TODO.md` in parallel unless the repo explicitly requires it.
- Do not change `data.location` in repo-local mode. The wrapper owns it.

## Common Operations

Use the documented Taskwarrior command form:

```text
task [<filter>] <command> [<mods>]
```

Common repo-local examples:

```bash
python scripts/taskw.py add "Ship the release notes" project:Repo.Release priority:H +release due:friday
python scripts/taskw.py list
python scripts/taskw.py next
python scripts/taskw.py ready
python scripts/taskw.py overdue
python scripts/taskw.py waiting
python scripts/taskw.py 3 modify project:Repo.Backlog +triage scheduled:tomorrow
python scripts/taskw.py 3 annotate "Blocked on API schema review"
python scripts/taskw.py 3 start
python scripts/taskw.py 3 stop
python scripts/taskw.py 3 done
python scripts/taskw.py 3 delete
python scripts/taskw.py projects
python scripts/taskw.py tags
python scripts/taskw.py summary
python scripts/taskw.py information 3
python scripts/taskw.py export
```

Use `--` when the description contains text that looks like metadata:

```bash
python scripts/taskw.py add -- project:Home needs scheduling
```

## Reports And Ingestion

- For agent task inspection, default to `export` and ingest the JSON first.
- Treat JSON export as an internal query format, not the final user-facing output.
- If the user asks to "list tasks", "show current tasks", or otherwise inspect the current task set, use `python scripts/taskw.py export` as the primary query.
- Use `export <report>` for machine-readable subsets like `ready`, `next`, `overdue`, or `waiting`.
- Use formatted reports like `list`, `next`, `ready`, `waiting`, `overdue`, `summary`, `projects`, and `tags` only when a human-readable terminal view is the goal.
- Taskwarrior supports exporting report selections as JSON, so prefer `export <report>` over scraping tabular output.

Examples:

```bash
python scripts/taskw.py export
python scripts/taskw.py export ready
python scripts/taskw.py export next
python scripts/taskw.py project:Repo export overdue
python scripts/taskw.py +READY export
```

- The default `export` output is a JSON array.
- If line-delimited JSON is easier for downstream tooling, use `rc.json.array=0` explicitly:

```bash
python scripts/taskw.py rc.json.array=0 export ready
```

- Treat `.taskwarrior/tasks.yaml` as the versionable snapshot, not the primary query interface. For fresh machine-readable views, query Taskwarrior directly with `export`.
- After ingesting JSON, present a readable task summary to the user instead of dumping raw JSON or raw tabular reports unless they explicitly asked for them.
- Summarize tasks in plain language. Include the task ID and description, then only the most decision-relevant metadata such as priority, project, due date, scheduled date, waiting state, dependency/blocking state, and notable tags.
- Omit low-signal fields like UUID, entry timestamp, modified timestamp, and urgency unless the user asked for them.
- If there are many tasks, group or sort them into a concise summary such as ready tasks, waiting tasks, overdue tasks, or by project, then mention the count.
- Only show raw JSON or the exact terminal table when the user explicitly asks for raw output, debugging detail, or a verbatim dump.

## Model Tasks Well

- Use dotted project hierarchies for subprojects, for example `project:Repo`, `project:Repo.Backlog`, `project:Repo.Release`.
- Use tags for cross-cutting descriptors such as `+bug`, `+docs`, `+blocked`, `+frontend`.
- Use `priority:H`, `priority:M`, and `priority:L` sparingly. Treat them as a coarse ordering tool, not a substitute for regular review.
- Keep the task `description` short and stable. Treat it as the task title, not the full brief.
- Put longer task context into annotations.
- Prefer multiple focused annotations over one overloaded description.
- Use `due` only for actual deadlines. Use `scheduled` for the earliest sensible start date. Use `wait` to hide tasks until they become actionable.
- Use dependencies when sequence matters:

```bash
python scripts/taskw.py add "Implement API client" project:Repo.SDK
python scripts/taskw.py add "Wire client into CLI" project:Repo.SDK depends:1
python scripts/taskw.py blocked
python scripts/taskw.py blocking
python scripts/taskw.py unblocked
```

- Use annotations for durable notes instead of overloading the description.
- Use annotations for implementation notes, acceptance criteria, blockers, links, next steps, and decisions.
- When creating or triaging a task that needs substantial context, add the task first with a short title, then attach one or more annotations immediately.
- If the user asks what a task involves, inspect annotations before answering.
- Use `start` and `stop` to mark active work when you want the task list to reflect current focus.

Example:

```bash
python scripts/taskw.py add "Prototype report export workflow" project:Skill.Taskwarrior.Research priority:M +reports
python scripts/taskw.py 4 annotate "Goal: verify export <report> paths and summarize them clearly in the skill."
python scripts/taskw.py 4 annotate "Acceptance: document default current-task query, ready/next examples, and user-facing summary rules."
python scripts/taskw.py 4 annotate "Notes: prefer export for ingestion, then answer in readable prose rather than raw JSON."
```

## Contexts And Reports

- Use contexts when you need a persistent default filter.
- For simple contexts, `task context define home project:Home` is fine.
- For complex contexts, set read and write sides intentionally. Taskwarrior docs warn that a complex read filter does not map cleanly to write modifications.

Example:

```bash
python scripts/taskw.py context define home project:Home
python scripts/taskw.py context home
python scripts/taskw.py add "Replace kitchen light"
python scripts/taskw.py context none
```

If the context filter is complex, explicitly refine the write side:

```bash
python scripts/taskw.py context define family 'project:Family or +paul or +nancy'
python scripts/taskw.py config context.family.write project:Family
```

- Reach for built-in reports before inventing custom ones: `next`, `ready`, `waiting`, `overdue`, `projects`, `tags`, `summary`, `completed`, `active`, `recurring`.
- Use virtual tags like `+READY`, `+TODAY`, `+OVERDUE`, `+BLOCKED`, and `+WAITING` to simplify filters.

## Safety Rules

- Prefer ID or UUID filters for write operations.
- Avoid broad write filters unless the scope is intentional and reviewed.
- The wrapper disables interactive confirmations for automation, so be precise.
- Avoid empty-filter write commands.
- Prefer `project.is:Root` when you want only the root project; plain `project:Root` also matches hierarchical subprojects on Taskwarrior 3.1.0.
- Ignore `.taskwarrior/data/` in version control because it contains SQLite and other local artifacts.
- Prefer versioning `.taskwarrior/tasks.yaml` when the task list itself should be reviewable or shared.

## Reference

Read `references/taskwarrior-reference.md` when you need the fuller command inventory, date semantics, filter modifiers, workflow guidance, or the doc/help sources behind this skill.
