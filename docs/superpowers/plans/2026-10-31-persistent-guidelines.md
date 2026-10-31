# Persistent Guidelines Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this approved plan in this session.

**Goal:** Provide explicit setup for persistent Codex guidance and release version 1.2.0.

**Architecture:** A setup skill wraps a standard-library Python installer. Preview and digest-bound apply protect existing instructions; one marked block derives from the original skill.

**Spec:** `docs/superpowers/specs/2026-10-31-persistent-guidelines-design.md`

## Constraints

Preserve original guideline, Claude, Cursor, and example files. Do not edit real global instructions while testing. No startup hooks, external runtime dependencies, or automatic instruction changes. Existing permissions and approval requirements take precedence.

## Tasks

- [x] Write behavioral installer tests; run and observe failure before implementation.
- [x] Implement preview, effective target selection, protected apply, backup, and idempotent merge; run all tests.
- [x] Add setup skill, onboarding metadata, version bump, and usage documentation.
- [ ] Verify native skill discovery and fresh-thread instruction loading in a temporary project.
- [ ] Obtain independent review, resolve material findings, publish and merge a pull request, and cut v1.2.0.

## Review focus

Preview must not write. Changed target/source/override invalidates approval. Original bytes outside the marked section survive. No backup is overwritten. Repeated setup makes no changes. Filesystem errors must not truncate the destination. Native instruction loading is distinct from model obedience.

## Verification and review record

- The installer tests were run before implementation and failed because the installer was absent. Final suite: 23 passing tests; installer line and branch coverage: 100%.
- Native Codex 0.166.0 installed the candidate, discovered both enabled skills at readable paths, and returned setup as the plugin onboarding skill.
- Model-based startup validation was attempted in a temporary project but blocked by this environment's authentication/startup behavior; it is not claimed as verified.
- Independent review found no release blockers. Its override-during-apply case was reproduced with a failing regression test and fixed by rechecking the complete effective plan before replacement. The residual race with unrelated editors is documented; no portable atomic compare-and-swap is claimed.
- Original guideline, Claude, Cursor and example files are unchanged. JSON/YAML metadata and whitespace checks pass. No real global instruction file was edited during testing.
