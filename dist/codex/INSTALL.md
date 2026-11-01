# Installation

The installer registers this package for the current user. It supports Codex,
Claude Code and Cursor. It does not install those applications, sign in to them,
trust hooks, grant permissions, edit persistent instruction files or write to a
project. ChatGPT web installation is a separate manual flow described in CODEX.md.

## One command

All detected supported local hosts:

```bash
curl -fsSL https://raw.githubusercontent.com/theocarranza/monolithic-agent-guidelines/v1.4.0/install.sh | bash -s -- --host all
```

Choose one or more hosts:

```bash
curl -fsSL https://raw.githubusercontent.com/theocarranza/monolithic-agent-guidelines/v1.4.0/install.sh | bash -s -- --host codex,cursor
```

Download and inspect install.sh first if you prefer to review it before running.
The bootstrap uses Git over HTTPS to fetch the pinned tag into a versioned user
data checkout. Reuse requires the same origin/tag and no local changes. It never
replaces an unrelated or edited checkout. Bash, Git and Python 3.9+ are required.

## From a checkout

```bash
bash install.sh --host all
bash install.sh --host codex --host claude
bash install.sh --host cursor --dry-run
```

--host all (the default) detects supported applications and reports unavailable
ones; it does not claim every application is installed. Explicit Codex/Claude
selection requires its CLI on PATH. Explicit Cursor selection can prepare its
local plugin directory before the application is installed. --dry-run from a
checkout detects targets without writes or client commands. With the remote
bootstrap, source files may first be cached; host installation is still skipped.

## What is installed

| Host | Installation | Activation |
| --- | --- | --- |
| Codex | Native plugin: monolithic-agent-guidelines@monolithic-agent-guidelines | Restart; review/trust four retrieval hooks through /hooks |
| Claude Code | Native plugin: andrej-karpathy-skills@monolithic-agent-guidelines | Restart; review the three guidance hooks using the host's trust controls |
| Cursor | Portable package under ~/.cursor/plugins/local/monolithic-agent-guidelines | Reload Cursor; enable local imports if your organization permits them; skills/references only |
| ChatGPT | Manual installation/configuration | See CODEX.md; shell installation does not publish or install into a web account |

Codex and Claude register a dedicated marketplace named monolithic-agent-guidelines.
The installer does not overwrite the original upstream karpathy-skills marketplace.
Cursor's portable package exposes the core skill and references; it does not claim
Cursor hook enforcement or install the Codex-specific setup skill.

## Updates and preservation

Rerun the installer for the new release. A versioned package lives under
~/.local/share/monolithic-agent-guidelines/releases/<version>. Cursor has an
installer-owned local copy. Owned files are hashed; modified or unowned files are
refused rather than overwritten. Symlink targets are refused. Unexpected stale
files require manual review; the installer does not delete them.

A native marketplace registration belonging to this repository can be refreshed
with the host's own remove/add commands. This does not remove plugin data or edit
AGENTS.md, CLAUDE.md, project rules, credentials or other marketplaces. Another
marketplace source with the same name is refused. Installation can stop after
some hosts completed; the JSON result/error and native client status are the
source of truth. A successful copy does not prove the client loaded it.

Persistent startup guidance remains an explicit setup action in Codex. Preview
and approve any AGENTS.md update separately. Refresh that setup after an upgrade
only if you use it. Existing project and approval rules continue to apply.

## Check the result

Codex: run codex plugin list --marketplace monolithic-agent-guidelines --json.
The installed version should be 1.4.0. In /hooks, only SessionStart,
UserPromptSubmit, PreToolUse and PostCompact belong to this plugin. Review/trust
those definitions; there is no completion verifier or state-write permission step.

Claude Code: use claude plugin list --json and inspect the dedicated plugin id.
Cursor: reload and inspect Customize for the local portable package. Local imports
may be restricted by enterprise policy; the installer never changes that policy.

In a fresh supported hook session, request pwd, read the first denial's guidance,
and allow a same-turn retry. It should finish normally without a verifier. Other
plugins can still apply their own completion requirements.
