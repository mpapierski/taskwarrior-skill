#!/usr/bin/env python3
"""Smoke-audit local Taskwarrior metadata names against bundled references.

This catches unmentioned command/report/column/config-family names. It does not
validate that the surrounding guidance is semantically correct.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_GLOBS = ("SKILL.md", "references/*.md")

# These are shell-completion internals. The skill mentions helper commands as a
# category, but does not need detailed operating guidance for every completion
# helper.
INTENTIONAL_COMMAND_OMISSIONS = {
    "_aliases",
    "_context",
    "_zshattributes",
    "_zshcommands",
    "_zshids",
    "_zshuuids",
}

# Read-only/report-internal columns that can remain covered by `task columns`
# guidance unless a user asks for custom report internals.
INTENTIONAL_COLUMN_OMISSIONS = {
    "last",
    "rtype",
    "template",
}


def run_task(data_dir: str, *args: str) -> str:
    cmd = [
        "task",
        "rc:/dev/null",
        f"rc.data.location:{data_dir}",
        "rc.verbose=nothing",
        *args,
    ]
    result = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout


def reference_text() -> str:
    parts: list[str] = []
    for pattern in REFERENCE_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts).lower()


def parse_reports(output: str) -> list[str]:
    reports: list[str] = []
    for line in output.splitlines():
        if not line or line.startswith("Report") or line.startswith("-") or line.endswith("reports"):
            continue
        first = line.split(None, 1)[0]
        if first:
            reports.append(first)
    return reports


def config_families(config_names: list[str]) -> list[str]:
    families = set()
    for name in config_names:
        if name.startswith("report."):
            families.add("report")
        elif name.startswith("context."):
            families.add("context")
        elif name.startswith("uda."):
            families.add("uda")
        elif name.startswith("urgency."):
            families.add("urgency")
        elif name.startswith("sync."):
            families.add("sync")
        elif name.startswith("color."):
            families.add("color")
        elif "." in name:
            families.add(name.split(".", 1)[0])
        else:
            families.add(name)
    return sorted(families)


def is_covered(token: str, docs: str) -> bool:
    token = token.lower()
    pattern = re.escape(token)
    if re.search(rf"(?<![a-z0-9_.+-]){pattern}(?![a-z0-9_.+-])", docs):
        return True
    if "." in token:
        prefix = token.split(".", 1)[0]
        if f"{prefix}.*" in docs:
            return True
    else:
        if re.search(rf"(?<![a-z0-9_.+-]){re.escape(token)}\.", docs):
            return True
    return False


def missing(tokens: list[str], docs: str, intentional: set[str] | None = None) -> list[str]:
    intentional = intentional or set()
    missing_tokens: list[str] = []
    for token in tokens:
        if token in intentional:
            continue
        if not is_covered(token, docs):
            missing_tokens.append(token)
    return sorted(set(missing_tokens))


def print_section(title: str, values: list[str]) -> None:
    print(f"{title}: {len(values)}")
    if values:
        print("  " + "\n  ".join(values))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit nonzero when uncovered metadata is found")
    args = parser.parse_args()

    docs = reference_text()
    with tempfile.TemporaryDirectory(prefix="taskwarrior-skill-audit-") as data_dir:
        commands = run_task(data_dir, "_commands").split()
        columns = run_task(data_dir, "_columns").split()
        configs = run_task(data_dir, "_config").split()
        reports = parse_reports(run_task(data_dir, "reports"))

    missing_commands = missing(commands, docs, INTENTIONAL_COMMAND_OMISSIONS)
    missing_reports = missing(reports, docs)
    missing_columns = missing(columns, docs, INTENTIONAL_COLUMN_OMISSIONS)
    missing_config_families = missing(config_families(configs), docs)

    print_section("Missing command coverage", missing_commands)
    print_section("Missing report coverage", missing_reports)
    print_section("Missing column coverage", missing_columns)
    print_section("Missing config-family coverage", missing_config_families)

    has_missing = any((missing_commands, missing_reports, missing_columns, missing_config_families))
    return 1 if args.strict and has_missing else 0


if __name__ == "__main__":
    sys.exit(main())
