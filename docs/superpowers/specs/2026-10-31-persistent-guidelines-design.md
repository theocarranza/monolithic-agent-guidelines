# Persistent Codex guidelines

Approved in conversation: keep the optional original skill and add an explicit setup workflow that installs its four principles into Codex instructions. Default to global `~/.codex/AGENTS.md` (respect `CODEX_HOME`); offer an explicit project directory. Use an active nonempty `AGENTS.override.md` instead when present so setup does not write an ignored file.

The repository owns `skills/setup/SKILL.md` and its bundled Python installer. Setup previews the exact target and diff, preserves existing instructions, creates a byte-identical backup before edits, and requires an explicit apply operation tied to that preview. A marked section is repeatable and updatable without duplicating or replacing surrounding content. Existing authorization and project rules prevail over the installed principles. Do not install global instructions automatically on plugin installation.

Use one source: read the four sections from the unchanged original skill. Add native onboarding metadata to the existing Codex compatibility overlay without shadowing it through a partial root extension. Preserve Claude and Cursor support. Update OpenAI versions to `1.2.0`; document namespaced skill invocation and native CLI installation.

Acceptance: tests cover preview without writes, new/existing files, backups, byte preservation, repeat installation, managed-section updates, override selection, malformed markers, unsafe targets, and preview drift. Native Codex must discover both skills and read project instructions from a fresh thread without explicit skill invocation. Review, publish a branch and pull request, merge, and release `v1.2.0` after checks pass, as authorized by the user.
