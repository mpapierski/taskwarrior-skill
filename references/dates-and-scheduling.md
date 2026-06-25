# Dates And Scheduling

Use this file for Taskwarrior date parsing, date-sensitive task modeling, due/scheduled/wait/until behavior, durations, named dates, relative expressions, and `task calc`.

## Table Of Contents

- Date semantics
- Exact dates and times
- Timezone dependence
- Named dates
- Durations
- Relative and DOM-based dates
- Filtering dates
- Recurrence dates
- Agent guidance

## Date Semantics

- `due`: the deadline or commitment date.
- `scheduled`: the earliest sensible start date; once reached, the task can become `+READY`. A `scheduled` date in the FUTURE excludes the task from `+READY` (and from the `ready`/`next`-style queries this skill recommends) until that date passes; this is the point of using `scheduled` to defer planned work. The default `next`/`list` reports still show it — only `+READY`-filtered queries hide it. The `+SCHEDULED` virtual tag matches any task with a `scheduled` date, past or future.
- `wait`: hide the task from normal pending reports until the wait date passes.
- `until`: auto-expiration date; use sparingly. Evaluated lazily: the task is set to `status:deleted` the next time a processing command (list/export/report, not a read-only `_get`) runs after the until date, not at the exact timestamp. The expired task is a normal deleted task — still in the DB and recoverable via `task <uuid> modify status:pending until:` (you MUST also clear or advance the past `until`; `modify status:pending` alone reports success but the task is re-expired to `deleted` on the next processing run), and visible in `task all` / `+DELETED export` until `task purge` removes it. Do not rely on precise auto-deletion timing.
- `entry`, `modified`, `start`, and `end`: lifecycle metadata. Do not set these unless the user is importing or repairing data.

Prefer `scheduled` or `wait` for "not before" behavior. Use `due` only for real deadlines.

## Exact Dates And Times

Default date input is controlled by `dateformat`, commonly `Y-M-D`:

```bash
task add "Renew cert" due:2026-07-01
task 12 modify due:
```

If `dateformat` omits time, Taskwarrior stores midnight for entered dates. ISO-8601 datetime input — `YYYY-MM-DDThh:mm:ss`, with an optional trailing `Z` for UTC — parses out of the box regardless of `dateformat` and captures the time. Prefer this `T` form for exact times:

```bash
task add "Open store" due:2026-07-01T08:30:00
task add "Deployment freeze" due:2026-07-01T18:00:00Z
```

Only space-separated time input needs a format override: with a date-only `dateformat` (e.g. default `Y-M-D`), `due:"2026-07-01 08:30:00"` silently drops the time and stores midnight; fix that specific case with `rc.dateformat:"Y-M-D H:N:S"`.

Input parsing uses `dateformat` (default `Y-M-D`); report date DISPLAY follows a separate precedence — `report.X.dateformat`, then `dateformat.report`, then `dateformat` — which is why a report can show only the date for a task you set with a `T`-time. For these and other date/calendar config keys (`date.iso`, ISO-8601 date support, default on; `weekstart`; `displayweeknumber`; `due`), read `taskrc-configuration.md` (Dates and Calendar sections).

Use absolute dates when the user uses relative language in a date-sensitive request. Include the resolved date in the final answer when it matters.

## Timezone Dependence

- Named and relative dates (`now`, `today`, `tomorrow`, `eod`, `eom`, durations) are computed in the running process timezone (`$TZ`); stored values are UTC. The same instant gives different calendar days across zones, e.g. `TZ=Pacific/Kiritimati task calc now` -> `2026-06-18` while `TZ=Pacific/Midway task calc now` -> `2026-06-17`.
- An agent process often runs in UTC or a server timezone that differs from the user's locale, so `due:today`/`due:tomorrow`/`due:eod` can silently land on the wrong day or hour. For example `TZ=Asia/Tokyo task add x due:today` stores `due:20260617T150000Z` (Tokyo midnight).
- For reliability: ensure the process `$TZ` matches the user's locale, or prefer explicit absolute datetimes (e.g. `due:2026-07-01T18:00:00Z`) for real deadlines, and verify the stored UTC value with `task <id> export` when the exact day or hour matters.

## Named Dates

Common named dates:

```text
now today tomorrow yesterday
eod eow eom eoq eoy
sod sow som soq soy
soww eoww
later someday
monday tuesday ... sunday
january february ... december
1st 2nd 3rd ...
goodfriday easter eastermonday ascension pentecost midsommar midsommarafton juhannus
```

Most weekday and month names can be abbreviated. Next/previous variants can be useful, for example `sonw` for start of next week and `sopw` for start of previous week. `man task` also lists `socw`/`eocw` (start/end of calendar week), but these are not recognized in 3.4.2 — prefer `sow`/`eow`, which resolve. `weekstart` affects only calendar display, not `sow`/`eow` parsing.

Use `task calc` to confirm ambiguous expressions:

```bash
task calc tomorrow
task calc eom
task calc 'eom - 1wk'
```

`task calc` echoes an unrecognized token back verbatim with exit code 0 (e.g. `task calc socw` prints `socw`), so confirm the output actually looks like a date rather than trusting the exit code. In `task add`/`modify`, an unrecognized date form fails loudly instead — `due:socw` exits 2 with `'socw' is not a valid date`.

## Durations

Durations can be used where dates are expected and are interpreted relative to now or an anchor expression:

```bash
task add "Follow up" wait:3days
task add "Submit report" due:2wks
task calc 'today + P3D'
```

Always prefix a count: `due:1q`, `wait:2h`, `scheduled:3days`. The bare single-letter abbreviations `s`, `h`, `q` are NOT parsed as durations (a leading number is required) — `due:h` exits 2, and `task calc 'now + h'` echoes the literal `h` back; multi-letter or spelled forms like `min`, `day`, `wk`, `mo`, `qtr`, `yr` happen to work bare, but the count form is unambiguous and always safe. Named periods such as `daily`, `weekdays`, `weekly`, `biweekly`, `monthly`, `quarterly`, `semiannual`, and `annual` are also available (mainly for `recur`).

Month, quarter, and year durations are calendar-relative and can be imprecise unless anchored to an exact date. Prefer exact dates for contractual deadlines.

## Relative And DOM-Based Dates

Taskwarrior can evaluate relative expressions and DOM references in command-line values:

```bash
task add "Mail birthday card" due:2026-11-08 scheduled:due-4d wait:due-7d
task add "Fix leak" depends:3 scheduled:3.due
```

DOM-relative dates are evaluated when the command runs. If the anchor date later changes, related dates do not automatically update.

Use `task _get` to inspect date parts when needed:

```bash
task _get 12.due.year
task _get 12.due.week
task _get 12.annotations.1.entry  # annotations are 1-indexed; .0 returns empty
```

## Filtering Dates

Use date attributes, modifiers, or virtual tags:

```bash
task due:today list
task due.any: list
task due.none: list
task due.before:eom list
task due.by:eow list
task +TODAY list
task +OVERDUE export
```

`+DUE` means due within the configured `due` window, defaulting to 7 days. `+WAITING` tasks may require `task waiting`, `task all`, or a direct `+WAITING export` because normal pending reports exclude waiting tasks.

## Recurrence Dates

Recurring templates usually require `due` and `recur`:

```bash
task add "File weekly report" due:friday recur:weekly
task add "Pay rent" due:2026-07-01 recur:monthly until:2027-01-01
```

Use `until` on recurrence to end the series. Inspect recurring templates with `task recurring`, `task all`, or `task information`.

## Agent Guidance

- Use exact dates when user intent, timezone, or legal/business deadlines matter.
- Do not silently turn "someday" ideas into due dates; use `wait:someday`, a tag, or an annotation depending on user intent.
- Prefer `scheduled` for planned start dates and `wait` for hidden/deferred tasks.
- Warn before using `until` because it can auto-delete tasks.
- Use `task calc` in an isolated store or read-only context when testing date parsing for explanation.
