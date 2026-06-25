# Taskrc Configuration Reference

Use this file for `.taskrc`, `taskrc(5)`, configuration syntax, includes, environment precedence, config variable families, and "what setting controls X?" questions. Use `config-storage-sync.md` first when the task is about database safety, upgrades, storage movement, or sync operations.

Condensed from local `man taskrc` / upstream `taskrc(5)` for Taskwarrior 3.4.2.

## Table Of Contents

- Configuration syntax and precedence
- Editing safely
- File, terminal, and miscellaneous settings
- Dates, calendar, journal, holidays, and dependencies
- Colors
- Urgency
- Defaults, reports, UDAs, contexts, and sync

## Configuration Syntax And Precedence

- Default taskrc path is `~/.taskrc`.
- If `~/.taskrc` is absent, Taskwarrior falls back to `$XDG_CONFIG_HOME/task/taskrc`, and to `~/.config/task/taskrc` when `XDG_CONFIG_HOME` is unset (the XDG default). `~/.taskrc` takes precedence when both exist.
- Override the taskrc file per command with `task rc:<path> ...` or `TASKRC=<path> task ...`.
- Override data path per command with `TASKDATA=<path> task ...`, `task rc.data.location:<path> ...`, or `task rc.data.location=<path> ...`.
- Command-line overrides have higher priority than environment variables. Environment variables override defaults, not command-line arguments.
- Individual config overrides use `rc.<name>:<value>` or `rc.<name>=<value>`.
- Taskwarrior can prompt to create a sample taskrc if no config file exists.

Taskrc entries are simple single-line values:

```text
<name> = <value>
include <file>
# comment
```

- Whitespace around `<name>`, `=`, and `<value>` is ignored; whitespace inside `<value>` is preserved.
- Whitespace is not permitted inside comma-separated lists.
- There are no line continuations.
- Values support UTF-8 and JSON-style escapes such as `\uNNNN`.
- Boolean settings accept `1`, `on`, `yes`, `y`, and `true` as enabled; other values are disabled.
- `name=` sets a blank value and overrides any default with blank.
- `include <file>` supports absolute or relative paths. `~`, environment variables, and taskrc variables are expanded.
- Relative include lookup order: current working directory, directory containing the active taskrc, then package-managed directories such as built-in theme/holiday locations.
- Comments start at `#` and run to end of line. There is no multi-line comment block.

## Editing Safely

- Prefer `task config <name> <value>` for persistent edits when the user asks to change config.
- `task config` prompts "Are you sure you want to add/change ...? (yes/no)" for EVERY write; with no TTY/closed stdin it silently no-ops ("No changes made.", exit 0, nothing written). For non-interactive writes pass `rc.confirmation=off`, e.g. `task rc.confirmation=off config default.command next`. See agent-runtime-safety.md.
- `task config` writes to the TASKRC file (default `~/.taskrc`, or whatever `rc:`/`TASKRC=` resolves to); `rc.data.location` does NOT redirect it. A temp-DB pattern using only `rc.data.location=$TMP` still modifies the real `~/.taskrc` — to isolate a config write you must also set `rc:$TMP/taskrc` or `TASKRC=$TMP/taskrc`.
- Use `task config <name>` with no value to delete a setting and fall back to the default.
- Use `task config <name> ""` to set a deliberately blank value.
- Use `task show [substring]` to display settings and validate the taskrc.
- Use temporary `rc.<name>=...` or `rc.<name>:...` overrides for automation or probes.
- Do not persistently change `data.location`, hooks, sync, recurring behavior, or destructive safety settings without explicit approval.
- Do not paste raw `task show`, `task _show`, or diagnostics output. Redact secrets, credential paths, server URLs, client IDs, and unrelated local paths.

Examples:

```bash
task show verbose
task rc.confirmation=off config default.command next
task rc.confirmation=off config nag ""
task rc.verbose=0 export
task rc:/tmp/taskrc rc.data.location:/tmp/taskdata next
```

## Files

- `data.location=$HOME/.task`: task data directory; `TASKDATA` overrides it.
- `hooks.location=$HOME/.task/hooks`: hook script directory. Some Taskwarrior 3.4.2 builds do not surface this key through `task show hooks.location` unless it is explicitly configured; default to `<data.location>/hooks` and inspect taskrc/includes for a non-default value.
- `gc=1`: enables rebuilding/garbage collection. Use temporary `rc.gc=0` only for specific cases; do not persistently disable it.
- `purge.on-sync=0`: purges old deleted tasks after sync when enabled.
- `hooks=1`: master switch for hook processing.
- `exit.on.missing.db=0`: when enabled, Taskwarrior exits if the database is missing.

## Terminal And Output Shape

- `detection=1`: detect terminal size with ioctl.
- `limit:25`: default report row limit; also accepts `page`.
- `defaultwidth=80`, `defaultheight=24`: fallback dimensions when detection is unavailable. `0` means unbounded.
- `avoidlastcolumn=0`: avoid last terminal column for problematic terminals.
- `hyphenate=1`: hyphenate wrapped lines mid-word.
- `editor=vi`: editor for `task edit`; Taskwarrior checks this, then `$VISUAL`, then `$EDITOR`, then `vi`.
- `reserved.lines=1`: bottom-screen reserved lines for `limit:page`.

## Verbosity And Automation Output

- `verbose=1`: default helpful explanatory output.
- `verbose=0`: regular output with fewer comments.
- `verbose=nothing`: suppress optional output, best for parsers.
- `verbose=<tokens>`: comma-separated output control. Tokens include `blank`, `header`, `footnote`, `label`, `new-id`, `new-uuid`, `news`, `affected`, `edit`, `special`, `project`, `sync`, `filter`, `context`, `override`, `recur`, and `default`.
- `new-uuid` overrides `new-id` and is useful for automation.
- `news` controls release-news reminders until `task news` records `news.version=<version>`.
- `affected`, `new-id`, `new-uuid`, `project`, `override`, and `recur` imply `footnote`; `default` implies `header`.
- `header`, `footnote`, and `project` comments go to stderr; the other optional comments go to stdout.
- The out-of-the-box default verbosity does NOT include `filter`, so filtered commands do not echo the parsed filter. To have an agent confirm the exact filter Taskwarrior parsed, add it back. The filter echo is a footnote on stderr, so `rc.verbose=filter` alone prints nothing — use `rc.verbose=filter,footnote` (or `rc.verbose=1`/`on`, which expand to all tokens incl. filter), e.g. `task rc.verbose=filter,footnote list +PENDING` prints `Filter: ( status = pending ... )`.

Useful forms:

```bash
task rc.verbose=0 add "Capture item"
task rc.verbose=nothing export
task rc.verbose=new-uuid,affected add "Capture item"
```

## Safety And Miscellaneous Behavior

- `confirmation=1`: prompts for delete and undo, and gates EVERY `task config` write (adding/changing/clearing any variable, including color rules, contexts, UDAs, custom reports, and sync keys). Leave enabled for humans; agents persisting config must pass `rc.confirmation=off` or the write is silently lost (see agent-runtime-safety.md).
- `allow.empty.filter=1`: empty-filter writes require confirmation; set `0` in automation to reject them.
- `bulk=3`: when this many or more tasks are modified in one command, Taskwarrior prompts per task REGARDLESS of `confirmation` (a bulk prompt is NOT disabled by `rc.confirmation=off`); `bulk=0` is treated as infinity (never prompt). For non-interactive batch writes that may touch >=3 tasks, set BOTH `rc.confirmation=off` AND `rc.bulk=0`; setting only one still hangs interactively or silently modifies 0 tasks (exit 1).
- `nag=You have more urgent tasks.`: prompt shown when starting/completing lower-urgency work; blank to suppress.
- `indent.annotation=2`, `indent.report=0`, `row.padding=0`, `column.padding=1`: report spacing controls.
- `list.all.projects=0`, `summary.all.projects=0`: include inactive/empty projects in project outputs when enabled.
- `complete.all.tags=0`, `list.all.tags=0`: tag completion and `tags` command scope.
- `print.empty.columns=0`: print columns with no data.
- `search.case.sensitive=1`: controls search case sensitivity.
- `regex=1`: regular expression support.
- `xterm.title=0`: sets terminal title when reports run.
- `expressions=infix|postfix`: expression notation preference.
- `json.array=1`: `export` emits a JSON array. With `json.array=0`, emits one JSON object per line.
- `_forcecolor=1`: force color even when stdout is not a TTY.
- `active.indicator=*`, `tag.indicator=+`, `dependency.indicator=D`, `uda.<name>.indicator=U`: indicator column strings.
- `abbreviation.minimum=2`: minimum unique abbreviation length for commands/values.
- `debug=0`, `debug.hooks=0`, `debug.parser=0`: diagnostic output; use temporarily for troubleshooting.
- `obfuscate=0`: replace report text with `xxx` for shareable bug reports.
- `alias.<name>=<command>`: command aliases, for example `alias.rm=delete`; inspect with `task show alias` before relying on an unknown alias.
- `burndown.cumulative=1`: burndown chart aggregation behavior.
- `sugar=1`: command-line syntax sugar. Leave enabled unless debugging parser behavior.

## Dates

- `dateformat=Y-M-D`: default parse/display date format.
- `dateformat.report=`, `report.X.dateformat=Y-M-D`: report date display; precedence is `report.X.dateformat`, then `dateformat.report`, then `dateformat`.
- `dateformat.holiday=YMD`: holiday date format.
- `dateformat.edit=Y-M-D H:N:S`, `dateformat.info=Y-M-D H:N:S`, `dateformat.annotation=`: display formats by surface.
- `date.iso=1`: ISO-8601 date support.
- Format placeholders include `m`, `d`, `y`, `D`, `M`, `Y`, `a`, `A`, `b`, `B`, `v`, `V`, `h`, `n`, `s`, `H`, `N`, `S`, `J`, `j`, and `w`. `v`, `V`, `a`, and `A` are display-only.
- Missing date fields are inferred from minimal valid values when another global date field exists, otherwise from `now`.

## Calendar

- `weekstart=Sunday`: `Sunday` or `Monday`.
- `displayweeknumber=1`: show calendar week numbers.
- `due=7`: days ahead that count as due and affect coloring / `+DUE`.
- `calendar.details=sparse`: `full`, `sparse`, or `none` task detail display in calendars.
- `calendar.details.report=list`: report used for detailed calendar task listings.
- `calendar.offset=0`, `calendar.offset.value=-1`: shift first calendar month.
- `calendar.holidays=none`: `full`, `sparse`, or `none` holiday display.
- `calendar.legend=1`: show calendar legend.
- `calendar.monthsperline=N`: requested months per row; Taskwarrior caps to what fits.

## Journal, Holidays, Dependencies, And Recurrence

- `journal.time=0`: record annotations when `start` and `stop` run.
- `journal.time.start.annotation=Started task`, `journal.time.stop.annotation=Stopped task`: text for journal annotations.
- `journal.info=1`: `information` shows task change log.
- Holidays can be direct entries or included files. Single-day: `holiday.<name>.name` plus `holiday.<name>.date`. Ranges: `holiday.<name>.start` and `.end`.
- Computed holiday date keywords include `goodfriday`, `easter`, `eastermonday`, `ascension`, and `pentecost`.
- `dependency.reminder=1`: dependency-chain violation reminders.
- `dependency.confirmation=1`: confirmation for dependency repair.
- `recurrence=1`: recurring task generation. With multiple sync clients, upstream guidance is primary client `recurrence=1`, other clients `recurrence=0`.
- `recurrence.confirmation=prompt`: `yes`, `no`, or `prompt` propagation of recurring task changes.
- `recurrence.indicator=R`: recurrence column indicator.
- `recurrence.limit=1`: number of future recurring instances shown in reports.

## Colors

For exact color syntax, previews, rule precedence examples, and themes, read `color-themes.md`.

- `color=1`: enable color; when disabled, headings use ASCII dashes.
- `fontunderline=1`: use terminal underline rather than ASCII underlines.
- Use `task colors` to inspect supported colors.
- Disable a default color rule by setting it blank, for example `color.tagged=`.
- `rule.color.merge=1`: whether color rules blend.
- `rule.precedence.color=...`: precedence list for color rules.
- General task state rules include `color.due.today`, `color.active`, `color.scheduled`, `color.until`, `color.blocking`, `color.blocked`, `color.overdue`, `color.due`, `color.project.none`, `color.tag.none`, `color.tagged`, `color.recurring`, `color.completed`, and `color.deleted`.
- Scoped rules: `color.tag.X`, `color.project.X`, `color.keyword.X`, `color.uda.X`, `color.uda.X.VALUE`, and `color.uda.X.none`.
- Message/report rules include `color.error`, `color.warning`, `color.header`, `color.footnote`, `color.label`, `color.label.sort`, and `color.alternate`.
- Calendar rules include `color.calendar.today`, `.due`, `.due.today`, `.overdue`, `.scheduled`, `.weekend`, `.holiday`, and `.weeknumber`.
- Graph/sync/debug rules include `color.summary.bar`, `color.summary.background`, `color.history.add`, `.done`, `.delete`, `color.burndown.pending`, `.started`, `.done`, `color.sync.added`, `.changed`, `.rejected`, and `color.debug`.
- `color.undo.before` and `color.undo.after` are listed by `taskrc(5)` as currently unsupported.
- For exact color syntax, use `task-color(5)`.

## Urgency

Urgency is a weighted polynomial. Change coefficients only when the workflow intentionally needs different ranking.

- Built-in coefficients: `urgency.blocking.coefficient`, `.blocked`, `.due`, `.waiting`, `.active`, `.scheduled`, `.project`, `.tags`, `.annotations`, and `.age`.
- Built-in defaults: due `12.0`, blocking `8.0`, scheduled `5.0`, active `4.0`, age `2.0` (capped at `age.max=365` days), project/tags/annotations `1.0` each, waiting `-3.0`, blocked `-5.0`, next `15.0`. Recover any value at runtime with `task show urgency`.
- `urgency.age.max=365`: age stops increasing urgency after this many days.
- Priority is a built-in UDA, so its urgency is configured under `urgency.uda.priority.<H|M|L>.coefficient` (defaults H `6.0`, M `3.9`, L `1.8`). There is NO `urgency.priority.*` key — writing one is silently ignored (no error, urgency unchanged). To re-weight priority use the `urgency.uda.priority.*` path.
- User-specific coefficients: `urgency.user.tag.<tag>.coefficient`, `urgency.user.project.<project>.coefficient`, `urgency.user.keyword.<keyword>.coefficient`.
- UDA urgency: `urgency.uda.<name>.coefficient` and `urgency.uda.<name>.<value>.coefficient`.
- `urgency.user.tag.next.coefficient=15.0`: default special urgency for `+next`.
- `urgency.inherit=0`: blocking tasks inherit highest urgency of blocked tasks when enabled; upstream recommends setting blocking/blocked coefficients to `0.0` if using this.

## Defaults

- `default.project=<project>`: default project for `task add`.
- `default.due=<date-or-duration>`: default due date for `task add`.
- `default.scheduled=<date-or-duration>`: default scheduled date for `task add`.
- `uda.<name>.default=...`: default UDA value for `task add`.
- `default.command=next`: command run when `task` has no arguments. It can include filters and report names.
- `task _config`/`task show`/`_get` enumerate only keys with a compiled-in default OR a currently-set value. `default.project`, `default.due`, `default.scheduled`, `uda.<name>.default`, `report.X.*`, and user urgency coefficients are absent until set, and `task show default.project` returns "No matching configuration variables." (exit 0). Do not read absence from `_config` as "unsupported" or "definitely unset" — query the exact key, and check the active taskrc plus included files (an include can define it).

## Reports

Custom reports are configured with `report.X.*`; report names become commands.

- `report.X.description`: help text.
- `report.X.columns`: comma-separated columns and format specifiers; use `task columns`.
- `report.X.context`: whether the active context applies to the report.
- `report.X.labels`: comma-separated labels.
- `report.X.sort`: sort columns with `+`/`-`; optional `/` creates grouping breaks. Special values: `none`, `random`.
- `report.X.filter`: report filter. `report.timesheet.filter` is a special case even though `timesheet` is otherwise not very customizable; `default.timesheet.filter` sets the default filter for the `timesheet [<weeks>]` report.
- `report.X.dateformat`: report-specific date format.
- `report.X.annotations`: deprecated; use description column formats such as `description.count`.
- Predefined reports listed in `taskrc(5)` include `next`, `long`, `list`, `ls`, `minimal`, `newest`, `oldest`, `overdue`, `active`, `completed`, `recurring`, `waiting`, `all`, and `blocked`.

## User Defined Attributes

UDAs define new stored attributes. Taskwarrior stores, filters, sorts, and reports them, but does not know their business meaning.

- `uda.<name>.type=string|numeric|uuid|date|duration`: define the UDA type.
- `uda.<name>.label=<column heading>`: default report label.
- `uda.<name>.values=A,B,C`: allowed string values and sort order. Blank value is allowed when included.
- `uda.<name>.default=...`: default value.
- `uda.<name>.indicator=U`: indicator string.
- UDA values can also have urgency and color config.

Example:

```text
uda.estimate.type=string
uda.estimate.label=Size Estimate
uda.estimate.values=huge,large,medium,small,trivial,
```

## Context

- `context=<name>`: active context.
- `context.<name>.read=<filter>`: read/report filter for the context.
- `context.<name>.write=<modifications>`: write modifications applied to new tasks under the context.
- `context.<name>.rc.<key>=<value>`: per-context override for any config key.
- Complex read filters often do not map safely to write modifications; set write context explicitly.

## Sync

`taskrc(5)` marks sync settings as the area used to connect and synchronize tasks. Use `sync-configuration.md` and `config-storage-sync.md` before editing sync configuration, credentials, replica identity, or backend settings.
