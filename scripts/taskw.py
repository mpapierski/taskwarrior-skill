#!/usr/bin/env python3
"""Repo-local Taskwarrior wrapper with YAML snapshot sync."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    raise SystemExit(
        "PyYAML is required in the active Python environment to use scripts/taskw.py."
    )


TASK_DIRNAME = ".taskwarrior"
TASKRC_NAME = "taskrc"
TASKS_FILE_NAME = "tasks.yaml"
DATA_DIRNAME = "data"


@dataclass(frozen=True)
class TaskPaths:
    repo_root: Path
    task_dir: Path
    taskrc: Path
    data_dir: Path
    tasks_file: Path


class SyncError(RuntimeError):
    """Raised when the wrapper cannot synchronize the YAML snapshot."""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Taskwarrior against a repo-local .taskwarrior store, importing "
            "from .taskwarrior/tasks.yaml before the command and exporting back after."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root that should contain .taskwarrior/. Defaults to git root or cwd.",
    )
    parser.add_argument(
        "--task-bin",
        default="task",
        help="Taskwarrior binary to execute. Defaults to 'task'.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Remove .taskwarrior/data before importing the YAML snapshot.",
    )
    parser.add_argument(
        "task_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to Taskwarrior. Use '--' before descriptions if needed.",
    )
    args = parser.parse_args(argv)
    if args.task_args and args.task_args[0] == "--":
        args.task_args = args.task_args[1:]
    return args


def discover_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def ensure_layout(repo_root: Path, rebuild: bool) -> TaskPaths:
    task_dir = repo_root / TASK_DIRNAME
    taskrc = task_dir / TASKRC_NAME
    data_dir = task_dir / DATA_DIRNAME
    tasks_file = task_dir / TASKS_FILE_NAME

    task_dir.mkdir(parents=True, exist_ok=True)
    if rebuild and data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    if not taskrc.exists():
        taskrc.write_text(
            "# Repo-local Taskwarrior config.\n"
            "# scripts/taskw.py owns rc.data.location at runtime.\n"
        )

    return TaskPaths(
        repo_root=repo_root,
        task_dir=task_dir,
        taskrc=taskrc,
        data_dir=data_dir,
        tasks_file=tasks_file,
    )


def base_command(task_bin: str, paths: TaskPaths, *extra_rc: str) -> list[str]:
    command = [
        task_bin,
        f"rc:{paths.taskrc}",
        "rc.verbose=0",
        f"rc.data.location={paths.data_dir}",
        "rc.confirmation=off",
        "rc.bulk=0",
        "rc.allow.empty.filter=0",
        "rc.recurrence.confirmation=no",
    ]
    command.extend(extra_rc)
    return command


def run_task(
    task_bin: str,
    paths: TaskPaths,
    task_args: list[str],
    *,
    capture_output: bool,
    extra_rc: list[str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = base_command(task_bin, paths, *(extra_rc or []))
    command.extend(task_args)
    try:
        return subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=capture_output,
            input=input_text,
        )
    except FileNotFoundError as exc:
        raise SyncError(f"Taskwarrior binary not found: {task_bin}") from exc


def yaml_to_json_text(yaml_text: str) -> str:
    data = yaml.safe_load(yaml_text) if yaml_text.strip() else []
    return json.dumps(data or [])


def json_to_yaml_text(json_text: str) -> str:
    data = json.loads(json_text)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def import_snapshot(task_bin: str, paths: TaskPaths) -> None:
    if not paths.tasks_file.exists() or paths.tasks_file.stat().st_size == 0:
        return

    json_text = yaml_to_json_text(paths.tasks_file.read_text())
    result = run_task(
        task_bin,
        paths,
        ["import", "-"],
        capture_output=True,
        extra_rc=["rc.verbose=nothing", "rc.hooks=off"],
        input_text=json_text,
    )
    if result.returncode != 0:
        raise SyncError(
            f"Failed to import snapshot {paths.tasks_file}:\n{result.stderr or result.stdout}"
        )


def export_snapshot(task_bin: str, paths: TaskPaths) -> None:
    result = run_task(
        task_bin,
        paths,
        ["export"],
        capture_output=True,
        extra_rc=["rc.verbose=nothing", "rc.json.array=1", "rc.hooks=off"],
    )
    if result.returncode != 0:
        raise SyncError(
            f"Failed to export snapshot to {paths.tasks_file}:\n{result.stderr or result.stdout}"
        )

    paths.tasks_file.write_text(json_to_yaml_text(result.stdout))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = args.repo_root.resolve() if args.repo_root else discover_repo_root(Path.cwd())
    paths = ensure_layout(repo_root, rebuild=args.rebuild)

    try:
        import_snapshot(args.task_bin, paths)
        result = run_task(
            args.task_bin,
            paths,
            args.task_args,
            capture_output=False,
        )
        if result.returncode == 0:
            export_snapshot(args.task_bin, paths)
        return result.returncode
    except SyncError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
