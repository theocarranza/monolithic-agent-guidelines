#!/usr/bin/env python3
"""Preview or explicitly apply persistent Codex guidelines. Python 3.9+."""

import argparse
from dataclasses import dataclass
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import uuid


START = b"<!-- monolithic-agent-guidelines:start -->"
END = b"<!-- monolithic-agent-guidelines:end -->"
SOURCE = Path(__file__).resolve().parents[2] / "karpathy-guidelines/SKILL.md"


def read_target(path):
    if path.is_symlink():
        raise ValueError(f"Refusing symlink instruction file: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Expected a regular instruction file: {path}")
    return path.read_bytes() if path.exists() else None


def effective_target(directory):
    override = directory / "AGENTS.override.md"
    data = read_target(override)
    return override if data and data.strip() else directory / "AGENTS.md"


def managed_block():
    source = SOURCE.read_text(encoding="utf-8")
    headings = [
        "## 1. Think Before Coding", "## 2. Simplicity First",
        "## 3. Surgical Changes", "## 4. Goal-Driven Execution",
    ]
    positions = [source.index(heading) for heading in headings]
    if positions != sorted(positions):
        raise ValueError("Original skill has unexpected principle order")
    principles = source[positions[0]:].strip().encode("utf-8")
    return (
        START + b"\n# Monolithic Agent Guidelines\n\n"
        b"These principles supplement existing instructions. Existing project requirements, "
        b"permissions, and explicit approval requirements for edits and deletions take "
        b"precedence if a principle conflicts with them. This section grants no additional "
        b"authorization. Use judgment for trivial tasks.\n\n" + principles + b"\n" + END
    )


def merge(existing, block):
    start_count, end_count = existing.count(START), existing.count(END)
    if not start_count and not end_count:
        separator = b"" if not existing else b"\n" if existing.endswith(b"\n") else b"\n\n"
        return existing + separator + block + b"\n"
    if start_count != 1 or end_count != 1 or existing.index(START) > existing.index(END):
        raise ValueError("Malformed or duplicate managed section; resolve it manually")
    start, end = existing.index(START), existing.index(END) + len(END)
    return existing[:start] + block + existing[end:]


@dataclass(frozen=True)
class Plan:
    target: Path
    before: bytes
    existed: bool
    after: bytes

    @property
    def digest(self):
        parts = [str(self.target).encode(), b"existing" if self.existed else b"missing", self.before, self.after]
        return hashlib.sha256(b"\0".join(parts)).hexdigest()

    def report(self, backup=None):
        lines = difflib.unified_diff(
            self.before.decode("utf-8").splitlines(), self.after.decode("utf-8").splitlines(),
            fromfile=str(self.target), tofile=str(self.target), lineterm="",
        )
        return {
            "target": str(self.target), "digest": self.digest,
            "changed": self.before != self.after, "backup": str(backup) if backup else None,
            "backup_required": self.existed and self.before != self.after,
            "diff": "\n".join(lines),
        }


def make_plan(directory):
    target = effective_target(directory)
    before = read_target(target)
    return Plan(target, before or b"", before is not None, merge(before or b"", managed_block()))


def apply_plan(plan):
    if plan.before == plan.after:
        return plan.report()
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    current = read_target(plan.target)
    if current != (plan.before if plan.existed else None):
        raise ValueError("Instruction file changed; preview again before applying")
    backup = None
    mode = stat.S_IMODE(plan.target.stat().st_mode) if plan.existed else 0o600
    if plan.existed:
        backup = plan.target.with_name(plan.target.name + ".monolithic-agent-guidelines." + uuid.uuid4().hex + ".bak")
        descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(plan.before)
            stream.flush()
            os.fsync(stream.fileno())
    descriptor, temporary = tempfile.mkstemp(prefix=".monolithic-agent-guidelines-", dir=plan.target.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(plan.after)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        if make_plan(plan.target.parent).digest != plan.digest:
            raise ValueError("Instruction file changed; preview again before applying")
        os.replace(temporary, plan.target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return plan.report(backup)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["global", "project"], default="global")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--codex-home", type=Path, help="Override global location; defaults to CODEX_HOME or ~/.codex")
    parser.add_argument("--apply", action="store_true", help="Apply only the reviewed preview")
    parser.add_argument("--expected-digest", help="Digest from the approved preview")
    args = parser.parse_args(argv)
    if args.scope == "project" and args.project is None:
        parser.error("--scope project requires --project PATH")
    if args.scope == "global" and args.project is not None:
        parser.error("--project requires --scope project")
    if args.apply and not args.expected_digest:
        parser.error("--apply requires the approved preview's --expected-digest")
    directory = args.project if args.scope == "project" else args.codex_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    try:
        plan = make_plan(directory.expanduser().resolve())
        # Decode before making any changes, so invalid UTF-8 cannot cause a partial install.
        preview = plan.report()
        if args.apply and args.expected_digest != plan.digest:
            raise ValueError("Preview changed; review a fresh preview before applying")
        result = apply_plan(plan) if args.apply else preview
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
