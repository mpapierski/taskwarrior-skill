# Taskwarrior Reference Selection Guide

Use this file as the routing authority. Load the smallest reference that matches the user's task, and avoid loading broad modeling/config docs for routine operations.

## Fast Load Profiles

- Routine capture, list, annotate, modify, start/stop, done/delete, and light triage: `quick-operations.md`.
- Any delete, bulk write, config write, import, sync, hook change, recovery, alternate taskrc/data path, or "why did this no-op?" task: `agent-runtime-safety.md` plus the topic reference.
- Exact command construction, quoting, abbreviations, aliases, and read command selection: `commands-and-syntax.md`.
- Write command semantics, description parsing, import, purge, write output, and verification: `write-commands.md`.
- DOM, helper commands, `_get`, `_show`, `_unique`, diagnostics, and sensitive metadata access: `helpers-dom.md`.

## Topic Routing

- First-use guidance, help, diagnostics, workflows, Tasksh review, and philosophy: `getting-started.md`.
- Filters, search, modifiers, expressions, report behavior, custom reports, columns, sorting, and export summaries: `filters-search-reports.md`.
- Task attributes, IDs/UUIDs, projects, tags, priority/urgency, recurrence, dependencies, annotations, UDAs, and JSON task shape: `task-modeling.md`.
- Date parsing, exact dates, named dates, durations, relative expressions, `task calc`, due/scheduled/wait/until behavior, and date-sensitive modeling: `dates-and-scheduling.md`.
- Context commands, active context inspection, read/write filters, context-aware commands, and global-scope troubleshooting: `contexts.md`.
- `.taskrc`, `taskrc(5)`, config syntax, includes, defaults, variable families, reports, urgency coefficients, and "what setting controls X?": `taskrc-configuration.md`.
- Database paths, read-only errors, storage movement, Taskwarrior 3 upgrade/import, verbosity, and high-level sync cautions: `config-storage-sync.md`.
- Sync servers, encryption secrets, cloud/object storage sync, local sync, replica setup, and TaskChampion sync server behavior: `sync-configuration.md`.
- Color syntax, `_forcecolor`, color rules, color precedence, themes, and `task-color(5)`: `color-themes.md`.
- TaskChampion internal key/value task representation, operations log, atomicity, sync-safe update patterns, and integration UDA namespacing: `taskchampion-representation.md`.
- Hooks v1/v2, hook authoring, external scripts, third-party apps, JSON import/export, and integration safety: `hooks-integration.md`.
- Diagnostics, pitfalls, deprecated behavior, support requests, local version notes, and unclear errors: `troubleshooting-sources.md`.
- Coverage audits against official docs, manpages, RFCs, and local CLI metadata: `source-coverage.md`.

## Baseline

This skill was refreshed against the official Taskwarrior documentation index and local Taskwarrior `3.4.2` command metadata.
