# On-demand Guidance Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task.

**Goal:** Deliver local reference retrieval and host hook guardrails.
**Architecture:** Immutable knowledge/catalog; read-only query; locked per-session
state; host-specific JSON adapters; explicit verification runner.
**Tech Stack:** Python 3.9+ standard library, unittest, JSON/TSV/Markdown.
**Spec:** docs/superpowers/specs/2026-10-31-on-demand-guidance-design.md

## Global Constraints
- Preserve existing permissions, original four principles and existing host support.
- No network at runtime; no live global configuration writes in verification.
- Never describe plugin guardrails as a complete enforcement boundary.

## Review Focus
- Shell quoting, alternate tool shapes, filenames with spaces and mixed languages.
- Malformed, stale, parallel or cross-session state and reference updates.
- Section boundaries, code fences, duplicate IDs and catalog path escapes.
- Failing checks, checks racing edits, unconfigured projects and stop loops.
- Plugin root relocation, host trust, unsupported events and non-Python installs.

### Task 1: Knowledge and retrieval
Files: knowledge/**; retrieval/{catalog,sections,query}.py; tests/test_query.py.
Produces: Catalog(root).rows, .fetch(id[#section]), .find(terms,language), .select(language).
- [x] Write behavior tests for metadata envelopes, filters, sections, no matches,
  recursive catalog paths, malformed catalogs and path containment; observe failure.
- [x] Implement dependency-free reader and command interface, curated references.
- [x] Run `python -m unittest discover -s tests -p test_query.py -q`; expect pass.
- [x] Commit task.

### Task 2: Policy, session state and verification
Files: enforcement/{policy,session_state,verify}.py; tests/test_enforcement.py.
Consumes Catalog; produces requirements(event), StateStore.transaction(key),
verify.run_checks(root, commands), verification receipts bound to generation.
- [x] Test routing, stale sources, locks, corruption, isolated identities and
  verification failures/races; observe failure.
- [x] Implement conservative policy, atomic private state and explicit check runner.
- [x] Run task tests; expect pass. Commit task.

### Task 3: Host hooks and packaging
Files: enforcement/adapters/{common,codex,claude}.py; hooks/{hooks,codex}.json;
.codex-plugin/plugin.json; tests/test_host_adapters.py.
- [x] Test real stdin/stdout subprocess lifecycle: first denial, retry, edit,
  verification, stop, prompt reset, compaction, errors and parallel sessions.
- [x] Implement synchronous host contracts and hook registration.
- [x] Run task tests; expect pass. Commit task.

### Task 4: Setup, documentation and release candidate validation
Files: skills/setup/**; skills/karpathy-guidelines/SKILL.md; README.md; CODEX.md;
CHANGELOG.md; tests/test_install_guidelines.py.
- [x] Test compact startup preview, retained permissions and unverified hook status;
  observe failure. Preserve all existing installer safety tests.
- [x] Update setup/routing/docs; mark candidate 1.3.0 without cutting a release.
- [x] Run full unittest suite, branch coverage, real query and hook smoke tests,
  native Codex metadata discovery when available. Review and commit.

## Execution ledger
Baseline: 23 tests pass. Working on feature branch feat/on-demand-guidance in the
existing task checkout; no additional worktree is needed for this remote workspace.
Ruling: hooks are guardrails, not a security boundary; Stop loop escape reports
unverified work rather than looping forever. No release/merge requested this turn.

Task 1: complete — 8 retrieval tests pass (f6ada61).
Task 2: policy/state/check execution implemented; 10 behavior tests pass.
Ruling: root-level pubspec.yaml/package.json provide conservative language routing;
explicit tool paths/prompts add languages in mixed or nested projects. Shell calls
are treated as possible changes, including read-only shell commands, because a
portable shell mutation detector would be unreliable. Native Read/Grep/Glob stay
read-only. This can require verification after shell inspection.


Resumption verification:
- Task 2: complete — session/state/verification tests and full suite pass.
- Task 3: complete — actual adapter subprocess tests cover both host protocols,
  denials/retries, reference refresh, lifecycle resets and verification evidence.
- Task 4: complete — compact setup, preserved permissions/backups, package metadata,
  documentation and local query/status smoke checks verified.
- Independent final review: two confirmed findings fixed. Regression tests first
  failed, then passed: compaction/resume discarded language/topic scope; nested
  corrupt state could produce a nonblocking process failure. Nested data is now
  validated before dispatch and continuation resets retain task scope.
- Codex PostCompact returns no additionalContext; SessionStart injects summaries.
- Final tests: 62 passed. Coverage: 100% source lines, 153/154 branches; all touched
  source files exceed 95% line/branch coverage. Function metric is not supplied by
  coverage.py. One unreachable redundant conditional branch remains uncovered.
- Ruling: generation freshness is scoped to one keyed session, not all processes
  editing a workspace — preserve explicit session isolation and document this
  boundary; independent sessions can retain evidence after another session edits.
- Ruling: native host/model behavior remains unverified unless the bounded smoke
  trace demonstrates hook delivery; subprocess protocol tests alone are not proof.

Native Codex 0.166.0 deterministic-provider smoke attempt: timed out before the
first provider request or tool action. No native hook-delivery claim is made.
The CLI starts but supplies no end-to-end evidence in this environment. Both
adapters are verified via real stdin/stdout subprocess lifecycle tests only.
Final package validation: seven package/hook JSON documents parse; git diff
--check passes. Final suite: 62 tests pass after review fixes and documentation.
