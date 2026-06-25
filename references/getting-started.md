# Getting Started, Workflow, And Help

Use this file for onboarding, routine usage advice, best practices, workflow design, help, and community/support questions.

## First Use

- Run `task` directly; the normal entrypoint is `task <filter> <command> <mods>`.
- A non-interactive `task` against a fresh/missing config does NOT prompt or auto-create anything: it prints `Cannot proceed without rc file.` and exits 2. Neither piping `yes` nor `rc.confirmation=off` bypasses this (the create-config prompt only fires on a real TTY).
- To bootstrap an explicitly-requested alternate or throwaway store, create the rc file first, then `add`/`list` work and exit 0:

  ```bash
  touch "$TASKRC"   # or write a minimal taskrc
  task add "first task"
  ```

- Never silently create rc files in the user's environment; only bootstrap a store the user asked for.
- Do not create project-local stores unless the user explicitly asks for one.
- Start with a few concrete tasks, then use reports to learn how the list behaves.

Minimal flow:

```bash
task add "Read Taskwarrior docs" project:Learning
task add "Pay rent" due:eom priority:H +finance
task list
task next
task 1 done
```

## Working Habits

- Keep descriptions short. Treat them as titles.
- Use projects for areas or workstreams and dotted subprojects when useful.
- Use tags for cross-cutting labels.
- Use annotations for details, links, acceptance criteria, blockers, decisions, and notes.
- Use `due` only for real deadlines.
- Use `scheduled` for "not before".
- Use `wait` for tasks that should disappear until later.
- Use `start` and `stop` to show active focus.
- Review the list regularly with `next`, `ready`, `waiting`, `overdue`, `summary`, `projects`, and `tags`.

## Fast Command Examples

```bash
task add "Write release notes" project:Repo.Release priority:H +docs
task add "Call bank" due:friday +phone
task 4 annotate "Blocked until API schema is approved."
task 4 modify project:Repo.Backlog +blocked wait:tomorrow
task 4 start
task 4 stop
task 4 done
task project:Repo ready
task +blocked waiting
task summary
```

## Best Practices For Agents

- Query first, then write. Use `task export` for machine-readable inspection.
- Prefer exact ID or UUID filters for writes.
- Count or export a broad filter before modifying it.
- Summarize results in readable prose unless the user asks for raw output.
- Do not hide uncertain choices in task metadata; ask or annotate.
- Use annotations instead of long descriptions.
- Do not maintain parallel TODO files unless the repo explicitly requires them.
- To mark the single "do this next" task, add `+next` (largest default urgency coefficient, 15.0); it ranks first across urgency-sorted reports. Prefer it over priority bumps for "do this next".
- Decompose broad or multi-step goals into several smaller, individually-completable tasks instead of one giant task that never progresses. Group them under a shared dotted project and add `depends:` where order matters.

## Review Workflows

- Use `task next` for ranked work.
- Use `task ready` for actionable work not blocked or waiting.
- Use `task waiting` for deferred items.
- Use `task overdue` and `task +TODAY list` for date pressure.
- Use `task summary` for project status and `task projects` for project inventory.
- Tasksh review workflows can help with manual periodic review, but the core skill should keep using `task` unless the user explicitly wants Tasksh.

Review is a triage pass, not just listing. Surface decision-needing tasks cheaply, then propose a concrete action for each:

```bash
task +OVERDUE export       # overdue: reschedule or re-prioritize
task +WAITING export       # waiting expired or near: act or re-defer
task project: export       # unprojected/orphaned: assign a project or re-tag
task +PENDING export       # stale by modified date: correct or prune
```

- For each, propose correct/re-tag/re-prioritize, reschedule, or `task <uuid> delete` for now-irrelevant items.
- Require user confirmation before any delete or bulk write (see `agent-runtime-safety.md`).

## Tasksh Review

If the user explicitly asks about Tasksh review, explain that `tasksh review` is an interactive periodic review flow outside the normal `task` CLI. It configures a `_reviewed` report and a `reviewed` timestamp UDA so reviewed tasks are skipped until the review interval passes. Treat first-time Tasksh review setup as persistent config and ask before running it for the user.

## Help And Diagnostics

- `task help`: general CLI help.
- `task commands`: command inventory and command behavior flags.
- `task reports`: report inventory.
- `task columns`: reportable columns and formats.
- `task show`: configuration.
- `task diagnostics`: installation, config, data, hook, and environment diagnostics. On Taskwarrior 3.4.2 this may touch the configured database, so use an isolated store when probing an unhealthy setup.
- `man task`, `man taskrc`, `man task-color`, `man task-sync`: local manual pages.

Treat `task show`, `task _show`, and `task diagnostics` as potentially sensitive. Query only needed settings and redact secrets, credential paths, server URLs, client IDs, and local paths before reporting output.

Isolated probe:

```bash
mkdir -p /tmp/task-probe
task rc:/dev/null rc.data.location=/tmp/task-probe diagnostics
```

## Philosophy

- Treat Taskwarrior as a flexible toolkit, not a forced methodology.
- Keep friction low: fast capture, later refinement.
- Review is not just listing; it is correcting stale data and pruning irrelevant tasks.
- Prefer native Taskwarrior features before inventing side files or custom task stores.
- Keep data open through JSON export/import and documented configuration.
- Be cautious with persistent config and storage changes because they affect the user's real task system.
