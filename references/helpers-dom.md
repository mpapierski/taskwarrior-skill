# Helpers And DOM Access

Use this file for Taskwarrior helper commands, DOM lookups, metadata access, and low-level read helpers. Treat `_show` and diagnostics as sensitive.

## DOM References

DOM references expose system, config, and task fields:

- `system.version`, `system.os`
- `tw.program`, `tw.args`, `tw.width`, `tw.height`, `tw.version`, `tw.syncneeded`
- `rc.<name>`
- `<attribute>`
- `<id>.<attribute>`
- `<uuid>.<attribute>`

Examples:

```bash
task _get system.version
task _get rc.data.location
task _get tw.version
task _get 12.description
task _get 12.due.year
```

`_get` takes DOM references directly. On Taskwarrior 3.4.2, adding `--` can make a valid `rc.<name>` reference fail; use bare references.

Missing values can produce empty output with exit 0. Malformed references exit 2. Confirm task identity with `task <id-or-uuid> export` when stale IDs matter.

## Helper Commands

Prefer current helpers:

```bash
task _columns
task _commands
task _config
task _show
task _udas
task _unique project
task _unique tags
task +READY _unique uuid
task 12 _urgency
task _version
```

Deprecated helpers such as `_ids`, `_uuids`, `_projects`, and `_tags` may still work, but `man task` directs users to `_unique` instead.

`ids` collapses contiguous IDs into ranges (`1-6`). If a script needs plain durable values, prefer `uuids`, `_unique uuid`, or JSON export.

## Sensitive Output

Treat these commands as potentially sensitive:

```bash
task show
task show sync
task _show
task diagnostics
```

They may reveal sync secrets, cloud credentials, credential paths, server URLs, client IDs, data paths, hook paths, or local usernames. Query only the needed setting and redact sensitive values before reporting output.

Some helper commands and diagnostics can still open the configured database. Use isolated `rc:/dev/null rc.data.location=/tmp/...` probes when the user's database is unhealthy.
