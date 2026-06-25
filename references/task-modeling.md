# Task Modeling

Use this file for attributes, IDs, projects, tags, priority, recurrence, dependencies, annotations, urgency, UDAs, and JSON task shape. Use `dates-and-scheduling.md` for detailed date parsing, scheduling, named dates, durations, and relative date expressions.

## Core Attributes

- `status`: usually `pending`, `waiting`, `completed`, `deleted`, or `recurring`.
- `uuid`: durable task identity. Prefer UUIDs for long-lived references.
- `id`: local working-set number. It can change after the working set is rebuilt.
- `description`: task title.
- `project`: hierarchy-capable workstream.
- `tags`: label list.
- `priority`: optional coarse priority.
- `entry`: creation time.
- `modified`: last modification time.
- `start`: task is active.
- `end`: completion/deletion time.
- `due`: deadline.
- `scheduled`: earliest start.
- `wait`: hide until actionable.
- `until`: recurrence end.
- `recur`: recurrence period.
- `limit`: report row limit, as a positive integer or `page`.
- `depends`: dependencies by UUID/ID.
- `parent`, `mask`, `imask`: recurrence linkage.
- `annotations`: timestamped notes.
- `urgency`: calculated ranking value.

## IDs And UUIDs

- IDs are convenient in the current terminal session but not durable.
- Why IDs shift: GC (`gc=1`, default) renumbers working-set IDs to a gapless `1..N` sequence, but only when a report that DISPLAYS IDs is run, not during the write itself. So it is safe to rely on the last displayed ID. Completing or deleting a low-numbered task shifts every higher ID down on the next ID-listing report; reusing an old listing's ID after running another report in between will hit the wrong task.
- UUIDs are stable across sync, export/import, and working-set rebuilds.
- Use `task ids` for current local IDs and `task <filter> _unique uuid` for durable IDs.
- Use `task information <id>` when the full task record matters.
- Avoid storing local IDs in external systems; store UUIDs instead.
- After writes such as `done`, `delete`, imports, or synchronization, capture UUIDs up front or refresh IDs with `task ids`, `task export`, or UUID-based lookups before chaining more local-ID writes.
- To keep IDs stable across a multi-step ID-based sequence, pass `rc.gc=0` (equivalently `rc.gc=off`) on each invocation; this freezes IDs and preserves gaps at a performance cost. Use it only as a command-line override, never persisted.
- `task add` reports a newly created local ID, but use `task _get <id>.uuid`, `task <id> export`, or `task <id> information` when follow-up identity matters.

## Projects

- Use projects for ownership, area, or workstream.
- Use dotted hierarchy: `Work`, `Work.Tickets`, `Work.Tickets.API`.
- `project:Work` matches `Work` and children.
- `project.is:Work` matches only `Work`.
- Use `task projects` and `task summary` for project inventory.

## Tags And Virtual Tags

- Use real tags for cross-cutting labels: `+bug`, `+docs`, `+frontend`, `+blocked`.
- Add a real tag with `+tag`; remove it with `-tag`.
- Avoid using too many tags as a substitute for project structure.
- Special real tags: `+nocolor` disables color rules for that task; `+nonag` suppresses nag messages when completing it; `+nocal` omits it from calendar output; `+next` elevates it in the `next` report.
- `+nonag` is unrelated to release-news reminders; use `task news` or temporary verbosity overrides for those.
- `task tags` lists stored tags, including special tags. It does not list virtual tags.
- Virtual tags are computed filters, not stored tags. Adding or removing them is an error.
- Virtual tags from `man task`: `+ACTIVE`, `+ANNOTATED`, `+BLOCKED`, `+BLOCKING`, `+CHILD`, `+COMPLETED`, `+DELETED`, `+DUE`, `+INSTANCE`, `+LATEST`, `+MONTH`, `+ORPHAN`, `+OVERDUE`, `+PARENT`, `+PENDING`, `+PRIORITY`, `+PROJECT`, `+QUARTER`, `+READY`, `+SCHEDULED`, `+TAGGED`, `+TEMPLATE`, `+TODAY`, `+TOMORROW`, `+UDA`, `+UNBLOCKED`, `+UNTIL`, `+WAITING`, `+WEEK`, `+YEAR`, and `+YESTERDAY`.
- `+CHILD` and `+PARENT` are deprecated in Taskwarrior 2.6.0+ terminology; prefer recurrence `+INSTANCE`, `+TEMPLATE`, and dependency filters where applicable.

## Priority And Urgency

- Built-in priorities are `H`, `M`, and `L`; no priority is valid.
- In modern Taskwarrior, `priority` is implemented as a built-in string UDA with default values `H,M,L,`.
- Priority is only one urgency contributor.
- Use priority sparingly for coarse ordering.
- Urgency is calculated from coefficients such as due dates, priority, waiting/scheduled state, active state, age, annotations, tags, blocking, and optionally UDAs. See `taskrc-configuration.md` for the numeric built-in defaults.
- The largest positive built-in terms are `+next` (15.0) and due (12.0), so they dominate default ordering. The built-in priority-UDA coefficients are `H`=6.0, `M`=3.9, `L`=1.8 — these are not in `taskrc(5)` and are only observable via `task <id> _urgency`.
- Urgency is non-linear: tag and annotation contributions do not scale with count — the coefficient is multiplied by 0.8 for one, 0.9 for two, and 1.0 for three or more, so adding tags past three adds nothing. The due term is a proximity sliding scale that decays as the due date moves into the future, not a flat per-task add. Do not estimate urgency as a simple sum of coefficients; verify with `task <id> _urgency`. This algorithm is documented upstream (taskwarrior.org/docs/urgency), not in the local manpage.
- Customize priority values or urgency coefficients only when the user's workflow explicitly needs changed ranking behavior. Keep priority/UDA configuration consistent across synced clients.

## Report Limit

- `limit:<number>` limits report output to that many rows.
- `limit:page` limits output to one terminal page.
- Limit is a report control attribute, not task metadata to preserve as task meaning.
- Prefer explicit limits when an agent needs a small sample from a large task database.

## Dates

For date-heavy work, read `dates-and-scheduling.md`.

Use date attributes semantically:

- `due`: deadline or commitment.
- `scheduled`: earliest sensible start.
- `wait`: hide from most normal reports until the date passes.
- `until`: stop recurring generation or auto-expire a task after this date. Use sparingly because it can delete tasks automatically.
- `entry`, `modified`, `start`, `end`: lifecycle metadata.

Common date forms:

```bash
task add "Submit report" due:friday
task add "Plan trip" scheduled:tomorrow
task add "Renew cert" due:2026-07-01
task add "Someday idea" wait:someday
task due.before:eom list
task +TODAY list
```

Named dates and shorthands include `today`, `tomorrow`, weekdays, `eod`, `eow`, `eom`, `eoq`, `eoy`, `sow`, `som`, `soy`, month names, week numbers, and calculated forms like `eom - 1wk`. Use exact dates when user intent is date-sensitive.

Durations can be used where dates are expected and are interpreted relative to now: `2days`, `3wks`, `1mo`, `P3D`, `PT12H`. Month/year durations are imprecise unless anchored to a date.

Use `task calc <expression>` when you need to verify how Taskwarrior resolves a date expression.

## Recurrence

- Recurring template tasks use `status:recurring`, `recur`, and usually `due`.
- The recurring template is hidden from normal reports; use `task recurring`, `task all`, or `task information` when inspecting it.
- Pending instances are generated from the template. These are the visible tasks users normally complete.
- Instances inherit description, recurrence, due timing, and usually project, priority, and tags from the template.
- Instances track the template via `parent` and an instance index (`imask` / "Mask Index"). These are what 3.4.2 actually populates to link instances to their template.
- The template tracks generated instance states with `mask`: pending (`-`), completed (`+`), deleted (`X`), or waiting (`W`).
- In 3.x, recurring tasks (template and instances) also carry `rtype`, recurrence type, always `periodic` in 3.4.2. Chained recurrence is not supported: `rtype:chained` is rejected. `rtype` is exported on every recurring task and instance and is filterable (e.g. `rtype:periodic`).
- `template` and `last` are read-only recurrence-registry columns that may appear in some scenarios; do not set them directly.
- Interact with instances in normal use. Avoid directly modifying the hidden template unless the user intends to change the recurrence series.
- Common recurrence periods: `daily`, `weekdays`, `weekly`, `biweekly`, `monthly`, `quarterly`, `semiannual`, `annual`, `biannual`, or numbered forms like `2wks`.
- Use `until` to end recurrence.
- Use `task recurring` to inspect recurring tasks.
- `recurrence.limit` controls how many future instances are shown/generated in reports. Completing one instance does not necessarily make another appear immediately.
- In automation imports involving recurrence, use `rc.recurrence.confirmation=no` when appropriate.
- With sync across multiple clients, choose one primary client for recurrence generation and set `recurrence=off` on the others to avoid duplicate instances.

Example:

```bash
task add "File weekly report" due:friday recur:weekly
task add "Pay rent" due:2026-07-01 recur:monthly until:2027-01-01
```

## Dependencies

- Use `depends:<id-or-uuid>` when order is real and useful.
- Multiple dependencies are comma-separated.
- Prefix a dependency with `-` to remove it.
- Dependent tasks appear in `blocked`; tasks blocking others appear in `blocking`.
- Dependencies are represented durably by UUID in JSON export even when specified with a local ID.
- Completing a blocking task can emit an `Unblocked ...` message and make dependent tasks actionable, though the dependency relationship can remain in the task data.
- To find tasks that depend on a specific task, get the blocker UUID and filter dependents with `depends.has:<uuid>`.

Examples:

```bash
task add "Implement API client" project:Repo.SDK
task add "Wire client into CLI" project:Repo.SDK depends:1
task blocked
task blocking
task unblocked
task depends.has:$(task _get 1.uuid) blocked
```

For automation or multi-step plans, capture UUIDs and use UUID filters:

```bash
task add "Implement API client" project:Repo.SDK
client_uuid=$(task _get 1.uuid)
task add "Wire client into CLI" project:Repo.SDK depends:$client_uuid
task +BLOCKED export
task $client_uuid done
```

Remove one dependency by prefixing it with `-`:

```bash
task 2 modify depends:-$client_uuid
```

## Annotations

- Use annotations for durable notes, links, acceptance criteria, blockers, and decisions.
- Prefer multiple focused annotations over a long description.
- Inspect annotations before explaining a task.

```bash
task 12 annotate "Goal: produce JSON export for ready tasks."
task 12 annotate "Acceptance: user-facing answer groups ready and waiting tasks."
```

## User Defined Attributes

- UDAs define extra metadata fields.
- Types: `string`, `numeric`, `uuid`, `date`, `duration`.
- String UDAs may restrict allowed values.
- UDAs can have defaults, report labels, and urgency coefficients.
- Removing UDA config can orphan stored UDA values.
- An invalid UDA type persisted via `task config` makes every subsequent `task` invocation error until the line is removed. Only `string`, `numeric`, `date`, `duration`, and `uuid` are allowed.

To define or test a UDA without persisting, use in-memory overrides:

```bash
task rc.uda.estimate.type=numeric rc.uda.estimate.label=Est add "Paint the door" estimate:4
```

To create a permanent, shared-across-synced-clients UDA, use `task config` — but note this rewrites the persistent taskrc config file and is NOT scoped by `rc.data.location`, so the usual temp-DB isolation does not protect `~/.taskrc`. Get explicit user approval first, and add `rc.confirmation=off` (or `rc:<path>`/`TASKRC=` to target an alternate file). See agent-runtime-safety.md.

```bash
task rc.confirmation=off config uda.estimate.type numeric
task rc.confirmation=off config uda.estimate.label Est
```

Use a UDA when the value needs sorting, filtering, reports, or import/export structure. Use a tag for lightweight labels and annotations for prose.
