# Write Commands

Use this file for Taskwarrior writes: add, log, modify, annotate, denotate, append/prepend, start/stop, done, delete, purge, duplicate, import, and undo. For broad runtime hazards, read `agent-runtime-safety.md` first.

## Table Of Contents

- Command catalog
- Narrow targets
- Output and identity
- Description parsing
- Substitutions
- Import
- Purge

## Command Catalog

- `add <description> [mods]`: create a pending task.
- `log <description> [mods]`: create an already completed task.
- `modify <mods>`: modify matched tasks.
- `done`: complete matched tasks.
- `delete`: mark matched tasks deleted.
- `purge`: permanently remove matched already-deleted tasks. Local-only, not synced, non-revertible.
- `annotate <text>`: add an annotation.
- `denotate <pattern>`: remove an annotation. Exact match removes that annotation; partial match removes the first partial match.
- `append` / `prepend`: edit description text.
- `duplicate`: clone matched tasks.
- `start` / `stop`: add or remove active work state.
- `undo`: revert the most recent action when undo data is available.
- `import [<file> ...]`: import Taskwarrior JSON from files or stdin. Existing tasks are matched by UUID.
- `import-v2`: import old Taskwarrior 2.x data into Taskwarrior 3.x.

Do not use `edit` non-interactively; it launches an editor. Use commands above or a full export-edit-import round trip.

## Narrow Targets

Use ID or UUID filters for writes. Count or export broad targets first.

```bash
task 12 modify priority:H
task 12 annotate "Acceptance: export +READY tasks as JSON."
task 12 done
task 1 2 3 modify +review
task 1-3 information
task 1,4-10,19 delete
```

For writes that may touch three or more tasks, use both prompt overrides:

```bash
task rc.confirmation=off rc.bulk=0 1-5 modify +review
```

## Output And Identity

Taskwarrior write output is human-facing, not a structured API. Prefer `rc.verbose=new-uuid` for new task identity:

```bash
task rc.verbose=new-uuid add "Draft release notes" project:Repo.Release +docs
task rc.verbose=new-uuid log "Submitted quarterly report" project:Finance
```

`rc.verbose=0` reports a working-set ID, not a durable UUID. Store UUIDs for long-lived references.

Common outputs:

- `Created task N.` after `add`.
- `Logged task <UUID>.` only when using `rc.verbose=new-uuid`.
- `Modified 1 task.`, `Annotated 1 task.`, `Started 1 task.`, `Stopped 1 task.`
- `Completed task N 'Description'.` and `Completed 1 task.` after `done`.
- `Modified 0 tasks.` or `Completed 0 tasks.` can exit 0; parse the affected count and verify state.

## Description Parsing

Taskwarrior treats unrecognized bare words as description text. Attribute-like tokens are position-sensitive.

- A mid-string attr-like token in one quoted argument stays literal: `task add "review project:Foo notes"`.
- A leading `key:value` or `+tag` token can be consumed as metadata and leave no description.
- Separate args extract metadata and can mangle connector words: `task add fix the +bug in project:Foo` stores `fix the in`.
- Unknown attribute keys are silently treated as description text and can replace a description on `modify`.

Use `--` when description text starts with metadata-like content:

```bash
task add -- project:Home needs scheduling
task add -- +bug is part of the title
```

Write commands take text as command-line arguments, not stdin. Only `import` reads stdin.

## Substitutions

Description substitutions are writes; quote them and use narrow filters.

```bash
task 12 modify "/draft/final/"
task project:Docs modify "/old phrase/new phrase/g"
```

## Import

`task import` replaces the whole task object for matching UUIDs; it does not merge partial objects. Preserve all fields when editing JSON.

```bash
task <uuid> export > task.json
task import task.json
task import -
```

Import output uses `add`, `mod`, or `skip` lines per task even under `rc.verbose=nothing`; parse those tokens when reporting batch results.

## Purge

Capture the UUID before `delete` if a later `purge` is intended. After deletion, local working-set IDs can be reassigned, so `task <former-id> purge` is unreliable.

```bash
uuid=$(task _get 12.uuid)
task rc.confirmation=off 12 delete
task rc.confirmation=off "$uuid" purge
```
