# Source Coverage Map

Use this file when auditing the skill against official Taskwarrior docs, local manpages, RFCs, and CLI metadata. It is a coverage checklist, not a user tutorial.

## Primary Sources

- Official docs index: https://taskwarrior.org/docs/
- Local CLI/manpage baseline: Taskwarrior 3.4.2 (`task --version`, `man task`, `man taskrc`, `man task-color`, `man task-sync`)
- JSON task format RFC: `doc/devel/rfcs/task.md`
- TaskChampion representation docs: https://taskwarrior.org/docs/task/
- Local metadata helpers: `task _commands`, `task _config`, `task columns`, `task reports`, `task _show`, `task diagnostics`
- Local audit helper: `scripts/audit-taskwarrior-coverage.py` for metadata smoke coverage only.

## Coverage Checklist

| Source area | Skill reference |
| --- | --- |
| Getting started, introduction, 30-second tutorial, help, best practices, examples, workflow, philosophy, review | `getting-started.md`, `quick-operations.md`, `SKILL.md` |
| CLI grammar, command categories, abbreviation, shell escaping, aliases | `commands-and-syntax.md` |
| Write commands, write output, descriptions, import, purge, non-interactive safety | `write-commands.md`, `agent-runtime-safety.md` |
| DOM access, helpers, sensitive metadata commands | `helpers-dom.md` |
| Commands and `task(1)` command semantics | `commands-and-syntax.md`, `write-commands.md`, `task-modeling.md` |
| Filters, search, modifiers, expressions, report behavior, report customization | `filters-search-reports.md` |
| Context commands, context read/write behavior, context troubleshooting | `contexts.md`, `config-storage-sync.md` |
| Attributes, IDs/UUIDs, projects, tags, priority, urgency, recurrence, dependencies, annotations, UDAs | `task-modeling.md`, `taskrc-configuration.md` |
| Dates, named dates, durations, date filtering, due/scheduled/wait/until modeling | `dates-and-scheduling.md`, `task-modeling.md`, `taskrc-configuration.md` |
| Taskrc syntax, includes, precedence, config variable families | `taskrc-configuration.md` |
| Database path selection, storage movement, upgrade, safe probes, high-level sync cautions | `config-storage-sync.md` |
| Syncing tasks, `task-sync(5)`, sync backends, encryption, local sync, recurring sync cautions | `sync-configuration.md` |
| Color controls, color syntax, color rules, themes, `task-color(5)` | `color-themes.md`, `taskrc-configuration.md` |
| Hooks v1/v2, hook authoring, third-party app rules | `hooks-integration.md` |
| JSON import/export RFC | `hooks-integration.md` |
| TaskChampion task representation and atomicity | `taskchampion-representation.md` |
| Deprecated features, pitfalls, diagnostics, bug/feature request guidance | `troubleshooting-sources.md` |

## Audit Procedure

1. Run `task --version` and note the local Taskwarrior version.
2. Compare `task _commands`, `task _config`, `task reports`, and `task columns` against the reference files for missing user-facing behavior.
3. Compare official docs index categories against the checklist above.
4. For each missing topic, either add a compact note to an existing reference or create a focused reference, then register its task-shaped selection rule in `taskwarrior-reference.md`.
5. Keep generated docs concise. Prefer source maps and routing over copying upstream manuals.
6. Run `scripts/audit-taskwarrior-coverage.py` for a local metadata drift smoke report. A clean run means referenced command/report/column/config-family names are mentioned somewhere; it does not prove the guidance is semantically correct.
7. Validate with `python3 scripts/audit-taskwarrior-coverage.py --strict` and `git diff --check`. Both are concrete pass/fail checks; do not add validation steps that name no runnable command or success criterion.
