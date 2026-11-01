# On-demand guidance and host hooks

Approved design: shared, versioned knowledge with catalog → find → fetch retrieval;
small startup summaries; host adapters that supply missing guidance before tools
proceed; session-local records invalidated on new prompts, resume and compaction;
completion gated on actual verification evidence. Existing permissions prevail.

Python 3.9+, standard library, Linux. Preserve original principles, Claude identity
and Cursor support. Knowledge is installed with the plugin, never fetched online
at runtime. Normalize project-specific references into portable advice. Strict Dart
rules override permissive general examples. Mark source confidence and correct
known dartz Task and floating-point monoid errors.

The catalog routes core/shared/Dart/TypeScript and optional topics. Fetch returns
source/version/provenance/hash even for sections; parent sections include children;
fenced headings do not split sections. Reject escaping paths and malformed catalogs.
No mutating catalog command is exposed.

Synchronous hooks use documented SessionStart, UserPromptSubmit, PreToolUse,
PostToolUse and Stop contracts. Codex also supports PostCompact. First guarded
call with stale guidance is denied with the full required text in the reason;
a retry can proceed. Never return permissionDecision=allow: normal permissions
still apply. All shell commands are guarded; shell commands conservatively count
as possible changes except exact bundled retrieval and verification invocations.
Read-only native tools do not make a task dirty. Missing/corrupt state never
means successful retrieval or verification. Use locked atomic private state files
outside the plugin and key them by host/session/agent/transcript/workspace.

Verification runs only when explicitly requested by the agent/user, never inside
a lifecycle hook. A runner executes configured argument arrays without a shell,
records real return codes and binds results to the current change generation.
Project `.monolithic-guidelines.json` can list `verification_commands` as arrays
of arguments. Without it, git projects use `git diff --check` (whitespace only);
non-git projects must configure checks. This is evidence of those checks only.
Stop may continue once; repeated Stop blocking must not create an infinite loop:
if still unverified, surface an explicit warning and permit an honest blocked
status report. It cannot prevent an agent from claiming unsupported completion.

Host limitations: disabled/untrusted hooks, unsupported tools, errors/timeouts and
cloud orchestration can bypass plugin hooks. Receipts prove emitted guidance, not
model comprehension or host delivery. Setup reports hooks as unverified pending
host trust and a real smoke test; it must never infer active enforcement merely
from installed files. No global settings or live instructions are edited by tests.
