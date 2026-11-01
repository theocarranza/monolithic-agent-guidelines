"""Exercise the real installer against temporary instruction directories."""

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/setup/scripts/install_guidelines.py"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "codex home"

    def invoke(self, *args):
        self.assertTrue(SCRIPT.is_file(), "installer does not exist yet")
        prefix = [sys.executable, "-m", "coverage", "run", "--branch", "--parallel-mode"] if os.environ.get("MONOLITHIC_TEST_COVERAGE") else [sys.executable]
        return subprocess.run(
            [*prefix, str(SCRIPT), *map(str, args)],
            capture_output=True, text=True,
        )

    def preview(self, *args):
        result = self.invoke(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, preview, *args):
        return self.preview(*args, "--apply", "--expected-digest", preview["digest"])

    def seed(self, data=b"Keep my instructions.\r\nNo edits without approval."):
        self.home.mkdir()
        target = self.home / "AGENTS.md"
        target.write_bytes(data)
        return target

    def test_preview_does_not_create_target_or_parent(self):
        result = self.preview("--codex-home", self.home)
        self.assertEqual(result["target"], str(self.home / "AGENTS.md"))
        self.assertIn("Think Before Coding", result["diff"])
        self.assertFalse(self.home.exists())

    def test_create_new_file_with_full_principles(self):
        before = self.preview("--codex-home", self.home)
        result = self.apply(before, "--codex-home", self.home)
        text = Path(result["target"]).read_text()
        for title in ["Think Before Coding", "Simplicity First", "Surgical Changes", "Goal-Driven Execution"]:
            self.assertIn(title, text)
        self.assertIn("explicit approval", text)
        self.assertIsNone(result["backup"])

    def test_startup_is_compact_and_reports_unverified_hooks(self):
        before = self.preview("--codex-home", self.home)
        self.assertEqual(before["hook_status"], "unverified")
        self.assertIn("retrieval/query.py", before["diff"])
        self.apply(before, "--codex-home", self.home)
        text = (self.home / "AGENTS.md").read_text()
        self.assertLess(len(text), 2300)
        self.assertIn("explicit approval", text)
        self.assertIn("sha256", text)

    def test_existing_bytes_and_backup_are_preserved(self):
        target = self.seed()
        original = target.read_bytes()
        before = self.preview("--codex-home", self.home)
        result = self.apply(before, "--codex-home", self.home)
        self.assertTrue(target.read_bytes().startswith(original))
        self.assertEqual(Path(result["backup"]).read_bytes(), original)

    def test_repeat_is_noop_without_another_backup(self):
        self.seed()
        self.apply(self.preview("--codex-home", self.home), "--codex-home", self.home)
        files = {p.name: p.read_bytes() for p in self.home.iterdir()}
        before = self.preview("--codex-home", self.home)
        self.assertFalse(before["changed"])
        result = self.apply(before, "--codex-home", self.home)
        self.assertIsNone(result["backup"])
        self.assertEqual({p.name: p.read_bytes() for p in self.home.iterdir()}, files)

    def test_updates_only_managed_section(self):
        self.seed(b"prefix\r\n")
        self.apply(self.preview("--codex-home", self.home), "--codex-home", self.home)
        target = self.home / "AGENTS.md"
        target.write_bytes(target.read_bytes().replace(b"Think Before Coding", b"Outdated guidance") + b"suffix\r\n")
        self.apply(self.preview("--codex-home", self.home), "--codex-home", self.home)
        self.assertTrue(target.read_bytes().startswith(b"prefix\r\n"))
        self.assertTrue(target.read_bytes().endswith(b"suffix\r\n"))
        self.assertNotIn(b"Outdated guidance", target.read_bytes())

    def test_nonempty_override_is_effective_target(self):
        target = self.seed()
        override = self.home / "AGENTS.override.md"
        override.write_text("Active override\n")
        before = self.preview("--codex-home", self.home)
        self.assertEqual(before["target"], str(override))
        self.apply(before, "--codex-home", self.home)
        self.assertEqual(target.read_bytes(), b"Keep my instructions.\r\nNo edits without approval.")
        self.assertIn("Think Before Coding", override.read_text())

    def test_empty_override_does_not_hide_normal_file(self):
        self.seed()
        (self.home / "AGENTS.override.md").write_text("  \n")
        self.assertEqual(self.preview("--codex-home", self.home)["target"], str(self.home / "AGENTS.md"))

    def test_project_scope_uses_explicit_directory(self):
        project = self.root / "project with spaces"
        before = self.preview("--scope", "project", "--project", project)
        self.apply(before, "--scope", "project", "--project", project)
        self.assertTrue((project / "AGENTS.md").is_file())
        self.assertFalse(self.home.exists())

    def test_apply_requires_preview_digest(self):
        result = self.invoke("--codex-home", self.home, "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.home.exists())

    def test_target_change_invalidates_preview(self):
        target = self.seed()
        before = self.preview("--codex-home", self.home)
        target.write_text("Changed after review")
        result = self.invoke("--codex-home", self.home, "--apply", "--expected-digest", before["digest"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), "Changed after review")
        self.assertEqual(len(list(self.home.iterdir())), 1)

    def test_new_override_invalidates_preview(self):
        self.seed()
        before = self.preview("--codex-home", self.home)
        override = self.home / "AGENTS.override.md"
        override.write_text("New override")
        result = self.invoke("--codex-home", self.home, "--apply", "--expected-digest", before["digest"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(override.read_text(), "New override")

    def test_malformed_or_duplicate_markers_are_refused(self):
        target = self.seed()
        for data in [
            b"<!-- monolithic-agent-guidelines:start -->\nunfinished",
            b"<!-- monolithic-agent-guidelines:end -->",
            b"<!-- monolithic-agent-guidelines:start --><!-- monolithic-agent-guidelines:end -->" * 2,
            b"<!-- monolithic-agent-guidelines:end --><!-- monolithic-agent-guidelines:start -->",
        ]:
            with self.subTest(data=data):
                target.write_bytes(data)
                self.assertNotEqual(self.invoke("--codex-home", self.home).returncode, 0)
                self.assertEqual(target.read_bytes(), data)

    def test_symlink_is_refused_without_modifying_destination(self):
        self.home.mkdir()
        external = self.root / "external.md"
        external.write_text("Keep me")
        (self.home / "AGENTS.md").symlink_to(external)
        self.assertNotEqual(self.invoke("--codex-home", self.home).returncode, 0)
        self.assertEqual(external.read_text(), "Keep me")

    def test_directory_target_is_refused(self):
        (self.home / "AGENTS.md").mkdir(parents=True)
        self.assertNotEqual(self.invoke("--codex-home", self.home).returncode, 0)

    def test_existing_permissions_are_preserved(self):
        target = self.seed()
        target.chmod(0o640)
        self.apply(self.preview("--codex-home", self.home), "--codex-home", self.home)
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_project_scope_requires_directory(self):
        self.assertNotEqual(self.invoke("--scope", "project").returncode, 0)

    def test_global_scope_rejects_project_argument(self):
        self.assertNotEqual(self.invoke("--project", self.root).returncode, 0)
        self.assertFalse(self.home.exists())

    def test_invalid_utf8_is_refused_before_backup_or_write(self):
        target = self.seed(b"preserve\xffthese bytes")
        self.assertNotEqual(self.invoke("--codex-home", self.home).returncode, 0)
        self.assertEqual(target.read_bytes(), b"preserve\xffthese bytes")
        self.assertEqual(len(list(self.home.iterdir())), 1)

    def test_source_change_invalidates_approved_preview(self):
        target = self.seed()
        original = target.read_bytes()
        module = runpy.run_path(str(SCRIPT))
        globals_ = module["managed_block"].__globals__
        source = self.root / "source.md"
        source.write_bytes(globals_["SOURCE"].read_bytes())
        with patch.dict(globals_, SOURCE=source):
            before = module["make_plan"](self.home)
            source.write_text(source.read_text() + "\nAdditional principle detail.\n")
            after = module["make_plan"](self.home)
        self.assertNotEqual(before.digest, after.digest)
        self.assertEqual(target.read_bytes(), original)

    def test_out_of_order_source_principles_are_refused(self):
        module = runpy.run_path(str(SCRIPT))
        source = self.root / "source.md"
        source.write_text("## 2. Simplicity First\n## 1. Think Before Coding\n## 3. Surgical Changes\n## 4. Goal-Driven Execution\n")
        with patch.dict(module["managed_block"].__globals__, SOURCE=source):
            with self.assertRaisesRegex(ValueError, "principle order"):
                module["make_plan"](self.home)
        self.assertFalse(self.home.exists())

    def test_change_between_planning_and_apply_preserves_new_content(self):
        target = self.seed()
        module = runpy.run_path(str(SCRIPT))
        plan = module["make_plan"](self.home)
        target.write_bytes(b"concurrent edit")
        with self.assertRaisesRegex(ValueError, "changed"):
            module["apply_plan"](plan)
        self.assertEqual(target.read_bytes(), b"concurrent edit")
        self.assertEqual(len(list(self.home.iterdir())), 1)

    def test_change_during_atomic_write_preserves_edit_and_cleans_temporary(self):
        target = self.seed()
        original = target.read_bytes()
        module = runpy.run_path(str(SCRIPT))
        plan = module["make_plan"](self.home)
        real_mkstemp = tempfile.mkstemp

        def concurrent_edit(*args, **kwargs):
            target.write_bytes(b"edit during write")
            return real_mkstemp(*args, **kwargs)

        with patch("tempfile.mkstemp", side_effect=concurrent_edit):
            with self.assertRaisesRegex(ValueError, "changed"):
                module["apply_plan"](plan)
        self.assertEqual(target.read_bytes(), b"edit during write")
        backups = list(self.home.glob("*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertEqual(len(list(self.home.iterdir())), 2)

    def test_new_override_during_apply_does_not_write_ignored_file(self):
        target = self.seed()
        original = target.read_bytes()
        module = runpy.run_path(str(SCRIPT))
        plan = module["make_plan"](self.home)
        real_mkstemp = tempfile.mkstemp
        override = self.home / "AGENTS.override.md"

        def activate_override(*args, **kwargs):
            override.write_bytes(b"new active override")
            return real_mkstemp(*args, **kwargs)

        with patch("tempfile.mkstemp", side_effect=activate_override):
            with self.assertRaisesRegex(ValueError, "changed"):
                module["apply_plan"](plan)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(override.read_bytes(), b"new active override")


if __name__ == "__main__":
    unittest.main()
