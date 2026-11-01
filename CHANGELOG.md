# Changelog

## 1.4.0

- Refactor README around the Monolithic Dev Harness documentation standard: badges, purpose, documentation map, architecture, installation, quick start, testing and support limits.
- Add a user-scoped installer for all detected supported local hosts or selected Codex/Claude/Cursor targets, with dry-run, preservation checks and explicit activation steps.

- Limit the default hook flow to reference retrieval, routing and lifecycle reloads.
- Remove registered Stop/PostToolUse hooks and their mandatory completion-verification logic. Shell inspection no longer requires a verifier, receipt or additional sandbox write access.
- Keep retrieval bookkeeping entirely in host hook execution; catalog/find/fetch remains read-only. The fourth principle still requires appropriate project verification.
- Preserve files and existing user configuration; legacy verifier files remain unregistered and are not part of the guidance workflow.
- Update setup, reference instructions and native discovery checks for four Codex retrieval hooks (three on Claude Code).

## 1.3.2

- Pass the exact hook state directory to the verifier so shell environment differences do not select an empty unrelated record.
- Refuse missing session records before creating state; retain workspace, generation and check-configuration validation.
- Report denied state writes with the exact path and narrowly scoped access instructions. Never grant permissions or edit host sandbox configuration automatically.
- Test verification with a sanitized environment and injected read-only/permission failures. An optional unprivileged process test is skipped where UID/GID mapping prevents it. Native Codex sandbox execution remains unverified here because namespace creation is prohibited.

## 1.3.1

- Fix hook discovery on Codex 0.166.0 by routing its marketplace to a generated legacy-format package without a portable root manifest.
- Keep the portable root package intact; generate Codex runtime files from the same source and check committed output for drift.
- Add package regression tests and an optional real Codex hooks/list test using a disposable home without model access.
- Native discovery verifies six enabled hooks awaiting trust. Live tool interception still requires user review/trust and a smoke test.

## 1.3.0

- Add versioned core, shared, Dart and TypeScript references with catalog/find/fetch retrieval.
- Add synchronous Codex and Claude hook adapters with per-context retrieval receipts, conservative tool gating, and explicit verification evidence.
- Reload after new prompts, resume and compaction; invalidate checks before and after guarded actions.
- Replace full persistent startup text with compact summaries and installed retrieval paths. Preserve existing instruction bytes, backups and preview approval safeguards.
- Correct supplied Task API/concurrency examples and floating-point monoid assumptions; keep project-specific helpers contextual.
- Hook trust, supported execution mode and live smoke tests are required. Disabled/untrusted hooks, errors/timeouts and unsupported tool paths can bypass guardrails.
- Preserve the original four principles, Claude plugin identity and existing Cursor rules. Advance both host packages to 1.3.0.

## 1.2.0

- Add an explicit setup skill and native plugin onboarding action for persistent Codex guidance.
- Preview global or project instruction changes before applying them; default to `~/.codex/AGENTS.md` and respect custom `CODEX_HOME` and active overrides.
- Derive the four principles from the unchanged original skill. Preserve surrounding instructions, back up existing files, avoid duplicate sections, and refuse stale previews.
- Keep existing project requirements, permissions, and approval gates authoritative. Do not install global guidance automatically or introduce startup hooks.
- Document native CLI installation, namespaced skill invocation, editor-extension limitations, and the separate scope of ChatGPT instructions.
- Add 23 installer tests. Native Codex 0.166.0 verified package installation, both skills, readable paths, and onboarding registration. Model-based startup behavior remains unverified in the test environment.

## 1.1.0

- Add portable OpenAI packaging, Codex compatibility metadata, a repository marketplace, and installation documentation while retaining original Claude Code and Cursor support.
