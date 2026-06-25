---
name: taskwarrior
description: Manage and explain Taskwarrior usage directly with the Taskwarrior CLI, grounded in the official Taskwarrior documentation. Use when capturing, triaging, listing, prioritizing, tagging, annotating, scheduling, sequencing, filtering, reporting, configuring, syncing, importing/exporting, writing hooks, integrating tools, troubleshooting, or explaining Taskwarrior concepts, commands, task data, contexts, reports, configuration, and database-path choices. Prefer the user's configured Taskwarrior database unless explicit instructions specify an alternate TASKRC, TASKDATA, or rc.data.location override.
---

# Taskwarrior

Use the `task` CLI directly when the user wants to inspect or modify tasks. Treat Taskwarrior as the task system and prefer native commands, reports, filters, contexts, annotations, JSON export/import, hooks, sync, and configuration over sidecar TODO files or custom task stores.

## Core Rules

- Default to the user's configured Taskwarrior state: their active taskrc and its configured `data.location`.
- Do not create project-local task stores, snapshots, shadow files, or generated task mirrors unless explicitly requested.
- Do not touch the user's live task database or taskrc for conceptual questions unless real task/config state is relevant.
- Use `TASKRC`, `TASKDATA`, `rc:<path>`, or `rc.data.location=<path>` only for explicit alternate stores or isolated probes.
- Treat persistent config, imports, sync, hooks, `purge`, and broad writes as side-effectful. Get explicit user approval when the user did not already ask for that change.
- Prefer `task export` / filtered export for agent ingestion; summarize parsed results instead of pasting raw JSON or tables.
- Prefer ID or UUID filters for writes, verify important writes with `export`, `information`, or `count`, and never rely on exit code alone for user-visible state.
- In this non-interactive environment, prompt-driven commands may silently no-op. Before deletes, bulk writes, config writes, imports, or recovery work, read `references/agent-runtime-safety.md`.
- Do not run `task edit` non-interactively. Use `modify`, `annotate`, `denotate`, or a full export-edit-import round trip.
- Redact secrets, credential paths, server URLs, client IDs, local paths, and raw `task show` / `_show` / `diagnostics` output unless the user explicitly asks to see them.

## Reference Routing

Use `references/taskwarrior-reference.md` as the routing authority. It lists the focused references and the task shapes that should load each one.

For common capture, list, annotate, modify, start/stop, done/delete, and summary work, start with `references/quick-operations.md`. For exact command syntax, write edge cases, helper/DOM access, filtering/reporting, modeling, dates, contexts, taskrc, storage/sync, colors, hooks, TaskChampion internals, troubleshooting, or source audits, load only the matching focused reference from the routing guide.

Focused references: `quick-operations.md`, `agent-runtime-safety.md`, `commands-and-syntax.md`, `write-commands.md`, `helpers-dom.md`, `filters-search-reports.md`, `task-modeling.md`, `dates-and-scheduling.md`, `contexts.md`, `taskrc-configuration.md`, `config-storage-sync.md`, `sync-configuration.md`, `color-themes.md`, `hooks-integration.md`, `taskchampion-representation.md`, `troubleshooting-sources.md`, and `source-coverage.md`.

The reference layer condenses the official Taskwarrior docs at https://taskwarrior.org/docs/, local Taskwarrior 3.4.2 manpages, the JSON task-format RFC, and local CLI metadata.
