# TaskChampion Task Representation

Use this file for TaskChampion-backed internal task representation, sync-safe integration behavior, atomicity, validity, and UDA namespacing. Use `hooks-integration.md` for Taskwarrior CLI JSON import/export and hook JSON.

## Scope

- This is the internal model exposed by TaskChampion, not the normal `task export` JSON shape.
- Prefer the `task` CLI, `task export`, and `task import` for ordinary integrations.
- Use this model when an integration talks directly to TaskChampion concepts or explains sync behavior.

## Key/Value Model

- Internally, a task is a key/value map with string keys and string values.
- All fields are optional at the storage layer. Display layers apply defaults where needed.
- Any key/value map is considered a valid task. Consumers should interpret best-effort even when fields appear contradictory.
- Integers are decimal strings.
- In the task key/value map, timestamp values are stored as Unix epoch integer strings (e.g. `1781774049`); the `annotation_<timestamp>` key suffix is also a Unix epoch.
- The operation log (sync layer) records each operation's own `timestamp` in RFC3339 (e.g. `2026-06-18T16:20:43Z`), not Unix epoch. See Operations Log and Replica Model below.

Common keys:

- `status`: one of `pending` (default), `completed`, `deleted`, `recurring` — full lowercase words, stored verbatim in the task data JSON and in operation-log Update `value`. `waiting` is not a stored status: a waiting task has `status:pending` plus a `wait` timestamp.
- `description`: one-line task summary.
- `entry`, `modified`, `start`, `end`, `wait`: timestamp fields.
- `tag_<tag>`: presence means the task has tag `<tag>`; value is the literal marker `x`. Taskwarrior also maintains a denormalized `tags` key holding the comma-joined tag list.
- `dep_<uuid>`: dependency on another task UUID; value is the literal marker `x`. Taskwarrior also maintains a denormalized `depends` key holding the comma-joined dependency UUIDs.
- `annotation_<timestamp>`: annotation text created at that timestamp.
- `recur`: recurrence period string (e.g. `weekly`); managed by Taskwarrior.
- `rtype`: recurrence type; managed by Taskwarrior. The 3.4.2 CLI only produces `periodic` and rejects `rtype:chained` (see `task-modeling.md`), though TaskChampion recognizes the `chained` value.

Taskwarrior derives its tag/dependency view from the per-item `tag_<tag>`/`dep_<uuid>` keys; `tags`/`depends` are redundant copies it also writes.

The user-facing small integer `id` is not a key in the stored task map. It is assigned by the separate local `working_set` table (a uuid->id index that is per-replica, unstable, and not synced); use `uuid` for durable identity.

TaskChampion recognizes the `recurring` status value, but Taskwarrior manages recurrence behavior.

## Atomicity

- Sync reconciliation does not support read-modify-write semantics safely for multi-value fields.
- Avoid integration updates that read a list, append one value, and write the whole list back. Concurrent replicas can lose one side of the change.
- Prefer atomic key updates:
  - add a tag by setting `tag_<tag>`.
  - remove a tag by deleting `tag_<tag>`.
  - add a dependency by setting `dep_<uuid>`.
  - remove a dependency by deleting `dep_<uuid>`.
  - add an annotation by setting a new `annotation_<timestamp>` key.
- The `tags`/`depends` strings are exactly the comma-separated multi-value lists this section warns are unsafe to read-modify-write. Keeping the per-item and denormalized forms mutually consistent is non-trivial, so mutate tags and dependencies only through the CLI (`modify +tag`, `depends:<uuid>`); hand-writing the stored map leaves a stale companion string.
- When using the CLI, prefer native commands such as `task <id> modify +tag`, `depends:<uuid>`, and `annotate`; Taskwarrior handles the storage operations.

## Operations Log and Replica Model

- The TaskChampion store keeps both an `operations` log and the denormalized `tasks` key/value map.
- The `operations` log is an ordered, append-only change journal and is the source of truth synced between replicas.
- The `tasks` map is a derived cache produced by replaying operations; it is not synced directly.
- Operation variants: `UndoPoint`, `Create{uuid}`, `Update{uuid,property,old_value,value,timestamp}`, `Delete{uuid,old_task}`. Each row has a `synced` flag.
- `task undo` rolls back the most recent operations up to the last `UndoPoint`.
- Replica invariant: applying a replica's operations to the base state reproduces its current tasks. Sync exchanges operations (deltas), not the `tasks` rows.
- A direct write to the `tasks` table records no operation: the CLI reads it locally, but the change is silently never synced and corrupts undo/replica consistency. Every mutation must go through the `task` CLI / TaskChampion so an operation is recorded.

## UDA Namespacing

- Unrecognized keys are treated as user-defined attributes.
- Applications that define UDAs should namespace them as `<namespace>.<key>`, for example `devsync.github.issue-id`.
- Namespacing avoids collisions between integrations.
- Existing integrations may use legacy UDA names without namespaces; preserve those when encountered.

## Integration Guidance

- Preserve unknown keys and values when operating below the CLI layer.
- Do not assume missing fields mean corruption. Missing `end` on a completed task, for example, should be interpreted best-effort.
- Do not use this representation as a reason to edit the SQLite database directly: a raw write to the `tasks` table records no operation, so it never syncs and breaks undo/replica consistency (see Operations Log and Replica Model).
- If a task representation question is really about import/export JSON, use `hooks-integration.md` instead.
