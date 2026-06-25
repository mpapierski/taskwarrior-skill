# Filters, Search, Reports, And Export

Use this file for selecting task sets, searching, custom reports, report columns, sorting, and machine-readable ingestion.

## Filter Basics

- Empty filter means all tasks accepted by the command/report.
- `attribute:value` matches an attribute.
- `attribute:` or `attribute.none:` matches tasks without that value.
- `attribute.any:` matches tasks with any value.
- `+tag` requires a tag; `-tag` excludes it.
- `/pattern/` searches description and annotations.
- Multiple terms imply `and`.

Examples:

```bash
task status:pending count
task project:Home list
task project: count
task +work -blocked ready
task /schema/ long
```

## Logic And Precedence

- Use `and`, `or`, `xor`, and `!`.
- Use parentheses when mixing logical operators.
- Quote parentheses so the shell passes them to Taskwarrior.
- Built-in report filters combine with command-line filters, so disjunctions usually need grouping.

Examples:

```bash
task project:Home -work count
task '(project:Home or project:Garden)' list
task '!(project:Home or project:Garden)' all
```

## Attribute Modifiers

Common modifiers:

- `before`, `under`, `below`: less than in the attribute's semantic ordering.
- `after`, `over`, `above`: greater than.
- `by`: inclusive `before`.
- `none`: no value.
- `any`: some value.
- `is`, `equals`: exact match.
- `isnt`: inverse exact match.
- `not`: inverse of the attribute's default comparison. For example, `project.not:H` excludes projects that match the default `project:H` prefix comparison.
- `has`, `contains`: substring match (case-sensitive by default; see Search).
- `hasnt`: inverse substring match (case-sensitive by default; see Search).
- `startswith`, `left`: prefix match.
- `endswith`, `right`: suffix match.
- `word`: whole-word match.
- `noword`: inverse whole-word match.

Examples:

```bash
task due.before:eom priority.not:L list
task due.by:eow list
task priority.none: list
task description.has:schema list
task project.startswith:Repo list
task description.word:API list
```

Calculated attributes such as `urgency` / `urg` can be used in filters and reports.

## Operators

Taskwarrior supports logical and relational operators:

```text
and or xor !
< <= = == != !== >= >
( )
```

- `=` is approximate equality.
- `==` is exact equality.
- `!=` and `!==` negate approximate/exact equality.
- Dates compare approximately by day for `=`.
- Strings compare approximately by prefix for `=`.

Examples:

```bash
task 'due < eom and priority != L' list
task 'description ~ schema' list
task 'desc !~ schema' list
```

## Search

- `/pattern/` is a convenient search across description and annotations.
- Regex is enabled by default in modern Taskwarrior.
- Quote search patterns containing spaces.
- Case sensitivity is controlled by `search.case.sensitive`, which defaults to `1` (case-SENSITIVE on all non-Cygwin platforms) and governs `/pattern/`, the `~` operator, and `has`/`contains`/`hasnt` alike.
- For any user-requested text search where the user did not specify exact casing, prepend `rc.search.case.sensitive=0` so a case mismatch does not silently return zero or partial results. A lowercase `/apple/` misses `Find the Apple` by default.
- A search with no matches exits 1 (see "Exit Codes And No-Match Detection" below), so do not treat exit 1 here as a hard error.

Examples:

```bash
task /foo/ long
task '/foo bar/' list
task rc.regex:off /literal*/ list
task rc.search.case.sensitive=0 /keyword/ export
task rc.search.case.sensitive=0 'description ~ keyword' export
```

## Report Types

- Static built-ins are not normal configurable tables: `summary`, `information`, `calendar`, `colors`, `export`, history/ghistory, burndown, `timesheet`.
- Modifiable built-ins act like default custom reports: `list`, `next`, `ready`, `waiting`, `overdue`, `blocked`, `blocking`, `unblocked`, `active`, `all`, `completed`, `recurring`, `newest`, `oldest`, `ls`, `minimal`, `long`.
- Custom reports are `report.<name>.*` config entries.
- `limit:<number>` or `limit:page` constrains report row count for large result sets.

Inspect reports:

```bash
task reports
task show report.next
task columns
task columns description
```

## Custom Reports

Custom reports are persistent config. Do not create or change `report.<name>.*` settings unless the user asked for a reusable report. For one-off agent analysis, prefer built-in reports, explicit filters, JSON export, or an isolated temporary taskrc/data store.

For one-off report display changes, prefer runtime report overrides:

```bash
task rc.report.next.sort=due-,urgency- next
task rc.report.list.columns=id,project,description.count list
```

Define five config values:

- `report.<name>.description`
- `report.<name>.columns`
- `report.<name>.labels`
- `report.<name>.sort`
- `report.<name>.filter`

Example:

```bash
task rc.confirmation=off config report.simple.description 'Simple list of open tasks by project'
task rc.confirmation=off config report.simple.columns 'id,project,description.count'
task rc.confirmation=off config report.simple.labels 'ID,Project,Description'
task rc.confirmation=off config report.simple.sort 'project+/,entry+'
task rc.confirmation=off config report.simple.filter 'status:pending'
task simple
```

Sort syntax:

- `+` ascending, `-` descending.
- `/` after a sort column inserts a visual break by that value.
- Sort can use attributes not displayed as columns.
- Do not use `sort=none` for natural/insertion order. In task 3.4.2 a report with `sort=none` suppresses the entire table body — zero rows render (empty output with `rc.verbose=nothing`; only an "N tasks" summary with verbose on), despite the manpage claiming tasks appear "in the order in which they are selected." An agent will see empty output and wrongly conclude nothing matched. For unsorted-but-rendered output use an empty sort (`sort=`); for programmatic natural-order data use `task export` (independent of report sort, returns tasks in selection/UUID order).
- `random` produces a fresh random order each time the report runs.

## Exit Codes And No-Match Detection

Table/report commands (`list`, `next`, `ready`, `all`, etc.) exit 1 when the filter matches zero tasks and 0 when at least one matches. So for these commands exit 1 does NOT mean the command failed — it usually just means "nothing matched." This qualifies the write-oriented rule in commands-and-syntax.md (nonzero = did not apply), which is correct for writes but misleads an agent that branches on a report's exit status. Genuine parse/config errors (e.g. mismatched parentheses, an unknown column) exit 2, not 1.

For programmatic "does anything match / how many" checks, never branch on a report's exit code. Instead:

- `task <filter> count` is the agent-preferred existence/cardinality test: it prints a bare integer on stdout and exits 0 even for zero matches (prints `0`). Use it as the canonical "are there any tasks?" primitive.
- `task <filter> export` always exits 0, returning `[]` when empty. Use it for the actual data once `count` confirms matches exist.

```bash
task project:Nope count    # prints 0, exit 0
task project:Nope list     # exit 1 (no match), looks like failure
task project:Nope export   # prints [], exit 0
```

See agent-runtime-safety.md ("never trust exit codes; verify with a follow-up query").

## Export For Agents

Use JSON export for reasoning:

```bash
task export
task project:Repo +OVERDUE export
task +READY export
task +WAITING export
task rc.json.array=0 +READY export
```

Guidelines:

- Parse JSON before answering.
- Summarize ID, description, project, status, priority, due/scheduled/wait timing, dependency state, and notable tags.
- Omit UUIDs, timestamps, urgency, and raw JSON unless requested.
- Use human reports only when the user wants terminal output; prefer `export`/`count` for programmatic checks because their exit codes are reliable (see "Exit Codes And No-Match Detection").
- After write commands, use export to verify the actual stored task state when later steps depend on IDs, UUIDs, dependencies, hooks, contexts, wait/scheduled state, or completion state.

## Column Format Cheatsheet

Use `task columns` and `task columns <name>` as the source of truth. Common custom-report formats:

- `description.count`: description plus annotation count.
- `description.oneline`: description and annotations collapsed into one line.
- `description.truncated`: shortened description for narrow reports.
- `uuid.short`, `parent.short`, `template.short`: short UUID display.
- `project.parent`: top-level parent project.
- `project.indented`: hierarchy-friendly project display.
- `tags.count`, `depends.count`: compact counts.
- `tags.indicator`, `depends.indicator`, `recur.indicator`, `start.active`: compact status marks.
- `due.relative`, `scheduled.countdown`, `wait.remaining`, `until.remaining`: human-readable date timing.
- `urgency.integer`: rounded urgency.

Example:

```bash
task rc.confirmation=off config report.review.columns 'id,project.parent,tags.count,due.relative,description.count,urgency.integer'
task rc.confirmation=off config report.review.labels 'ID,Area,Tags,Due,Description,Urg'
task rc.confirmation=off config report.review.sort 'project+/,urgency-'
task rc.confirmation=off config report.review.filter '+READY'
```
