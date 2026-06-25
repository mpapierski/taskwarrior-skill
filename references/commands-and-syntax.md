# Commands And Syntax

Use this file for Taskwarrior command shape, command categories, abbreviation, shell escaping, temporary overrides, aliases, and read command selection. Use `write-commands.md` for write-specific behavior and `helpers-dom.md` for DOM/helper metadata access.

## Table Of Contents

- Command shape
- Command abbreviation
- Command categories
- Read command notes
- Description and shell escaping
- Overrides
- Aliases and external execution
- Unicode

## Command Shape

Taskwarrior command lines have four logical parts:

```text
task [<filter>] <command> [<mods>] [<misc>]
```

- `command`: the first exact or abbreviated command Taskwarrior recognizes. Emit full command names.
- `filter`: selects tasks. It usually appears before the command.
- `mods`: changes to apply, usually after write commands.
- `misc`: command-specific arguments for commands like `show`, `config`, `columns`, or `calc`.
- Overrides such as `rc.confirmation=off` are handled before the command and may appear anywhere.
- If no command is specified, Taskwarrior runs `rc.default.command`.

Examples:

```bash
task list
task +home list
task 12 modify project:Garden
task show editor
task rc.verbose=0 project:Repo export
```

## Command Abbreviation

- Taskwarrior accepts command prefixes and may silently resolve even non-unique-looking prefixes by internal precedence.
- Prefer full command names in generated commands. Abbreviations are convenient for humans but brittle in docs and automation.
- `abbreviation.minimum` can require longer command prefixes, for example `task config abbreviation.minimum 3`.

## Command Categories

Read/report commands:

```text
next ready list ls minimal long all active waiting overdue blocked blocking
unblocked completed recurring newest oldest summary calendar timesheet
history.* ghistory.* burndown.* count ids uuids projects tags stats information
```

Write/data commands:

```text
add log modify done delete purge annotate denotate append prepend duplicate
start stop undo import import-v2 synchronize sync
```

Config/help/misc commands:

```text
show config context reports columns udas commands help diagnostics calc colors
logo news execute version
```

For agents, prefer `task export` and `count` over scraping formatted reports.

## Read Command Notes

- `calendar [due|<month> <year>|<year>] [y]`: show a calendar; `due` selects due tasks, `y` adds yearly display.
- `timesheet [<weeks>]`: weekly report of tasks completed and started; scope with `report.timesheet.filter` / `default.timesheet.filter`.
- `ids` / `uuids`: emit current task IDs or UUIDs for a filter. Prefer UUIDs outside the current terminal context.
- `information`: show all task data and metadata, including change history.
- `udas`: show defined UDAs, including name, type, label, allowed values, usage, and orphan UDAs.
- `calc <expression>`: evaluate an expression and inspect date/arithmetic parsing.
- `version`: show Taskwarrior version details as a normal command.
- `news`: interactive, blocking multi-page walkthrough; do not run non-interactively unless the user explicitly asks and a TTY is available.
- `tags`: lists stored tags, not virtual tags.
- `count`: count matching tasks and reports; exits 0 and prints `0` for no matches.

For no-match behavior and export guidance, use `filters-search-reports.md`.

## Description And Shell Escaping

- Quote descriptions with spaces.
- Quote filters containing parentheses or shell operators.
- Escape or quote special shell characters such as `(`, `)`, `!`, `*`, `$`, `;`, `&`, `|`, `<`, and `>`.
- Quote projects or tags containing spaces; prefer avoiding spaces in project and tag names.
- Use `--` when description text starts with metadata-like tokens.

Examples:

```bash
task '(project:Home or project:Garden)' list
task '/foo bar/' list
task add "Review Q3 plan" project:'Work Planning'
task add -- project:Home needs scheduling
```

For write-time description parsing hazards, use `write-commands.md`.

## Overrides

Use command-line overrides for temporary behavior:

```bash
task rc.verbose=0 export
task rc.verbose:0 export
task rc.confirmation=off rc.bulk=0 12 delete
task rc:/path/to/taskrc rc.data.location=/path/to/data next
```

Do not persist overrides with `task config` unless the user asked for lasting configuration changes.

`task --version` is the conventional option form intended for add-on scripts that need version detection without creating default files. For normal interactive use, `task version` is also available.

## Aliases And External Execution

- Prefer full built-in command names in generated commands.
- Taskwarrior aliases are persistent config entries such as `alias.rm=delete`; inspect them with `task show alias` when an unknown command or user workflow may depend on aliases.
- Common default aliases include `burndown`, `ghistory`, `history`, and `rm`, but user aliases can differ.
- Treat `execute` and unknown aliases/extensions as side-effectful external command execution. Do not run them unless the user explicitly asks for that integration behavior.
- Do not create or modify `alias.<name>` config unless the user wants a persistent alias.

## Unicode

Taskwarrior supports Unicode descriptions and metadata when the terminal, locale, and fonts support them. Preserve user text when present, but prefer ASCII for generated examples unless non-ASCII text is required.
