# Changelog

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
