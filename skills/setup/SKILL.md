---
name: setup
description: Set up persistent Monolithic Agent Guidelines and explain bundled hook activation on the user's intended Codex machine. Use only when explicitly asked to configure global or project guidance; preview changes and obtain authorization before applying them.
---

# Set up persistent guidance and inspect hook readiness

Configure compact principle summaries and installed retrieval paths. Plugin
installation alone does not modify instruction files or prove hooks are active.

1. Establish that this executor is the user's intended Codex machine. A cloud
   executor has a separate home. If local execution is unavailable, give the
   manual steps in CODEX.md at the plugin root. Do not claim their computer is
   configured.
2. Offer global scope (recommended) or a specific project directory. Global
   scope defaults to $CODEX_HOME, otherwise ~/.codex. A nonempty active
   AGENTS.override.md takes precedence over AGENTS.md. Show the effective target.
3. Locate this skill's registered installed path. Run its bundled Python 3.9+
   installer; do not guess a versioned cache path:

   ```bash
   python3 /absolute/path/to/skills/setup/scripts/install_guidelines.py
   ```

   For project scope add --scope project --project /absolute/project/path.
   Default operation is read-only preview. Present target, diff, backup requirement
   and hook_status. It preserves bytes outside the managed block.
4. Respect existing edit/deletion approval gates. Authorization to install a plugin
   does not authorize changing instruction files. Only after the displayed change
   is authorized, repeat identical scope arguments with --apply --expected-digest
   DIGEST from that preview. Refuse mismatches; do not silently approve a new diff.
   Already-current guidance is a no-op. Avoid concurrent edits during apply; the
   final recheck is best effort against unrelated editors, not a shared lock.
5. Report written and backup paths. Explain that startup summaries route the agent
   to installed full principles and relevant language references. Rerun setup after
   a plugin relocation or upgrade so absolute retrieval paths remain current.
6. Explain bundled hook registration: Codex uses .codex-plugin/plugin.json pointing
   to hooks/codex.json; Claude Code discovers hooks/hooks.json. No global hook file
   needs to be written. Do not automatically trust hooks, enable unrelated features
   or alter host security settings. Direct the user to the host's hook review
   interface to review the current definition. If a separate configuration change
   is needed, preview it and obtain authorization under existing project gates.
7. Run the appropriate adapter with --status only as a readiness explanation:

   ```bash
   python3 /absolute/plugin/root/enforcement/adapters/codex.py --status
   ```

   This returns enforcement: unverified. Presence on disk does not establish host
   support, trust, startup loading or model compliance. Follow HOOKS.md for a real
   isolated host smoke test; distinguish protocol tests from live host evidence.
8. Explain explicit verification: the hook supplies an enforcement/verify.py
   command after guarded work. It executes configured project argument arrays
   only when explicitly invoked and records actual exit codes. Explain that the
   default git diff --check proves whitespace cleanliness only. Preview and obtain
   authorization before creating a project verification configuration.

Do not delete instructions, backups or session records. Do not claim local command
hooks cover cloud-orchestrated ChatGPT sessions or ordinary ChatGPT conversations.
Report unsupported/disabled/untrusted hooks as inactive or unverified, never active.
