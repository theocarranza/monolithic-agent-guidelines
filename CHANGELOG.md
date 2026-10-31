# Changelog

## 1.2.0

- Add an explicit setup skill and native plugin onboarding action for persistent Codex guidance.
- Preview global or project instruction changes before applying them; default to `~/.codex/AGENTS.md` and respect custom `CODEX_HOME` and active overrides.
- Derive the four principles from the unchanged original skill. Preserve surrounding instructions, back up existing files, avoid duplicate sections, and refuse stale previews.
- Keep existing project requirements, permissions, and approval gates authoritative. Do not install global guidance automatically or introduce startup hooks.
- Document native CLI installation, namespaced skill invocation, editor-extension limitations, and the separate scope of ChatGPT instructions.
- Add 23 installer tests. Native Codex 0.166.0 verified package installation, both skills, readable paths, and onboarding registration. Model-based startup behavior remains unverified in the test environment.

## 1.1.0

- Add portable OpenAI packaging, Codex compatibility metadata, a repository marketplace, and installation documentation while retaining original Claude Code and Cursor support.
