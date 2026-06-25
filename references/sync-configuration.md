# Sync Configuration

Use this file for Taskwarrior 3 sync setup, `task-sync(5)`, sync backends, encryption, replica setup, TaskChampion sync server behavior, local sync, and recurring-task sync cautions. Use `config-storage-sync.md` first when the question is about database path safety, storage movement, or whether sync should be run at all.

## Core Model

- Sync exchanges changes between replicas. A replica is a configured Taskwarrior data store on a machine or app.
- A change usually needs two `task sync` calls to appear elsewhere: one on the source replica to upload, one on the destination replica to download.
- Sync has a side effect: once changes have synchronized, previous operations may no longer be undoable.
- Taskwarrior 3 sync is implemented through TaskChampion.
- Do not use file synchronization tools such as rsync, Syncthing, Dropbox, or generic file sharing against the live Taskwarrior 3 database. Taskwarrior data is not a mergeable flat-file store.
- Do not configure sync credentials, buckets, servers, or replica identity without explicit user approval.

## Writing `sync.*` Config Non-Interactively

Every `task config sync.<key> <value>` example below would prompt `(yes/no)` without `rc.confirmation=off` and, under non-interactive stdin, answer "no", make NO change, and STILL exit 0. See `agent-runtime-safety.md`. For agents:

```bash
task rc.confirmation=off config sync.<key> <value>
task _config | grep sync.<key>                        # VERIFY the write; do not trust exit 0
```

- These writes PERSIST to the taskrc file (default `~/.taskrc`; selected by the `TASKRC` env var or `task rc:<file>`). `rc.data.location` redirects only the database, not the taskrc, so it does NOT sandbox these writes.
- To set sync values without touching the user's real config, either (a) use a throwaway taskrc: `TASKRC=/tmp/rc task rc.data.location=/tmp/data rc.confirmation=off config sync...`, or (b) pass one-shot non-persistent overrides: `task rc.sync.<key>=<value> sync`.
- Get explicit user approval before persisting any `sync.*` key.

## Adding A Replica

- Configure a new empty replica identically to an existing one, then run `task sync`.
- Use the same sync backend settings and the same `sync.encryption_secret` for replicas that share tasks.
- Keep `data.location` separate per replica. Do not copy live database files as the setup path.
- After setup, verify with `task sync`, then inspect expected tasks with `task export` or a report.
- `task sync` also accepts an optional `initialize` keyword (`task sync init` / `task sync initialize`). It is NOT needed for normal first-run setup — a fresh empty replica pulls everything with plain `task sync`. Treat `initialize` only as a rarely-needed full re-sync/replay path; with no backend configured it still exits 2 with `No sync.* settings are configured.` just like plain `sync`.

## Encryption

- Most sync backends require `sync.encryption_secret`. A fresh install leaves it unset; there is no default.
- The secret encrypts/decrypts task data and must match on all replicas sharing the same task set.
- Treat it like a credential. Do not print it in final answers or commit it into a repo.
- Generate it from a strong random source. `task-sync(5)` suggests `pwgen(1)`; non-interactively, `openssl rand -base64 32` produces a suitable value.
- Mismatch failure mode (server/cloud backends): a replica whose secret differs from its peers' cannot decrypt their data, so it syncs as a separate, empty task set rather than erroring. Suspect this when sync "succeeds" (exit 0) but expected tasks do not appear. Local sync (`sync.local.server_dir`) does NOT enforce the secret — a mismatched or absent secret still reads peers' data, so do not blame a secret mismatch when diagnosing missing tasks after a local sync.

```bash
task rc.confirmation=off config sync.encryption_secret "$(openssl rand -base64 32)"
```

## TaskChampion Sync Server

- Configure server URL and client ID:

```bash
task rc.confirmation=off config sync.server.url <url>
task rc.confirmation=off config sync.server.client_id <client_id>
```

- The URL must include a scheme such as `http://` or `https://`.
- `sync.server.origin` is deprecated; use `sync.server.url`.
- TaskChampion sync server identifies users by client ID. Different client IDs are independent.
- Task data is encrypted by Taskwarrior; the sync server should not see unencrypted task data.
- A new client ID can be a UUID. The sync server can create a user when a new client ID appears.

## Google Cloud Storage

- Basic GCP config:

```bash
task rc.confirmation=off config sync.gcp.bucket <bucket-name>
```

- If using a service account key instead of application-default credentials:

```bash
task rc.confirmation=off config sync.gcp.bucket <bucket-name>
task rc.confirmation=off config sync.gcp.credential_path <absolute-path-to-json-credentials>
```

- The bucket and credential setup happens outside Taskwarrior. Agents should not create cloud resources or store credential paths without user approval.

## AWS S3

Taskwarrior supports several AWS credential paths.

Direct keys:

```bash
task rc.confirmation=off config sync.aws.region <region>
task rc.confirmation=off config sync.aws.bucket <bucket-name>
task rc.confirmation=off config sync.aws.access_key_id <access-key-id>
task rc.confirmation=off config sync.aws.secret_access_key <secret-access-key>
```

AWS profile:

```bash
task rc.confirmation=off config sync.aws.region <region>
task rc.confirmation=off config sync.aws.bucket <bucket-name>
task rc.confirmation=off config sync.aws.profile <profile-name>
```

Default AWS credential sources:

```bash
task rc.confirmation=off config sync.aws.region <region>
task rc.confirmation=off config sync.aws.bucket <bucket-name>
task rc.confirmation=off config sync.aws.default_credentials true
```

- The bucket should not have lifecycle policies that delete or transition Taskwarrior sync objects unexpectedly.
- The IAM principal needs object create/read/list/delete permissions for the bucket used by sync.
- Prefer profile/default-credential approaches over embedding secret keys in taskrc when possible.

## S3-Compatible Object Storage

- Upstream sync docs note that some S3-compatible storage services are supported.
- Do not assume every S3-compatible provider works with the AWS settings. Check the local `task-sync(5)` manpage and the provider's current TaskChampion/Taskwarrior guidance before configuring endpoints, regions, credentials, or bucket behavior.
- Treat non-AWS object storage as credentialed sync setup: get explicit user approval before persisting settings, and redact endpoints, access keys, and bucket names in summaries unless the user asks to see them.

## Local Sync

- Local sync stores sync data on disk rather than on a network server.
- It can save local database space but is not a multi-user merge strategy by itself.

```bash
task rc.confirmation=off config sync.local.server_dir /path/to/sync
```

- Use a normal local directory, not a live shared database copy.
- `server_dir` must already exist before `task sync` — Taskwarrior does NOT create it (not even one missing level under an existing parent). Run `mkdir -p <server_dir>` before the first sync. On first sync it writes `taskchampion-local-sync-server.sqlite3` into that dir.
- A missing/uncreatable dir fails with `unable to open database file: .../taskchampion-local-sync-server.sqlite3: Error code 14: Unable to open the database file` and exit 2.

## Recurring Tasks Across Replicas

To avoid duplicate recurring-task instances in multi-client sync setups:

```bash
# primary client
task rc.confirmation=off config recurrence on

# other clients
task rc.confirmation=off config recurrence off
```

- Pick the primary client intentionally.
- Document this choice when helping a user configure sync.

## Operational Safety

- Run `task sync` only when sync is configured and expected by the user.
- Inspect sync-related config before changing anything, but do not paste raw `task show sync` or `_show` output. Query targeted settings and redact secrets, credential paths, server URLs, client IDs, and local paths in user-facing summaries.
- Do not expose `sync.encryption_secret`, access keys, or downloaded credential paths in logs or summaries.
- Prefer a dry explanation over modifying cloud credentials automatically.
- If sync errors mention credentials, remote object permissions, replica identity, or encryption, stop and inspect config rather than retrying writes.
- `purge.on-sync` (default off) auto-purges tasks that have been Deleted and unmodified for 180 days after each `task sync`; see `taskrc-configuration.md`.

### Detecting Sync Success vs Failure

- `task sync` and `task sync init` exit 0 on success and non-zero (observed: 2) on failure. Branch on the exit code, not on stdout text — see the exit-code-first pattern in `commands-and-syntax.md`.
- With `rc.verbose=nothing` a successful sync prints nothing, so stdout-parsing is unreliable; the exit code is the only safe signal.
- Common exit-2 failures: `No sync.* settings are configured. See task-sync(5).` (sync not configured) and `unable to open database file: .../taskchampion-local-sync-server.sqlite3: Error code 14` (`sync.local.server_dir` missing/uncreatable).
