# Codex support

## Intent

Add Codex and ChatGPT plugin packaging to the existing repository while preserving Claude Code and Cursor support and all original behavioral guidance.

## Approaches

Use one shared skill with additive host manifests (selected and approved in conversation). A separate Codex copy would duplicate instructions and allow drift. A complete packaging rewrite would unnecessarily disturb existing clients.

## Scope

- Add root portable `plugin.json` and a Codex compatibility manifest, version `1.1.0`.
- Add a repository marketplace pointing to this repository's root plugin.
- Add OpenAI skill display metadata without changing `SKILL.md`.
- Add Codex installation instructions and an optional persistent-guidance setup.
- Add a short discovery section to the English README.
- Keep all other original files byte-for-byte unchanged, including legacy version metadata.

## Constraints and acceptance

No automatic installation, publication, cleanup, or changes to user configuration. No executable dependencies, hooks, or services. Preserve upstream attribution. Parse new manifests and metadata, verify referenced files, and compare protected files against upstream commit `2c606141936f1eeef17fa3043a72095b4765b9c2`.

Native installation testing requires a Codex client. Static checks alone must not be reported as runtime verification. Original Claude packaging stays at its existing version; the new OpenAI package is an additive version.
