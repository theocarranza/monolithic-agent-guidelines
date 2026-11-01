# Codex 0.166.0 hook discovery compatibility

User-approved approach: generate a dedicated legacy Codex installation package
without root plugin.json, retain the portable root package, and point the Codex
marketplace at the generated package. No live user configuration is edited.

Root cause: the released 0.166.0 loader explicitly skips hook loading for the
AgentPlugin format, including packages that also provide a compatibility overlay.
Moving a hook field within the portable manifest cannot repair this release.

Alternative: remove or rename the portable root manifest. Rejected because it
would remove an existing supported distribution. A separate generated package
preserves it and avoids manually maintaining copies.

The build script copies runtime trees and linked documentation into dist/codex,
rejects symlink inputs/outputs, and provides a read-only drift check. Unexpected
files require manual review; the builder never deletes them. Runtime files remain
authoritative at the repository root. The generated package is committed so a Git
marketplace install needs no build tools beyond runtime Python.

Verification: package tests first fail without the builder; native Codex install
and hooks/list reproduce zero plugin hooks for 1.3.0 and six enabled/untrusted
hooks for 1.3.1. The native test uses a temporary CODEX_HOME and working directory;
it does not trust hooks, invoke a model or modify the user's installed settings.
After user review/trust, native live tool blocking remains a separate smoke test.

Review fixes: regression tests reproduced top-level directory symlinks and a
dangling output manifest bypassing the drift check, then passed after validation
was fixed. Native subprocesses now use the disposable project as cwd. Packaged
README links have their target documents included; development commands are
explicitly labelled as requiring a repository checkout.
