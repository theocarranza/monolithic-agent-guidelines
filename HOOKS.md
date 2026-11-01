# On-demand references and host hooks

This plugin bundles guidance and a read-only query command. Synchronous host hooks
supply missing guidance before guarded tool calls and request check evidence at
completion. They are guardrails; they cannot prove model comprehension or enforce
all tool paths. Python 3.9+ and Linux are required for these scripts.

## Retrieval

From the complete plugin checkout (or use absolute script paths):

```bash
python3 retrieval/query.py catalog --language dart
python3 retrieval/query.py find "error" --language dart
python3 retrieval/query.py fetch dart/either
python3 retrieval/query.py fetch core/principles#4-goal-driven-execution
```

Catalog/find only route reading. Fetch returns content plus ID, source path,
provenance, installed version, whole-document hash and returned-content hash.
Parent sections include child sections; fenced code headings are ignored. IDs and
section slugs must match exactly. Ambiguous headings and unknown IDs are errors.
No matches exits 1; invalid input/store exits 2. Retrieval never downloads sources,
rebuilds the catalog or changes session receipts. A standalone skill copy keeps
the original embedded principles but lacks this engine and hooks.

## Host registration and trust

Codex: the marketplace selects generated dist/codex, whose legacy
.codex-plugin/plugin.json selects hooks/codex.json. Codex 0.166.0 skips hooks
for the portable root package; do not point this marketplace back to ./.
Regenerate with python3 scripts/build_codex_package.py after source changes. Claude Code: the standard
hooks/hooks.json calls the Claude adapter. Both retain their existing plugin
identities. Install/enable the plugin through the host and review its current hook
definition through the host's review interface where required. Codex skips
untrusted or changed non-managed hooks. No global hook file is needed.

Do not bypass trust review in normal use. Setup and `--status` deliberately report
enforcement as unverified; a script cannot infer host trust or callback coverage
from its own files. Unsupported clients, standalone skill installs and ordinary
ChatGPT conversations have no automatic hook enforcement. Cloud-orchestrated Work
threads do not support these local command hooks even with local tool execution.

## Lifecycle

SessionStart supplies a short summary and retrieval rules. UserPromptSubmit starts
a fresh task context. SessionStart on resume/compact resets receipts while preserving accumulated task
languages/topics. Codex also registers PostCompact to invalidate receipts; startup
context is supplied through SessionStart, not PostCompact. Pending unverified changes survive these resets.

PreToolUse checks the current prompt scope, affected paths and root pubspec.yaml /
package.json. A package.json is a conservative TypeScript hint; explicit prompt
and tool paths add languages for mixed/nested projects. Full repository language
analysis and shell interpretation are not attempted. Optional topic references
are selected by task/tool words; use the catalog for topics inference misses.

The first guarded call with missing/stale references is denied with that guidance
in the denial reason. Read it and retry. Receipts record emitted IDs/version/hash,
not acknowledged delivery. If the host truncates feedback, fetch the named sources
again. A fresh pre-tool event does not return permissionDecision=allow: normal
permissions still decide whether the action can proceed.

Native Read/Grep/Glob and known read tools remain read-only. All shell commands
and unknown local tools are guarded and conservatively count as possible changes,
including shell inspection. Only exact direct `python3`/`python` invocations of
the installed query or verification entry points are exempt. Shell expressions,
redirection, command substitutions and unrelated scripts are not exempt. Existing
interactive shell sessions and unsupported tool paths are outside this boundary.

Private state lives under PLUGIN_DATA (or CLAUDE_PLUGIN_DATA), otherwise
$XDG_STATE_HOME/monolithic-agent-guidelines/<host> (default ~/.local/state).
Keys include host/session/workspace/agent/transcript identity. Linux file locks
serialize updates; atomic private JSON files preserve state. Records are not
automatically deleted. Do not edit them to fabricate successful retrieval/checks.
A corrupt record blocks normal guarded work; use a fresh session or resolve it
manually. The state is local and writable, not tamper-proof audit evidence.

## Verification

The hook supplies the exact command with a session key:

```bash
python3 /absolute/plugin/enforcement/verify.py --key SESSION_KEY --cwd /project --host codex --state-dir /exact/host/state/directory
```

It runs only when invoked explicitly, never in a lifecycle hook. Project
.monolithic-guidelines.json can configure checks as argument arrays, without a
shell. For this Python repository an appropriate configuration is:

```json
{
  "verification_commands": [
    ["python3", "-m", "unittest", "discover", "-s", "tests", "-q"],
    ["git", "diff", "--check"]
  ]
}
```

Configure commands appropriate to the project under its usual edit approval
rules. Commands run as local programs with inherited environment and project
working directory; review them as executable project configuration. They may
have side effects just like manually running the same test commands. No shell
expansion is performed. Each check has a 300-second timeout; output tails and real
exit codes are retained. Failures/timeouts never count as passing evidence.

Without configuration, git projects use git diff --check. This verifies whitespace
only, including neither test correctness nor all untracked/staged content. Non-git
projects require explicit checks. Configure real project tests for meaningful
completion evidence.

Guarded calls invalidate evidence before execution and again after completion.
Checks bind to that generation, task epoch and configured commands; concurrent
guarded work for the same session identity or configuration changes invalidate
them. Independently keyed sessions and subagents do not share generations, even
when editing the same workspace. Verification is not workspace-wide across those
sessions. Edits outside observed hook paths cannot reliably be detected. Stop requests fresh checks for missing, failed
or stale evidence. On repeated Stop continuation it warns and permits a response
reporting the blocker so the host cannot loop forever. This escape does not certify
completion or prevent an unsupported claim by the model.

## Smoke test on your machine

Use a disposable project with harmless verification commands. Enable/trust hooks
in the host. In a new session request one small file change. Confirm that:

1. Session startup contains the summaries and local retrieval instructions.
2. The first guarded action is denied with the correct language references;
   retrying it proceeds subject to normal permissions.
3. Completion requests the explicit verifier; its real result satisfies the gate.
4. A later edit makes earlier verification stale.
5. Resume/compaction causes guidance to be supplied again.

These observations prove those callbacks ran in that host/version/environment.
They do not establish universal enforcement. `python3 -m unittest discover -s tests
-q` exercises real adapter subprocesses with documented host JSON, independently
of model access. Live model-based obedience is a separate test.

## Host limits

Disabled/untrusted hooks, unsupported clients/tool paths, hook process startup
failures and host errors/timeouts can permit actions without this policy running.
Returning exit 2 or a supported denial blocks covered calls; a process that never
starts cannot issue that denial. Subagents may share a parent session ID; isolation
also uses agent/transcript fields when supplied by the host. Avoid claiming full
subagent coverage until tested on the intended host.

Contracts checked against official documentation on 2026-10-31:
- https://learn.chatgpt.com/docs/hooks
- https://developers.openai.com/plugins/build/plugins
- https://code.claude.com/docs/en/hooks


Native discovery was reproduced with Codex 0.166.0: portable v1.3.0 yielded zero
plugin hooks; the legacy distribution in v1.3.1 yields all six, enabled and
untrusted, without registry errors. Run tests/native_codex_discovery.py with the
absolute Codex binary path to repeat this check. Trust and live execution remain
separate user-machine checks; discovery does not prove the hook callbacks ran.


## Shared state and sandbox access (1.3.2)

The generated verifier command carries --state-dir with the exact host-specific
StateStore directory. This overrides hook-only PLUGIN_DATA/CLAUDE_PLUGIN_DATA and
shell XDG_STATE_HOME differences. Preserve the entire current command, including
its key, workspace and state directory. The verifier refuses missing records
rather than creating an empty session in a guessed directory.

The verifier writes a lock and evidence under that directory. A workspace-write
sandbox may expose it read-only. Permission failures print the exact directory
and a narrow access instruction. For a local Codex session, the user may approve
that specific directory by starting `codex --add-dir /exact/state/directory`.
This is a launch permission, not a plugin-managed setting. It does not change an
already running desktop session. Setup must show the path and obtain permission;
neither setup nor the hooks automatically grant access, disable the sandbox,
change filesystem permissions or write global configuration. Grant only the
shown state directory, not the whole home or plugin cache.

Verification: subprocess lifecycle tests start with hook-only PLUGIN_DATA, remove
it for the verifier, and still satisfy Stop using the explicit directory. Injected EROFS/EACCES/EPERM lock failures leave Stop blocked; once access is
available, real configured checks run and Stop accepts the evidence. An optional
unprivileged Linux subprocess test exercises file permissions where mapped
UID/GID support exists. It is skipped in the development host, which maps only
root. These are not exact Codex sandbox tests. Native
bubblewrap execution in the development host is unavailable (namespace creation
is prohibited); repeat the supported-client test after approving its scoped
write access. No live user permissions are changed by these tests.
