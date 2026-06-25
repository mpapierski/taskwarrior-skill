# Troubleshooting, Deprecated Behavior, And Source Map

Use this file for failures, ambiguous behavior, deprecated features, support paths, and source coverage.

## Troubleshooting Flow

1. Capture the exact command and output.
2. Identify whether the command is read-only, write, config, import/export, sync, or hook-related.
3. Check `TASKRC`, `TASKDATA`, and taskrc path assumptions.
4. If the live database errors, stop before writes and use an isolated probe.
5. Use `task diagnostics` only when it is safe to touch the configured database.
6. Inspect hooks if task behavior changes unexpectedly.
7. Inspect contexts if reports or adds are unexpectedly scoped.
8. Use `task export` for machine-readable state.

Isolated probe:

```bash
mkdir -p /tmp/task-probe
task rc:/dev/null rc.data.location=/tmp/task-probe diagnostics
```

## Error Signatures (Verified 3.4.2)

Branch on the message and exit code, never on "nonzero" alone. Exit codes: `0` = success; `2` = hard error (DB/permission/sync/invalid expression or DOM reference); `4` = hook failure; `1` is ambiguous — it is also returned for empty-result reads and declined/no-match writes, not only for failures (see agent-runtime-safety.md).

| Signature (stderr) | Exit | Cause | Fix / agent action |
| --- | --- | --- | --- |
| `... file is not a database: Error code 26 ...` | 2 | Corrupt or non-DB file at `taskchampion.sqlite3`. | Do not retry. Surface to user. Do not hand-edit the SQLite file. |
| `attempt to write a readonly database ... Error code 1544: SQLITE_READONLY_DIRECTORY` (or `unable to open database file ... Error code 14`) | 2 | `data.location` dir not writable; WAL needs write even for reads. | Fix dir permissions/ownership. Do not retry. |
| `Hook Error: Expected feedback from failing hook script: <name>` | 4 | A hook rejected/failed the action. | Inspect the hook; re-run the diagnostic read with `rc.hooks=0` to isolate. |
| `No sync.* settings are configured. See task-sync(5).` | 2 | `task sync` invoked with no sync config. | Configure sync (see `config-storage-sync.md`) before retrying. |
| `Mismatched parentheses in expression` (and similar) | 2 | Malformed filter expression. | Fix quoting/grouping; do not retry unchanged. |
| `No matches.` | 1 | Empty-result read, no-match write, or an unknown/removed command parsed as a filter term. | Not retryable as-is. Distinguish empty result from bad command (see below). |

A malformed USER taskrc (e.g. an invalid UDA type) makes even read-only commands fail: a stray `uda.foo.type=<bogus>` yields `User defined attributes may only be of type 'string', 'uuid', 'date', 'duration' or 'numeric'.` and exit 2 on a plain `list`. Suspect taskrc content first; re-run with `rc:/dev/null rc.data.location=<tmp>` to confirm (a `rc.data.location` override alone still loads `~/.taskrc`). See agent-runtime-safety.md.

## Common Pitfalls

- Broad write filters affect more tasks than intended. Run `count` or `export` first.
- Local IDs change; use UUIDs outside the current working set.
- Report filters combine with command-line filters. Quote grouped `or` expressions.
- Shell parsing eats parentheses, spaces, `!`, `*`, `$`, and other metacharacters unless quoted.
- `wait` hides tasks from normal reports.
- Contexts can change both reads and writes.
- Hooks can modify, reject, or annotate tasks.
- If every command prints a recently-upgraded reminder, run `task news`; for noninteractive commands use a temporary `rc.verbose=0` override.
- Taskwarrior 3 data should not be synchronized by file-copy tools.
- Persistent red `Found existing '*.data' files ... storage format changed in 3.0 ... Run `task import-v2`` on every run = leftover Taskwarrior 2.x files in `data.location`. Fix per `config-storage-sync.md` "Taskwarrior 3 Upgrade": run `task import-v2 rc.hooks=0`, verify counts, then back up/remove old `*.data` only with user approval.
- `purge` permanently removes data.
- `task show`, `task _show`, `task diagnostics`, and sync config can expose secrets or local paths. Redact credentials, server URLs, client IDs, credential paths, and unrelated local paths before reporting output. In `task diagnostics` the concrete path-disclosure lines are `File:`, `Data:`, and the Hooks `Location:`.

## Deprecated Or Removed Behavior

- Old push/pull/merge sync behavior is gone. `merge`/`push`/`pull` are absent from `task _commands`; the only sync entry point is `task sync` (alias `synchronize`).
- `task push|pull|merge` does NOT error as an unknown command — the word is parsed as a search/filter term, prints `No matches.` and exits 1 (easily misread as a transient failure to retry); if a task description contains that word it can even exit 0 and list tasks, falsely appearing to succeed while syncing nothing. Never invoke them; treat any nonzero result as "command does not exist", not retryable.
- Shadow files are removed; do not rebuild a shadow-file workflow.
- Bare word search terms and old helpers such as `_ids`, `_uuids`, `_projects`, and `_tags` are deprecated patterns; prefer explicit filters and `_unique`.
- `DUETODAY` virtual tag is deprecated; use modern date filters or virtual tags.
- Deprecated DOM context references should not be used for new guidance.
- Taskwarrior 3 no longer uses old Taskwarrior 2 storage/sync assumptions.

## Bug And Feature Requests

- File bugs and feature requests at https://github.com/GothenburgBitFactory/taskwarrior/issues. Code repo: https://github.com/GothenburgBitFactory/taskwarrior. Support: support@GothenburgBitFactory.org. The current org is `GothenburgBitFactory`, not the legacy `taskwarrior` GitHub org — do not route users to a stale tracker.
- Use `task diagnostics` output when reporting bugs if safe to run.
- `task diagnostics` includes a data-integrity scan, reported under `Tests` as `Broken ref: Scanned N tasks for broken references` (broken references are dependencies pointing at missing/purged tasks); `No broken references found` is the healthy state. This contradicts the manpage's stale "duplicate UUIDs" wording — do not tell a user the scan checks for duplicate UUIDs.
- Reduce reports to a minimal reproduction.
- Include Taskwarrior version, platform, configuration relevant to the issue, and exact commands.
- For feature requests, describe the workflow problem first, then the proposed behavior.

## Local Version Notes

- Local CLI checked during this skill update: Taskwarrior `3.4.2`.
- Local `task diagnostics` against the user's configured database reported a read-only WAL/database error, so this skill avoids presenting live metadata commands as always harmless.
- Isolated `rc:/dev/null rc.data.location=/tmp/...` probes worked for command/report/path inspection.

## Official Source Map

The skill condenses the official documentation index into focused reference files. For an explicit coverage checklist, read `source-coverage.md`.

- Getting started: `start`, `introduction`, `30second`, `help`, `best-practices`, `examples`, `workflow`, `philosophy`, `review`.
- Command mechanics: `syntax`, `commands`, `escapes`, `unicode`, `dom`, `man/task.1`.
- Filters and reports: `searching`, `filter`, `report`, `tags`, `priority`, `man/task.1`.
- Task modeling: `using_dates`, `dates`, `named_dates`, `durations`, `recurrence`, `ids`, `urgency`, `udas`, `task`, TaskChampion representation, JSON task RFC.
- Contexts: `context`, `task(1)` context subcommands, `taskrc(5)` context settings.
- Configuration and storage: `configuration`, `verbosity`, `themes`, `terminology`, `upgrade-3`, `sync`, `man/taskrc.5`, `man/task-sync.5`, `man/task-color.5`.
- Integration: `hooks`, `hooks2`, `hooks_guide`, `3rd-party`, `tools`, JSON task RFC.
- Support/about: `bugs`, `features`, `deprecated`, `history`, `license`.

Primary URLs:

- https://taskwarrior.org/docs/
- https://taskwarrior.org/docs/syntax/
- https://taskwarrior.org/docs/filter/
- https://taskwarrior.org/docs/report/
- https://taskwarrior.org/docs/using_dates/
- https://taskwarrior.org/docs/man/task.1/
- https://taskwarrior.org/docs/man/taskrc.5/
- https://taskwarrior.org/docs/man/task-sync.5/
- https://taskwarrior.org/docs/sync/
- https://taskwarrior.org/docs/task/
- https://taskwarrior.org/docs/man/task-color.5/
- https://taskwarrior.org/docs/hooks/
- https://taskwarrior.org/docs/hooks2/
- https://taskwarrior.org/docs/hooks_guide/
- https://taskwarrior.org/docs/udas/
- https://taskwarrior.org/docs/dom/
- https://github.com/GothenburgBitFactory/taskwarrior
