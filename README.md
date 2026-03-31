# Taskwarrior Skill

This repo is a Codex skill for managing tasks with Taskwarrior instead of maintaining a handwritten `TODO.md`.

## Repo-local task data

The wrapper stores repo-local state under `.taskwarrior/`:

- `.taskwarrior/data/` contains the Taskwarrior SQLite database and related local artifacts.
- `.taskwarrior/tasks.yaml` is the versionable YAML task snapshot used for import and export.

Ignore `.taskwarrior/data/` in git. It contains binary or machine-local state and should not be treated as source.

Prefer versioning `.taskwarrior/tasks.yaml` when you want the task list itself to be shareable or reviewable in version control.

If repo-local contexts or report configuration matter to the team, consider whether `.taskwarrior/taskrc` should also be versioned.

## Task shape

Keep task descriptions short. Put richer context into Taskwarrior annotations.

Typical annotation content:

- goals
- acceptance criteria
- blockers
- implementation notes
- links or references

## Machine-readable task views

When tooling or an agent needs to ingest task lists, prefer live JSON exports from Taskwarrior instead of parsing formatted reports.

Examples:

```bash
python scripts/taskw.py export
python scripts/taskw.py export ready
python scripts/taskw.py export next
python scripts/taskw.py rc.json.array=0 export ready
```

Use `python scripts/taskw.py export` as the default "current tasks" query for machine consumption.

That JSON is an internal ingestion format. User-facing answers should summarize the tasks in readable text rather than dumping raw JSON or a raw terminal table, unless the user explicitly asks for the raw output.
