# Taskwarrior Reference

This reference distills the official Taskwarrior docs plus local `task help`, `task commands`, `task reports`, `man task`, and `man taskrc` checks against the installed `task` 3.1.0 binary.

## Scope

- Default to repo-local mode with `scripts/taskw.py`.
- Require `PyYAML` in the active Python environment for repo-local mode.
- Invoke the wrapper with the Python interpreter that belongs to the current project or virtualenv.
- Use global `task ...` only when repo instructions explicitly require the global Taskwarrior config and data.
- Ignore `.taskwarrior/data/` in git.
- Prefer versioning `.taskwarrior/tasks.yaml` when shared task state is useful.
- Repo-local mode uses:
  - `.taskwarrior/taskrc` for persistent config, contexts, and custom reports
  - `.taskwarrior/data/` for the SQLite-backed Taskwarrior state
  - `.taskwarrior/tasks.yaml` as the round-tripped YAML snapshot

## Command Shape

Taskwarrior documents the general form as:

```text
task [<filter>] <command> [<mods>]
```

Examples from `task help` and `man task`:

- `task add Fix the leaky plumbing`
- `task 3 modify priority:H`
- `task project:Home due.before:today list`
- `task +weekend annotate "Need hardware store run"`

Use `--` before the description when text would otherwise be parsed as metadata:

```bash
task add -- project:Home needs scheduling
```

## Core Task Modeling

- `description`: main task text
- `project`: project or subproject, commonly dotted like `Repo.Backlog`
- `priority`: `H`, `M`, `L`
- `due`: hard deadline
- `scheduled`: earliest meaningful start date
- `wait`: hide until actionable
- `start`: mark active work
- `depends`: dependency chain
- `tags`: cross-cutting descriptors
- `annotations`: durable notes

Use projects for ownership or workstream, tags for cross-cutting labels, and annotations for notes that should not clutter the main description.

Recommended pattern for agents:

- Keep descriptions short, usually one line.
- Use annotations for richer context such as goals, constraints, acceptance criteria, blockers, references, and links.
- Add multiple targeted annotations instead of turning the description into a paragraph.
- When answering questions about a specific task, inspect annotations before summarizing it.

## Projects And Subprojects

Workflow examples from the official docs recommend project hierarchies such as `tw.242`, `Work.Tickets`, or `Volunteering.Floss.Taskwarrior`.

Taskwarrior 3.1.0 behavior verified locally:

- `project:Work` matches `Work` and `Work.*`
- `project.is:Work` matches only `Work`

Use this pattern:

- Root area: `project:Repo`
- Child stream: `project:Repo.Backlog`
- Leaf work: `project:Repo.Backlog.API`

Useful commands:

- `task projects`
- `task summary`
- `task project:Repo list`
- `task project.is:Repo list`

## Tags And Virtual Tags

Use real tags for descriptors such as `+bug`, `+docs`, `+blocked`, `+frontend`.

Official virtual tags include:

- `+READY`
- `+TODAY`
- `+OVERDUE`
- `+BLOCKED`
- `+UNBLOCKED`
- `+BLOCKING`
- `+WAITING`
- `+ACTIVE`
- `+PROJECT`
- `+PRIORITY`

Useful commands:

- `task tags`
- `task +READY list`
- `task +OVERDUE list`
- `task +BLOCKED list`

## Dates

The official date guidance is:

- Use `due` for the latest acceptable completion time.
- Use `scheduled` for the earliest opportunity to work on the task.
- Use `wait` to hide a task until later.

Best-practice interpretation:

- Do not add `due` dates unless there is a real deadline or deliberate commitment.
- Prefer `scheduled` for "not before".
- Prefer `wait` when the task should disappear from normal reports until later.

Useful reports and filters:

- `task overdue`
- `task ready`
- `task waiting`
- `task +TODAY list`
- `task due.any: list`
- `task due.none: list`

## Dependencies

Use dependencies when there is a clear sequence:

```bash
task add "Implement API client"
task add "Wire client into CLI" depends:1
```

Useful views:

- `task blocked`
- `task blocking`
- `task unblocked`
- `task ready`

## Annotations

Annotations are the right place for long-form task context.

Useful patterns:

```bash
task 12 annotate "Goal: make report ingestion machine-readable for the agent."
task 12 annotate "Acceptance: default current-task query uses export, not list."
task 12 annotate "Blocker: waiting on a decision about raw JSON vs summarized output."
```

Best-practice guidance:

- Keep the task description as a short title.
- Use annotations for evolving details.
- Prefer several concise annotations over one massive blob.
- Add annotations during triage, not only after work starts.
- When presenting a task to a user, summarize the relevant annotation content instead of dumping it verbatim unless they ask.

## Contexts

Contexts persist default read filters and optional write modifications.

Documented forms:

- `task context define home project:Home`
- `task context home`
- `task context list`
- `task context none`

Important doc guidance:

- A complex read context does not automatically make a good write context.
- If the filter is complex, explicitly set `context.<name>.write` to the modifications you want applied on `add` or `log`.

Example:

```bash
task context define family 'project:Family or +paul or +nancy'
task config context.family.write project:Family
```

## Reports Worth Using First

Built-in reports from `task help` and `task reports`:

- `next`: most urgent tasks
- `ready`: actionable tasks
- `list`: standard listing
- `ls`: shorter listing
- `long`: more detail
- `active`: started tasks
- `waiting`: hidden tasks
- `overdue`: late tasks
- `projects`: project inventory
- `tags`: tag inventory
- `summary`: status by project
- `completed`: finished tasks
- `recurring`: recurring tasks
- `information`: full task metadata

Use `task columns` and `task reports` before defining custom report columns or sorts.

## Machine Ingestion

For agent consumption, prefer `export` over scraping tabular reports.

Useful patterns:

- `task export`
- `task export`
- `task export ready`
- `task export next`
- `task project:Repo export overdue`
- `task +READY export`

Observed on Taskwarrior 3.1.0:

- `task export ready` applies the `ready` report selection while returning raw task objects as JSON.
- `task +READY export` yields the same task set for the common `ready` case.
- `task rc.json.array=0 export ...` emits one JSON object per line instead of a JSON array.

Practical guidance:

- Default to `task export` for "current tasks" or general task inspection.
- Use human reports when you want a quick terminal scan.
- Use `export <report>` when the agent needs to inspect or transform the resulting task set.
- Prefer direct exports for automation, ranking, downstream filtering, or diffing against another task set.
- Treat `.taskwarrior/tasks.yaml` as the versioned snapshot and `export` as the live query interface.
- Use the JSON export to build a readable answer for the user. Do not paste raw JSON or raw tables by default.
- In user-facing summaries, prefer: ID, description, status, priority, project, due or scheduled timing, dependency/blocking state, and notable tags.
- Skip UUIDs, timestamps, and other low-level fields unless they matter to the request.

## Import And Export

From `man task`:

- `task import [<file> ...]` imports JSON and updates existing tasks by UUID.
- `task export` exports all tasks as JSON.

Observed on Taskwarrior 3.1.0:

- `import` accepts a JSON array or newline-delimited JSON objects.
- `export` output can be re-imported without duplicate tasks because UUIDs are preserved.
- Recurring task imports should use `rc.recurrence.confirmation=no` in automation.

This skill's wrapper therefore:

1. Reads `.taskwarrior/tasks.yaml`
2. Transcodes it to JSON for `task import`
3. Runs the requested command
4. Exports JSON with `task export`
5. Transcodes the result back to `.taskwarrior/tasks.yaml`

Use `--rebuild` on the wrapper if the YAML snapshot was edited manually and you need to force the database to match it.

## Automation Safety

Relevant `taskrc` settings from `man taskrc`:

- `data.location`: path to task data
- `confirmation`: delete and undo confirmation
- `bulk`: confirmation threshold for multi-task changes
- `allow.empty.filter`: reject empty-filter write commands when set to `0`
- `json.array`: export as a JSON array
- `context.<name>.read` and `context.<name>.write`

The wrapper forces these runtime overrides:

- `rc.data.location=.taskwarrior/data`
- `rc.confirmation=off`
- `rc.bulk=0`
- `rc.allow.empty.filter=0`
- `rc.recurrence.confirmation=no`

Internal import/export calls also use:

- `rc.verbose=nothing`
- `rc.hooks=off`
- `rc.json.array=1` for export

YAML transcoding details in this repo:

- `scripts/taskw.py` expects `PyYAML` to be installed in the active Python environment.
- Do not hard-code a package manager into the skill. Follow the host project's normal environment workflow.
- If `PyYAML` is missing, install it the way that repo already manages Python dependencies.

`rc.bulk=0` is documented as "infinity", which prevents automation from hanging on the bulk confirmation prompt. The tradeoff is that the agent must be precise with write filters.

## Workflow Heuristics

Pulled from the official workflow examples and docs:

- Use project hierarchies heavily when work naturally nests.
- Use tags sparingly and deliberately.
- Use `start` and `stop` to remember where work was left off.
- Use annotations for implementation notes, decisions, or blockers.
- Keep due dates meaningful; do not turn them into wishful ordering.
- Use `wait` to keep the visible list short.
- Use dependencies only when the sequence is real enough to help.

## Source URLs

- https://taskwarrior.org/docs/
- https://taskwarrior.org/docs/commands/add/
- https://taskwarrior.org/docs/tags/
- https://taskwarrior.org/docs/using_dates/
- https://taskwarrior.org/docs/workflow/
- https://taskwarrior.org/docs/man/task.1/
- https://taskwarrior.org/docs/man/taskrc.5/
