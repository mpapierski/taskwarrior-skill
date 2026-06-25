# Contexts

Use this file for Taskwarrior contexts: persistent default filters, context commands, read/write behavior, per-context config, and troubleshooting unexpectedly scoped task operations.

## Table Of Contents

- Core model
- Commands
- Read and write sides
- Context-aware commands
- Troubleshooting and global scope
- Context silently narrows broad writes

## Core Model

- A context is a named default filter stored in taskrc.
- The active context is stored in `context=<name>`.
- Context definitions use `context.<name>.read=<filter>` and `context.<name>.write=<mods>`.
- Per-context config can use `context.<name>.rc.<key>=<value>`.
- Taskwarrior wraps context filters in parentheses before combining them with command-line filters.
- Avoid the names `define`, `list`, `show`, `none`, `delete`. Only `list`, `show`, `none` are truly reserved (rejected at define time, exit 2); `define`/`delete` are accepted as context names but cannot be activated via `task context <name>` because the subcommand parser shadows them.

Use contexts when the user wants a persistent view such as work/home/study, not for one-off filters.

## Commands

```bash
task rc.confirmation=off context define work 'project:Work or +client'
task context work
task context show
task context list
task context none
task rc.confirmation=off context delete work
```

- `task context define <name> <filter>` creates or updates a context definition.
- `task context <name>` activates a defined context.
- `task context show` shows the active context and definition.
- `task context list` lists all defined contexts.
- `task context none` clears the active context.
- `task context delete <name>` removes a definition and clears it if active.

Mutating commands prompt under the default `confirmation=on`; run non-interactively they fail closed (see agent-runtime-safety.md). Always prefix them with `rc.confirmation=off`:

- `context define` prompts to add each `context.<name>.read`/`.write`; non-interactively it prints `Context ... not defined`/`Context definition aborted` and exits 2 (nothing created).
- `context delete` prompts; non-interactively it prints `Context ... not deleted` and exits 2 (still present).
- `config context.<name>.*` prompts; non-interactively it prints `No changes made` and exits **0** — a silent no-op an exit-code check will not catch. Verify with `task context list` or `task _get rc.context.<name>.write`, not the exit code.

`task context define` adds an extra leading prompt `The filter '...' matches 0 pending tasks. Do you wish to continue?` when the read filter matches no existing tasks (common on a first run / empty DB); it is skipped once the filter matches tasks. `rc.confirmation=off` is the single override that suppresses every one of these prompts — `rc.bulk` has no effect here. Use `rc.confirmation=off` regardless of DB state, since `define` prompts even when the filter matches tasks.

If `task context show` is not enough for automation, inspect the config values:

```bash
task show context
task show context.work
task _get rc.context
```

Redact taskrc paths and unrelated config if reporting output to the user.

## Read And Write Sides

Simple contexts can infer a write side:

```bash
task rc.confirmation=off context define home project:Home
task context home
task add "Replace kitchen light"
```

Complex read filters often do not map cleanly to new-task modifications. Set the write side explicitly:

```bash
task rc.confirmation=off context define family 'project:Family or +paul or +nancy'
task rc.confirmation=off config context.family.write project:Family
```

For a context-specific default report:

```bash
task rc.confirmation=off config context.family.rc.default.command ready
```

Use `task config` only when the user wants persistent context changes. For temporary scope, use explicit filters on the command line.

## Context-Aware Commands

Reports that accept task filters generally inherit the active context. Important context-aware commands include:

```text
add burndown count delete denotate done duplicate edit history log prepend
projects purge start stats stop summary tags
```

Every report (built-in AND custom) respects the active context by default, because `report.<name>.context` defaults to `1`. So `task list`, `task next`, `task ready`, `task waiting`, `task overdue`, etc. ARE context-scoped out of the box. A report ignores context ONLY when `report.<name>.context` is explicitly set to `0`.

`export`, `info`, and `modify` are NOT context-affected (they are absent from the list above). Among writes, `done`, `delete`, `start`, `stop`, `duplicate`, `purge`, `denotate`, and `prepend` ARE context-affected, but `modify` is not. So `task <filter> export`/`info` always operate globally, while `task <filter> done` is narrowed by the active context.

Miscellaneous and helper commands do not always inherit context. Pass explicit filters when the desired scope must be unambiguous.

## Troubleshooting And Global Scope

When reports, adds, or writes appear unexpectedly scoped:

1. Run `task context show`.
2. Inspect `task show context` and the relevant `context.<name>.*` settings.
3. Check whether `report.<name>.context` is explicitly set to `0` (for any report, built-in or custom) — that is the only way a report opts out of the active context.
4. Use `task context none` only if the user wants to clear the active context persistently.
5. For one command that should ignore context, prefer an explicit context override rather than changing the user's active context:

```bash
task rc.context= +PENDING count
task rc.context= +PENDING done
```

To APPLY a defined context for a single command without changing the user's active context, set it by name. This is the stateless/idempotent alternative to `task context <name>`, which mutates the persistent `context` setting:

```bash
task rc.context=home next
task rc.context=home add "Buy milk"
```

The read side scopes reports (use a context-aware command such as `next`/`list`, not `export`, which ignores context even when applied by name); the write side applies only to `add` (new tasks inherit the write modifications) — verified NOT to inject into `modify`.

### Context silently narrows broad writes

An active context is wrapped in parentheses and AND-ed onto every context-aware command's filter (`add`/`done`/`delete`/`start`/`stop`/`duplicate`/`count` and reports; `modify` is NOT affected). So a bulk write like `task +PENDING done` or `task +READY start` silently affects ONLY the in-context subset, even when the agent intends global scope.

`count` and the reports are context-aware too, so a preview run under the active context shows the SAME narrowed set as the write — it agrees with the narrowed write and hides the discrepancy. `export` and `info`, by contrast, IGNORE context, so previewing with `task <filter> export` then running `task <filter> done` acts on a different, smaller set than the preview showed.

To preview the EXACT set a context-affected write will touch, use a context-affected command (`count`, or the matching report) under the same context — or add the context's read filter to `export` explicitly.

For a globally-intended bulk write, run both the preview and the write with `rc.context=` (or `task context none` first):

```bash
task rc.context= +READY count
task rc.context= +READY done
```

Two non-blocking cases to watch: an explicit id/uuid write (`task 2 done`) is NOT blocked by context and WILL hit out-of-context tasks; and ids shown by `task list` under a context are still global ids with out-of-context ids hidden, so an agent reading ids under a context can mis-target.
