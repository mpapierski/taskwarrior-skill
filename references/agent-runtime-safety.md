# Agent Runtime Safety

Use this file before deletes, bulk writes, config writes, imports, sync, hooks, recovery, alternate taskrc/data paths, or any task where a silent no-op would be harmful.

## Non-Interactive Rules

Codex runs `task` with non-interactive stdin. Prompts usually read EOF as "no", so a command may print a reassuring message, exit 0 or 1, and change nothing.

- `delete` and `purge` prompt. Use `rc.confirmation=off` when the user intends the action.
- Writes touching `rc.bulk` or more tasks (default `3`) trigger a bulk prompt that ignores `confirmation`. Use both `rc.confirmation=off rc.bulk=0`.
- Empty-filter writes prompt by default. Use `rc.allow.empty.filter=0` in automation to make them hard errors.
- `task config` prompts for every write and persists to the selected taskrc, not to `data.location`.
- `task edit` launches an editor and can hang the agent. Do not use it non-interactively.

```bash
task rc.confirmation=off 4 delete
task rc.confirmation=off rc.bulk=0 1-5 done
task rc.confirmation=off config default.command next
task rc.confirmation=off rc.bulk=0 rc.allow.empty.filter=0 12 modify +review
```

## Verification

Never trust exit code alone to prove a write applied.

- A declined `purge` can exit 0 while purging nothing.
- A no-match human report can exit 1 even though nothing failed.
- `count` and `export` are better state checks: `count` prints `0`, `export` emits `[]`.
- Some no-op writes return exit 0 with `Modified 0 tasks.` or `Completed 0 tasks.`.

After important writes, verify with:

```bash
task <id-or-uuid> export
task <id-or-uuid> information
task <filter> count
```

## Dangerous Write Shapes

- Do not let user-supplied or templated `status:` tokens reach `modify`. `task <id> modify status:deleted` bypasses `delete` confirmation, and `status:completed` bypasses `done`.
- Unknown attribute keys are treated as description text. A typo such as `priorty:H` can silently become part of the description; on `modify`, it can replace the description. Use known attributes and verify parsed state after attribute writes.
- `import` replaces whole tasks by UUID. A partial object such as `{uuid, priority}` wipes omitted fields. To change one field, round-trip the full exported task.

```bash
task <uuid> export > task.json
# edit the full object, preserving existing fields
task import task.json
```

## Config And Path Safety

- `rc.data.location` changes the database path only. It does not sandbox `task config`; config writes still update the selected taskrc.
- To isolate config writes, use a separate taskrc path with `rc:<file>` or `TASKRC=<file>`, and ensure that file already exists.
- Non-interactively, Taskwarrior does not create a missing taskrc. A missing `TASKRC` or `rc:` path fails with `Cannot proceed without rc file.`.

```bash
touch /tmp/taskrc
task rc:/tmp/taskrc rc.data.location=/tmp/taskdata rc.confirmation=off config default.command next
```

## Recovery

Use undo only when the most recent operation is the one to revert and undo data is available. Synced operations may no longer be undoable.

```bash
task rc.confirmation=off undo
```

If undo is unavailable, inspect the task with `information`/`export` and repair with explicit `modify`, usually by UUID.
