from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "taskw.py"
TASK_BIN = shutil.which("task")


@unittest.skipIf(TASK_BIN is None, "task binary is not installed")
@unittest.skipIf(yaml is None, "PyYAML is not installed in the active Python environment")
class TaskWrapperIntegrationTest(unittest.TestCase):
    def load_yaml(self, path: Path) -> object:
        return yaml.safe_load(path.read_text()) or []

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_wrapper(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(WRAPPER), *args]
        return subprocess.run(
            command,
            cwd=str(cwd or self.repo_root),
            text=True,
            capture_output=True,
            check=False,
        )

    def load_snapshot(self) -> list[dict[str, object]]:
        snapshot = self.repo_root / ".taskwarrior" / "tasks.yaml"
        self.assertTrue(snapshot.exists(), "expected .taskwarrior/tasks.yaml to exist")
        return self.load_yaml(snapshot)

    def test_add_creates_repo_local_snapshot(self) -> None:
        result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "add",
            "Write",
            "release",
            "notes",
            "project:Repo.Release",
            "priority:H",
            "+docs",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr.strip(), "")

        snapshot = self.load_snapshot()
        self.assertEqual(len(snapshot), 1)
        task = snapshot[0]
        self.assertEqual(task["description"], "Write release notes")
        self.assertEqual(task["project"], "Repo.Release")
        self.assertEqual(task["priority"], "H")
        self.assertEqual(task["status"], "pending")
        self.assertEqual(task["tags"], ["docs"])

        task_dir = self.repo_root / ".taskwarrior"
        self.assertTrue((task_dir / "taskrc").exists())
        self.assertTrue((task_dir / "data").exists())

    def test_modify_round_trips_without_duplicates(self) -> None:
        add_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "add",
            "Triage",
            "bug",
            "report",
            "project:Repo.Backlog",
        )
        self.assertEqual(add_result.returncode, 0, msg=add_result.stderr)

        modify_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "1",
            "modify",
            "priority:M",
            "+triaged",
        )
        self.assertEqual(modify_result.returncode, 0, msg=modify_result.stderr)

        count_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "project:Repo.Backlog",
            "count",
        )
        self.assertEqual(count_result.returncode, 0, msg=count_result.stderr)
        self.assertIn("1", count_result.stdout)

        snapshot = self.load_snapshot()
        self.assertEqual(len(snapshot), 1)
        task = snapshot[0]
        self.assertEqual(task["priority"], "M")
        self.assertEqual(task["tags"], ["triaged"])

    def test_export_ready_is_machine_readable(self) -> None:
        self.assertEqual(
            self.run_wrapper(
                "--repo-root",
                str(self.repo_root),
                "add",
                "Ready",
                "task",
                "project:Repo",
                "priority:H",
            ).returncode,
            0,
        )
        self.assertEqual(
            self.run_wrapper(
                "--repo-root",
                str(self.repo_root),
                "add",
                "Waiting",
                "task",
                "project:Repo",
                "wait:tomorrow",
            ).returncode,
            0,
        )

        export_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "export",
            "ready",
        )
        self.assertEqual(export_result.returncode, 0, msg=export_result.stderr)
        self.assertEqual(export_result.stderr.strip(), "")

        exported = json.loads(export_result.stdout)
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["description"], "Ready task")

    def test_imported_yaml_id_is_not_preserved_as_taskwarrior_local_id(self) -> None:
        task_dir = self.repo_root / ".taskwarrior"
        task_dir.mkdir()
        (task_dir / "taskrc").write_text("# test\n")
        (task_dir / "tasks.yaml").write_text(
            yaml.safe_dump(
                [
                    {
                        "id": 999,
                        "description": "Imported high id task",
                        "entry": "20260331T120000Z",
                        "modified": "20260331T120000Z",
                        "status": "pending",
                        "uuid": "99999999-1111-2222-3333-444444444444",
                    }
                ],
                sort_keys=False,
                allow_unicode=True,
            )
        )

        list_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "--rebuild",
            "list",
        )
        self.assertEqual(list_result.returncode, 0, msg=list_result.stderr)
        self.assertIn("Imported high id task", list_result.stdout)
        self.assertRegex(list_result.stdout, r"(?m)^ 1\s")
        self.assertNotIn(" 999 ", list_result.stdout)

        export_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "export",
        )
        self.assertEqual(export_result.returncode, 0, msg=export_result.stderr)
        exported = json.loads(export_result.stdout)
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["id"], 1)
        self.assertEqual(
            exported[0]["uuid"],
            "99999999-1111-2222-3333-444444444444",
        )

    def test_undo_persists_across_wrapper_invocations(self) -> None:
        add_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "add",
            "Undo",
            "priority",
            "change",
        )
        self.assertEqual(add_result.returncode, 0, msg=add_result.stderr)

        modify_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "1",
            "modify",
            "priority:H",
        )
        self.assertEqual(modify_result.returncode, 0, msg=modify_result.stderr)

        undo_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "undo",
        )
        self.assertEqual(undo_result.returncode, 0, msg=undo_result.stderr)

        snapshot = self.load_snapshot()
        self.assertEqual(len(snapshot), 1)
        task = snapshot[0]
        self.assertEqual(task["description"], "Undo priority change")
        self.assertNotIn("priority", task)

    def test_context_definition_persists_in_repo_local_taskrc(self) -> None:
        define_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "context",
            "define",
            "home",
            "project:Home",
        )
        self.assertEqual(define_result.returncode, 0, msg=define_result.stderr)

        activate_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "context",
            "home",
        )
        self.assertEqual(activate_result.returncode, 0, msg=activate_result.stderr)

        add_result = self.run_wrapper(
            "--repo-root",
            str(self.repo_root),
            "add",
            "Replace",
            "kitchen",
            "light",
        )
        self.assertEqual(add_result.returncode, 0, msg=add_result.stderr)

        snapshot = self.load_snapshot()
        self.assertEqual(snapshot[0]["project"], "Home")

        taskrc = self.repo_root / ".taskwarrior" / "taskrc"
        taskrc_text = taskrc.read_text()
        self.assertIn("context.home.read=project:Home", taskrc_text)
        self.assertIn("context.home.write=project:Home", taskrc_text)

    def test_auto_discovers_repo_root_from_nested_git_dir(self) -> None:
        (self.repo_root / ".git").mkdir()
        nested_dir = self.repo_root / "src" / "pkg"
        nested_dir.mkdir(parents=True)

        result = self.run_wrapper(
            "add",
            "Nested",
            "task",
            cwd=nested_dir,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((self.repo_root / ".taskwarrior" / "tasks.yaml").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
