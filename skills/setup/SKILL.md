---
name: setup
description: Set up persistent Monolithic Agent Guidelines in Codex AGENTS.md on the user's intended machine. Use only when explicitly asked to configure global or project guidance; preview the change and obtain authorization before applying it.
---

# Set up persistent Codex guidance

This workflow installs the original four principles as Codex startup instructions.
Installing the plugin alone does not change any instruction file.

1. Establish that the executor is the user's intended Codex machine. A cloud
   executor's home is separate from the user's computer. If this is the wrong
   machine or local execution is unavailable, provide the manual steps in
   `CODEX.md` at the plugin root; do not claim the user's machine is configured.
2. Offer global scope (recommended) or a specific project directory. Global
   scope defaults to `$CODEX_HOME/AGENTS.md`, or `~/.codex/AGENTS.md` when unset.
   An active nonempty `AGENTS.override.md` takes precedence; show the effective
   target selected by the installer. Do not silently install into an ignored file.
3. Locate this installed skill's directory from its registered path. Run its
   bundled installer with Python 3.9 or newer. Do not guess a cache path:

   ```bash
   python3 /absolute/path/to/skills/setup/scripts/install_guidelines.py
   ```

   For project scope, add `--scope project --project /absolute/project/path`.
   The default operation is a read-only preview. It derives the four principles
   from the original sibling skill, preserving one authoritative source.
4. Present the reported target, proposed diff, and backup requirement. Explain
   that global guidance applies to subsequent Codex sessions across projects;
   project instructions can refine or override it. Respect all existing edit
   and deletion approval gates. The user's authorization to install the plugin
   is not authorization to modify their instruction files.
5. Only after the proposed instruction change is explicitly authorized, repeat
   the same scope arguments with `--apply --expected-digest DIGEST`, using the
   digest from the approved preview. Do not fabricate a digest, bypass a mismatch,
   or automatically apply a newly generated preview. A mismatch requires a new
   review. Already-present guidance is a no-op.
6. Report the written path and backup path. The installer preserves all content
   outside its marked section and backs up existing bytes before replacement.
   It does not reconcile conflicting prose automatically. If conflicts exist,
   resolve them with the user before applying. Existing project requirements,
   permissions, and explicit authorization gates take precedence.
   Ask the user to avoid concurrent edits during apply: the final checks are
   best effort against unrelated writers, not a shared editor lock.
7. Ask the user to start a fresh Codex session in the intended project and
   summarize the four principles from its initial instructions without invoking
   a skill, browsing, or modifying files. Distinguish a successful file write
   from verified startup loading and from observed model behavior.

Do not edit unrelated configuration, install startup hooks, delete instruction
files or backups, or claim automatic coverage for ChatGPT conversations. This
workflow configures Codex instruction loading only.
