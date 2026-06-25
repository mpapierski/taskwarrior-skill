# Configuration, Storage, Upgrade, And Sync

Use this file before changing Taskwarrior config, database paths, storage, colors, verbosity, upgrades, imports from v2, or sync.

## Configuration Model

For detailed taskrc syntax and the full config variable family map, read `taskrc-configuration.md`.

- Taskwarrior reads a taskrc file, commonly `~/.taskrc`.
- If `~/.taskrc` is absent, Taskwarrior can use `$XDG_CONFIG_HOME/task/taskrc`.
- Non-interactively, Taskwarrior never auto-creates a taskrc: with no readable rc file it aborts with `Cannot proceed without rc file.` (exit 2). Verified for missing `~/.taskrc`, `TASKRC=/nonexistent`, and `rc:/nonexistent`. The first-run "create sample taskrc" prompt fires only on a real TTY; piping `yes` or setting `rc.confirmation=off` does not bootstrap it.
- To target a fresh rc path for an agent, create the file first (`touch /new/taskrc`) or point `TASKRC`/`rc:` at `/dev/null` — an empty or already-existing file is enough.
- Config entries are `name=value`.
- `task config <name> <value>` persists a value.
- `task show [name]` displays config.
- Command-line overrides such as `rc.verbose=0` are temporary.
- Colon-style overrides such as `rc.verbose:0` are also supported.
- `include <file>` in taskrc can split config into multiple files.

Examples:

```bash
task show data.location
task show report.next
task rc.confirmation=off config default.command next
task rc.verbose=0 list
```

Do not persist config changes unless the user explicitly asks for them. Do not paste raw `task show`, `task _show`, or diagnostics output into a response; redact secrets, credential paths, server URLs, client IDs, and unrelated local paths.

## Environment And Path Overrides

- `TASKRC=/path/to/taskrc task ...`: use another taskrc.
- `TASKDATA=/path/to/data task ...`: use another data directory.
- `XDG_CONFIG_HOME=/path task ...`: affects the taskrc fallback path when `~/.taskrc` is absent.
- `task rc:/path/to/taskrc ...`: CLI taskrc override.
- `task rc.data.location=/path/to/data ...`: CLI data directory override.
- `task rc.data.location:/path/to/data ...`: colon-style CLI override.
- `task rc.confirmation=off config data.location /path/to/data`: persistent data path change.

Each override needs a usable rc file behind it. `TASKRC=/new/taskrc` and `rc:/new/taskrc` both abort (`Cannot proceed without rc file.`, exit 2) if that path does not exist — pre-create it with `touch`, or use `rc:/dev/null` for a throwaway/probe run. For the general non-interactive prompt/exit-code rules, see `agent-runtime-safety.md`.

Use environment/taskrc inspection first when the database is unhealthy. On Taskwarrior 3.4.2, even metadata commands may try to open or update the configured database.

Safe isolated probe:

```bash
mkdir -p /tmp/task-probe
task rc:/dev/null rc.data.location=/tmp/task-probe _get rc.data.location
task rc:/dev/null rc.data.location=/tmp/task-probe diagnostics
```

## Storage Safety

- Taskwarrior 3 uses a TaskChampion-backed local database, commonly `taskchampion.sqlite3` under `data.location`.
- That single file is the whole store: all tasks, the working set, and the undo/operations log live inside it. There is no separate `pending.data`/`completed.data`/`undo.data` in v3 (those are legacy 2.x artifacts; see the Upgrade section). `task undo` reads the operations log from the same DB.
- The DB runs in SQLite WAL mode, so `taskchampion.sqlite3-wal` and `taskchampion.sqlite3-shm` sidecars exist while a `task` process is running and disappear (checkpoint) once it exits. A file-level copy taken while `task` is running, or one grabbing only the `.sqlite3` file, can miss uncommitted WAL data — another reason to use export/import below, not raw copies.
- Every command needs read+write access to BOTH `data.location` and `taskchampion.sqlite3`, including pure reads (`list`, `export`, `count`): each run sets WAL journal mode and rebuilds the working set. There is no fully read-only reporting mode. A read-only dir fails `Setting journal_mode=WAL: ... SQLITE_READONLY_DIRECTORY` (code 1544); a read-only file with a writable dir fails `Clear working set query: ... readonly database` (code 8) — both exit 2. The fix is to make dir+file writable, not to retry. Sole mitigation: when only the file (not the dir) is read-only, `task rc.gc=0 ... export` skips the working-set rebuild and succeeds (exit 0).
- Do not edit SQLite data directly.
- Do not copy database files between machines as a sync strategy.
- Do not use file sync tools such as rsync/Syncthing for live Taskwarrior 3 data; use Taskwarrior sync.
- Prefer `task export` and `task import` for portable task data.
- Ask before changing `data.location`, running imports, or moving/copying task stores.

Approved data move pattern:

```bash
mkdir -p /new/data && touch /new/taskrc   # import aborts (exit 2) if the rc file is missing
task export > tasks.json
TASKRC=/new/taskrc TASKDATA=/new/data task import tasks.json
TASKRC=/new/taskrc TASKDATA=/new/data task count
```

- `task import` keys on `uuid` and reports one line per task: `add` (new uuid), `mod` (existing uuid, fields changed), `skip` (existing uuid, identical). Re-running the same import is therefore idempotent — it never duplicates — and an agent can parse these tokens to report what happened.
- `task export` with no filter includes deleted (`status:deleted`) and completed tasks, so a full export/import carries deletion and completion history. Pass a filter such as `status:pending or status:waiting` if that is unwanted.

Verify counts and representative tasks before old data is considered disposable.

## Taskwarrior 3 Upgrade

- Taskwarrior 3 changed task storage and sync internals.
- Upgrade old 2.x task data with `task import-v2`.
- `import-v2` takes NO file argument and reads NO stdin (unlike `import [<file>]`, which it is easily confused with). It scans the configured `data.location` (`TASKDATA` / `rc.data.location`) for legacy v2 `*.data` files (`pending.data`, `completed.data`, etc.) and imports them into `taskchampion.sqlite3` in that same directory. To migrate, point `data.location` at the directory holding the old v2 files. An empty or wrong directory still succeeds: `Imported 0 tasks from \`*.data\` files.` exit 0 — verify the imported count, not just the exit code.
- Disable hooks during upgrade import unless the user specifically wants them:

```bash
task import-v2 rc.hooks=0
```

- Taskwarrior 3 sync does not interface with the old `taskd` protocol.
- After import, old 2.x `*.data` files are no longer used and are left in place. Back them up or remove them only with user approval. While they remain, the standard task-list reports (`list`, `next`, `all`, `ready`, `overdue`, etc.) print a `Found existing '*.data' files ... Run \`task import-v2\`` notice on STDERR with exit 0 — treat it as informational, not a failure. It is not a verbose token, so `rc.verbose=nothing`/`rc.verbose=0` do not suppress it. `info`/`information`, `summary`, `projects`, `tags`, `export`, `count`, `stats`, `ids`, and `uuids` do not emit it, so their stdout (e.g. `task export` JSON) stays clean. The only real fix is `task import-v2` then removing the files.

## Sync

For backend-specific settings and replica setup, read `sync-configuration.md`.

- Taskwarrior sync exchanges changes between replicas.
- It takes one sync on the source to upload and another sync on the destination to download.
- Taskwarrior 3 sync is implemented through TaskChampion.
- Supported backends include TaskChampion sync server and supported cloud/object storage backends.
- Treat older workflow examples that mention git, rsync, Syncthing, Dropbox, or Taskserver-era file sharing as historical unless the current Taskwarrior 3 sync docs explicitly support that setup.
- Use `task sync` / `task synchronize` only when sync is configured and the user expects it.
- Do not configure sync credentials or remotes without explicit approval.
- Inspect sync config with targeted settings, not raw `task show sync`, when output may be reported to the user.

Example flow:

```bash
task add "Finish odd exercises" +homework
task sync
```

Then on another replica:

```bash
task sync
task +homework list
```

## Sync Configuration Areas

Consult `task-sync(5)` before editing sync config. Common areas include:

- sync server URL and credentials.
- local replica configuration.
- cloud storage provider configuration.
- TaskChampion sync server setup.
- recurring-task duplication cautions.

## Verbosity

- Verbosity controls which messages Taskwarrior emits.
- Use temporary `rc.verbose=...` overrides for automation when possible.
- Avoid suppressing output during troubleshooting.

Example:

```bash
task rc.verbose=0 export
```

## Release News Reminder

If Taskwarrior prints `Recently upgraded to <version>. Please run 'task news'...`, the intended fix is to run `task news` once. This records `news.version=<version>` in taskrc.

For one-off automation where the reminder would pollute output, use a temporary verbosity override such as `rc.verbose=0` or `rc.verbose=nothing`. Do not persistently set `news.version` unless the user explicitly wants to mark release notes as read.

## Colors And Themes

For color syntax, rule precedence, and theme includes, read `color-themes.md`.

- `task colors` shows color samples and rules.
- Taskwarrior can automatically disable color in non-color terminals.
- Color rules and theme files are taskrc settings.
- Prefer not changing color/theme config unless the user asks for UI output changes.

## Contexts In Config

- Context definitions persist in config as read/write filters.
- The active context name persists in the `context` config value.
- Context data is stored as `context.<name>.read` and `context.<name>.write`.
- Per-context config overrides can be stored as `context.<name>.rc.<parameter>`.
- Simple contexts may define read and write sides automatically.
- Complex contexts should set write modifications explicitly.
- Contexts affect report commands that filter the task list, plus these named commands: `add`, `burndown`, `count`, `delete`, `denotate`, `done`, `duplicate`, `edit`, `history`, `log`, `prepend`, `projects`, `purge`, `start`, `stats`, `stop`, `summary`, and `tags`.
- Do not assume miscellaneous/helper commands inherit context; pass explicit filters when context should not be assumed.

```bash
task context define family 'project:Family or +paul or +nancy'
task rc.confirmation=off config context.family.write project:Family
task rc.confirmation=off config context.family.rc.default.command ready
```

## Automation Runtime Settings

Per-command override quick reference (for why these are mandatory non-interactively and the exit-code caveats, see `agent-runtime-safety.md`):

```bash
task rc.confirmation=off rc.bulk=0 rc.allow.empty.filter=0 12 delete
task rc.hooks=off export
task rc.recurrence.confirmation=no import tasks.json
```

- `confirmation=off`: avoid interactive confirmations.
- `bulk=0`: avoid bulk prompts (the bulk prompt ignores `confirmation`, so set both).
- `allow.empty.filter=0`: reject empty-filter writes.
- `hooks=off`: avoid hook side effects during controlled automation.
- `recurrence.confirmation=no`: avoid recurring-task prompts during import.

## Sensitive Config Redaction

Treat these config families as sensitive in logs and summaries:

```text
sync.encryption_secret
sync.aws.access_key_id
sync.aws.secret_access_key
sync.aws.profile
sync.aws.credential*
sync.gcp.credential_path
sync.server.url
sync.server.client_id
data.location
hooks.location
```

Use targeted commands and summarize findings without exposing values:

```bash
task show default.command
task show report.next
task show context
task show sync.server.url
```
