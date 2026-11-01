# On-demand guidance hooks

The plugin provides a versioned reference store and read-only catalog/find/fetch
query. Host hooks supply missing guidance before guarded tools proceed. Python
3.9+ and Linux are required. Hooks establish emitted guidance, not comprehension.

## Registration and trust

The Codex marketplace installs generated dist/codex. Its legacy
.codex-plugin/plugin.json selects hooks/codex.json, avoiding the Codex 0.166.0
portable-format hook discovery limitation. Claude Code uses hooks/hooks.json.
Review/trust installed definitions through the host's hook interface. Neither
installation nor setup automatically trusts hooks or changes security settings.

Codex registers SessionStart, UserPromptSubmit, PreToolUse and PostCompact.
Claude Code registers SessionStart, UserPromptSubmit and PreToolUse; its
SessionStart compact/resume events refresh receipts. No Stop or PostToolUse hook
is registered by this package. Other plugins may have their own policies.

## Retrieval lifecycle

SessionStart supplies compact summaries and the installed query path. A new
prompt clears receipts and selects task scope. Resume/compaction clears receipts
while retaining the established language/topic scope.

PreToolUse selects core/shared guidance, language rules and relevant topics from
the prompt, tool arguments and root pubspec.yaml/package.json. The first guarded
action with missing or stale references is denied with the guidance and its
source/version/hash. Read it and retry. The retry returns no permission override;
normal permissions decide whether the action proceeds. A changed reference forces
fresh delivery even without a version bump. If feedback was truncated, fetch the
named sources explicitly. Routing is conservative, not full repository analysis.

Native read tools and exact direct installed query invocations remain read-only.
Shell and unknown local tools pass through the retrieval gate. They do not become
"dirty work" and do not create a requirement to run project checks. Completing a
turn does not touch this plugin's session state or request another command.

Private retrieval bookkeeping lives under PLUGIN_DATA/CLAUDE_PLUGIN_DATA, otherwise
XDG_STATE_HOME/monolithic-agent-guidelines/<host> (default ~/.local/state). Only
host hooks read/write it. Session identity, private file permissions, atomic writes
and locking protect consistency. Existing records remain in place; no cleanup or
user configuration changes are performed. Records show emitted references, not
acknowledged delivery or tamper-proof evidence.

The agent never needs additional sandbox access to plugin state for this flow.
Do not request escalation, --add-dir or permission changes for reference retrieval.
A host that cannot run the hook or write its own bookkeeping is unsupported or
misconfigured; report the actual failure rather than broadening permissions.

## Read-only query

Use the installed root, not a guessed cache version:

```bash
python3 /absolute/plugin/retrieval/query.py catalog --language dart
python3 /absolute/plugin/retrieval/query.py find error --language dart
python3 /absolute/plugin/retrieval/query.py fetch dart/either
python3 /absolute/plugin/retrieval/query.py fetch core/principles#4-goal-driven-execution
```

Queries never download content or write receipts. Fetch includes ID, provenance,
version, path, whole-document hash and returned-content hash. Section boundaries
respect child headings and fenced code. Unknown or ambiguous references are
errors. No matches exits 1; invalid input/store exits 2.

## Verification of actual work

The fourth principle still applies: choose acceptance criteria, run appropriate
project checks and report their actual results and limits. Existing project and
development-harness verification requirements prevail. This plugin does not add a
completion runner, a receipt requirement or .monolithic-guidelines.json.

Legacy verification scripts from 1.3.x remain on disk for compatibility. They are
unregistered, not an opt-in completion system, and not part of this hook flow.
Do not invoke them for normal guidance tasks or treat old receipts as certification.

## Smoke test

After upgrading, restart the host and review/trust the current hooks. In a fresh
session ask for pwd, allowing a same-turn retry after reading hook feedback.
Confirm initial guidance delivery, successful retry, and normal completion with
no verifier, extra command or state-write permission request from this plugin.
Repeat with Dart/TypeScript scope and resume/compaction to check relevant reloads.

From a repository checkout, run python3 -m unittest discover -s tests -q and
python3 tests/native_codex_discovery.py /absolute/path/to/codex. The native check
installs into a disposable home and checks the actual registry without a model.
It expects four Codex hooks and no Stop/PostToolUse entry for this package.

## Limits

Disabled/untrusted hooks, unsupported clients/tool paths, host errors/timeouts and
existing interactive shell sessions can bypass retrieval. Receipts cannot prove
understanding or compliance. Ordinary ChatGPT conversations and unsupported cloud
execution modes do not gain local hook execution by installing this package.
Standalone skill copies retain the principles but lack this bundled reference
store and hook flow. Unsupported behavior must be reported, not inferred active.
