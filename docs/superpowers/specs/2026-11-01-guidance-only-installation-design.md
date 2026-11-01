# Guidance-only hooks and multi-host installation

Approved scope: simplify reference delivery, remove the mandatory completion
verifier flow, refactor documentation to the Dev Harness structure, and add one
command to install all detected supported local hosts or a selected subset.

Codex registers SessionStart, UserPromptSubmit, PreToolUse and PostCompact. Claude
Code registers the first three. Initial guarded calls receive missing references
and may retry after reading. Stop and PostToolUse are unregistered; their adapter
events are no-ops even when legacy state is corrupt. Legacy verifier files remain
for preservation, outside the active workflow. Projects own delivery verification.

Installation is user-scoped. Codex and Claude use native plugin commands and a
dedicated marketplace. Cursor receives a portable core skill with references.
ChatGPT remains manual. Installation never grants trust, changes permissions or
edits persistent instruction files. Versioned snapshots and ownership hashes
preserve unrelated and edited files; stale files are reported without deletion.

The README follows the Dev Harness pattern at this repository's scale: useful
badges, purpose, documentation map, architecture, support, requirements, install,
quick start, development checks and limitations.

Acceptance evidence: isolated-home installer tests; adapter denial/retry/reload
tests; completion no-op tests; generated package equality; real Codex 0.166.0
discovery through the installer. Live Claude/Cursor activation is not established
by mocked native command contracts or filesystem copies. Native model execution
is not established by registry discovery.
