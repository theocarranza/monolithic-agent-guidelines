---
name: karpathy-guidelines
description: Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria.
license: MIT
---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

<!-- reference-routing -->

## Installed references and reloads

Keep the four principles above authoritative. Before substantial planning,
implementation or review, consult the installed [catalog](../../knowledge/catalog.tsv)
and fetch the full applicable language/topic references. Use
`python3 <plugin-root>/retrieval/query.py catalog --language dart` (or `typescript`),
then `find TOPIC --language LANGUAGE`, then `fetch ID` or `fetch ID#heading`.
Read [retrieval policy](../../knowledge/core/retrieval-policy.md) for reload rules.
Reload after resume, compaction, a new task or a change of language/module/library.
Use returned source/version/hash metadata rather than recalling an earlier copy.

Dart tasks use [strict Dart guidance](../../knowledge/dart/guidelines.md) and fetch
Task, Option and Either references as relevant. TypeScript tasks use
[TypeScript guidance](../../knowledge/typescript/guidelines.md), with effects and
monoid references when relevant. Shared advice never weakens stricter language or
project rules. Research and examples support decisions; they do not prescribe
source-project helpers or dependencies in other repositories.

Bundled hooks can supply missing guidance before tools proceed and request actual
verification evidence at completion. Host support, trust and observed execution
are required. Installation alone does not prove enforcement. If installed as a
standalone skill without the plugin's reference store and scripts, apply the four
principles above and report that references/hooks are unavailable. Never invent
missing guidance or bypass project permissions and approval gates.
