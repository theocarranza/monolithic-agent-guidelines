# Codex Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add native Codex packaging around the original shared skill.

**Architecture:** Add portable and compatibility manifests and a repository marketplace. Reuse existing instructions without changing their behavior.

**Tech Stack:** JSON, YAML, Markdown; Git and Python for verification.

**Spec:** `docs/superpowers/specs/2026-10-31-codex-support-design.md`

## Global Constraints

Preserve original files except the English README's additive discovery section. No installation, publication, deletion, hooks, or services. Use package version `1.1.0`; retain upstream attribution and original legacy versions.

## Review Focus

- Resolve marketplace paths from repository root, not catalog directory.
- Avoid implying the upstream repository already distributes these additions.
- Distinguish skill activation from persistent project instructions.
- Keep native skill installation from overwriting existing directories.
- Report unavailable client testing explicitly.

### Task 1: Add packaging and documentation

**Files:** Create `plugin.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `skills/karpathy-guidelines/agents/openai.yaml`, `CODEX.md`; append to `README.md`.

**Interfaces:** All manifests consume existing `skills/karpathy-guidelines/SKILL.md`; the marketplace produces one discoverable root plugin.

- [x] Verify clean upstream baseline and absence of project-specific instructions.
- [x] Add manifests, metadata, and installation guide based on current OpenAI documentation.
- [x] Parse JSON and YAML; verify names, versions, path resolution, prompt skill reference, and protected file bytes against upstream.
- [x] Review the complete diff, run `git diff --check`, and record checks and limitations.

Configuration and documentation only: use direct validation rather than introduce a test framework.

## Verification record

Static JSON/YAML, manifest identity/version agreement, marketplace and skill path resolution, original file preservation, and `git diff --check` passed. No test or coverage setup exists. Native Codex installation has not been tested because the executable is unavailable. Final review was a self-review; no independent reviewer result was available.
