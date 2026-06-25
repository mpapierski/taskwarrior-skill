# Hooks, External Scripts, And Integration

Use this file for hook scripts, external tooling, app integration, JSON import/export format, and API-like usage.

## Hooks Overview

- Hooks are executable scripts run at specific Taskwarrior events.
- Hook scripts normally live under the active data directory's `hooks` subdirectory, commonly `~/.task/hooks`. If `hooks.location` is configured, use that path instead.
- A hook runs when its filename begins with a supported event name and is executable.
- Multiple hooks for the same event run in filename collation order.
- Disable a hook by removing execute permission, renaming it, moving it, or setting `rc.hooks=off`.

Events:

- `on-launch`: before processing; can stop launch.
- `on-exit`: after processing before output; can add footnotes/errors, not modify tasks.
- `on-add`: after a new task is processed but before save; can approve, reject, or modify it.
- `on-modify`: after a task modification is processed but before save; completion and deletion are modifications.

## Hook I/O

- Hook input and output use Taskwarrior JSON objects, one object per line.
- Successful hooks exit `0`.
- Failed hooks exit non-zero and should emit a clear error message.
- Malformed JSON is rejected.
- Correct JSON that is not a task is ignored.

Task exit code on hook abort:

- When any hook aborts an operation, the `task` process itself exits with code `4` (verified in 3.4.2) regardless of the hook's own exit code — a hook exiting `1` or `7` both yield task exit `4`. Compare: `0` on success, `1` for ordinary errors such as no-match.
- For explicit rejections Taskwarrior prints the hook's free-text feedback line; for protocol violations (wrong JSON count, changed UUID, malformed JSON) it prints a line prefixed `Hook Error:` naming the offending script.
- Non-interactively, exit code `4` plus a `Hook Error:`/feedback line reliably signals a hook-caused failure, distinct from generic exit `1`. This refines the "Check the process exit code first" guidance in `commands-and-syntax.md`.

Event input/output shape:

- `on-launch`: no input, no JSON output.
- `on-exit`: receives on stdin the JSON of the task(s) affected by the just-completed command (added/modified/completed task), one per line; pure read/report commands (`list`, `export`, etc.) feed zero lines. Must NOT emit any JSON task object on stdout — doing so aborts with `Hook Error: Expected 0 JSON task(s), found N`. It MAY print plain (non-JSON) feedback text, which is shown to the user; a non-zero exit reports an error but does not roll back the already-committed change.
- `on-add`: one task JSON object input. MUST write exactly one task-JSON line to stdout, and that line's `uuid` MUST equal the input task's uuid.
- `on-modify`: two input lines (original first, modified last). Echo back the LAST line, edited as needed, preserving its uuid. MUST write exactly one task-JSON line to stdout.

For `on-add`/`on-modify`, emitting zero lines, multiple lines, or a different uuid aborts the operation with exit code `4` and a `Hook Error:` message: `Expected 1 JSON task(s), found N` or `JSON must be for the same task: <orig> != <new>`.

## Hook Command-Line Arguments

Taskwarrior 3.4.2 passes these six positional arguments to EVERY hook for EVERY event (`on-launch`, `on-add`, `on-modify`, `on-exit`), unconditionally — there is no opt-in, no version declaration, and no `api:1` fallback. Rely on them always being present in this order:

- `api:2`
- `args:task <full argv>`
- `command:<command>`
- `rc:<absolute-taskrc-path>`
- `data:<absolute-data-path>`
- `version:<x.y.z>`

Use these to detect alternate rc/data paths and command context. Prefer reading the live `version:` argument over assuming an API level. (Older docs describe a future "v2" API negotiation; in 3.4.2 the contract is already fixed as above.)

## Hook Author Workflow

1. Decide whether the hook should validate, mutate, annotate, reject, or report.
2. Write the hook in any language with reliable stdin/stdout JSON handling.
3. Test the script independently with sample JSON.
4. Resolve the active hooks directory, install the hook there, and make it executable.
5. Run `task diagnostics` or an isolated equivalent to confirm discovery (see "Verifying hook discovery" below).
6. Debug with `rc.debug.hooks=1` or `rc.debug.hooks=2`. These work even though `debug.hooks` is absent from `task _config`/`show` — do not conclude it is unsupported just because `task _config | grep debug.hooks` returns nothing; see `taskrc(5)`.

Verifying hook discovery — read the `Hooks` block of `task diagnostics`:

```text
Hooks
     System: Enabled
   Location: <data.location>/hooks
     Active: on-add.good   (executable)
   Inactive: badname.sh    (executable)unrecognized hook name
             on-add.noexec (not executable)
```

- `System: Enabled`/`Disabled` reflects `rc.hooks` — if `Disabled`, NO hook runs regardless of the Active list, so check this first.
- `Location:` is the resolved hooks dir.
- `Active:` lists scripts that both begin with a valid event name and are executable (annotated `(executable)`).
- `Inactive:` lists non-runnable scripts with the reason inline — `(not executable)` means add the execute bit (`chmod +x`); `(executable)unrecognized hook name` means rename so the filename begins with `on-add`/`on-modify`/`on-launch`/`on-exit`.
- `(-none-)` means the directory has no hooks.

After installing a hook, confirm it appears under `Active` and that `System` is `Enabled`; if it is under `Inactive`, apply the annotated fix.

Safety:

- Treat hook installation like installing arbitrary software.
- Keep hooks fast; they run during task operations.
- Avoid network calls in hooks unless the user accepts latency and failure modes.
- Disable hooks for controlled imports/exports/upgrades when hook side effects are undesirable.

Resolve hook paths carefully:

```bash
task _get rc.data.location
```

Default to `<data.location>/hooks`. In 3.4.2, `hooks.location` (and other keys that have built-in defaults, e.g. `debug.hooks`, `debug.parser`) do NOT appear in `task _config`, `task show`, or `task _get` unless explicitly set, yet are still honored. So do not trust `show`/`_get` to learn the resolved hooks directory: prefer the `Hooks > Location` line of `task diagnostics`, rather than parsing taskrc and its includes by hand. Redact local paths if they are not necessary in the final answer.

## External Scripts And Third-Party Apps

- Prefer the native `task` CLI and JSON export/import.
- Use `task export` for read access and `task import` for structured writes.
- Avoid parsing human report tables in automation.
- Do not write directly to Taskwarrior's local database.
- Respect user configuration, contexts, hooks, and sync setup.
- Ask before changing persistent config, installing hooks, or adding sync/app credentials.

## JSON Import/Export

- `task export` emits task JSON.
- `task import <file>` imports JSON and updates existing tasks by UUID.
- Preserve UUIDs when exporting and importing tasks.
- Use `rc.json.array=0` for newline-delimited objects when easier for streaming.
- Use `rc.json.array=1` for JSON arrays when easier for parsers.
- The JSON task format is one task object per line when not wrapped as an array.
- Task JSON is UTF-8. Newline characters are not permitted inside task values.
- Blank values are omitted rather than emitted as empty name/value pairs.
- At minimum, a valid imported task needs `uuid`, `status`, `entry`, and `description`.
- Deleted and completed tasks also need `end` and `modified`.
- Waiting tasks need `wait`.
- Recurring templates need `status:recurring`, `recur`, and `due`; recurring instances need `parent`.
- Preserve unknown fields. They may be UDAs or fields from another client/version.

Common attributes in JSON:

- identity: `uuid`, local `id` in exports.
- lifecycle: `status`, `entry`, `modified`, `start`, `end`.
- content: `description`, `annotations`.
- organization: `project`, `tags`, `priority`.
- dates: `due`, `scheduled`, `wait`, `until`.
- recurrence: `recur`, `parent`, `mask`, `imask`.
- dependencies: `depends`.
- custom metadata: UDA fields.

Container shapes for `tags`, `annotations`, and `depends` (what to emit when building import JSON, and what to parse from hook stdin):

- `tags`: JSON array of single-word strings, e.g. `"tags":["home","garden"]`.
- `annotations`: JSON array of objects, each with `entry` (compact UTC date) and `description`, e.g. `"annotations":[{"entry":"20260617T162416Z","description":"text"}]`.
- `depends`: JSON array of lower-case UUID strings, e.g. `"depends":["<uuid>"]`.

Do not follow the JSON RFC type column (which labels these `String`/`String list`) literally. Verified 3.4.2 import failure modes:

- `"tags":"a,b"` (comma string) imports with NO error but SILENTLY DROPS the tags.
- `"annotations":"text"` HARD-ERRORS with `Annotations is malformed` (exit 2).
- `"depends":"uuid1,uuid2"` happens to be accepted, but `export` always normalizes it to an array.

Durable rule: mirror exactly what `task export` emits. Run an export first and copy the shape rather than trusting the RFC type column.

Dates in JSON use Taskwarrior's compact UTC format, for example `YYYYMMDDTHHMMSSZ`.
UUIDs are lower-case UUID strings and should not be changed once assigned.
Exported `id` and `urgency` are derived convenience values, not durable stored fields. Use UUIDs for durable external identity and recalculate/refresh urgency through Taskwarrior instead of preserving it as source data.

## Import/Export Cautions

- Import updates by UUID, so changing UUIDs creates different tasks.
- Recurring task imports may prompt unless `rc.recurrence.confirmation=no` is set.
- Hooks may run during imports; use `rc.hooks=off` only when a controlled import should bypass them.
- JSON format details can change; rely on Taskwarrior's own `export` and `import` rather than handcrafted assumptions when possible.

## Integration Checklist

- Identify active `TASKRC`, `TASKDATA`, and `data.location`.
- Identify the resolved hooks directory (the `Hooks > Location` line of `task diagnostics`; defaults to `<data.location>/hooks`) before installing hook scripts.
- Read with `task export`, not database files.
- Write with `task add`, `task modify`, or `task import`.
- Use UUIDs for external references.
- Respect contexts or explicitly clear/override them if the user asks for global scope.
- Consider hooks and sync side effects.
- Summarize changes clearly for the user.
