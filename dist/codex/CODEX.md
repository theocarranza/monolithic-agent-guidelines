# Monolithic Agent Guidelines for Codex and ChatGPT

This adaptation adds OpenAI packaging around the original principles in
`skills/karpathy-guidelines/SKILL.md`, extended with reference routing. Claude Code and Cursor files remain
available. Both host packages are version 1.3.1; Claude retains its original plugin identity. These additions are not an upstream release.

## Install the local plugin

Use a checkout containing this adaptation. From its root, register the
repository marketplace with a Codex client that supports plugins:

```bash
codex plugin marketplace add .
codex plugin marketplace list
```

Install directly from a supported Codex CLI:

```bash
codex plugin add monolithic-agent-guidelines@monolithic-agent-guidelines
```

Registration makes the marketplace available; it does not itself activate
the skill. In the ChatGPT desktop Plugins Directory, select **Monolithic Agent Guidelines**
and install **Monolithic Agent Guidelines**. Local marketplace availability
depends on the client. Refresh or reopen the directory if needed.

The marketplace's `source.path` selects `./dist/codex`, generated from the
repository's runtime files. This package intentionally has no root `plugin.json`:
Codex 0.166.0 skips plugin hook loading for portable Agent Plugins. The legacy
`.codex-plugin/plugin.json` declares `./hooks/codex.json` in this distribution.
The portable package at the repository root remains available for other clients.

This project has not been published to the public ChatGPT plugin directory.
Local installation does not publish it. Register this fork's implementation branch with:

```bash
codex plugin marketplace add theocarranza/monolithic-agent-guidelines --ref v1.3.2
```

Do not use the upstream URL expecting these additions to be present.
The new OpenAI plugin is named `monolithic-agent-guidelines`; its shared skill
retains the original `karpathy-guidelines` name. Claude's original plugin
identity is unchanged.

## Use the skill

In Codex CLI, select the installed skill through `/skills` or mention:

```text
Use $monolithic-agent-guidelines:karpathy-guidelines to fix the bug described below.
```

In ChatGPT where the plugin is installed and available, use the `@` selector
to choose Karpathy Guidelines. Automatic activation depends on the task
matching the skill description. Installation does not guarantee activation
for every task and does not grant editing or deletion authorization.

## Install only the skill in a local Codex project

The editor extension supports standalone skills, not plugins. As an alternative
to plugin installation, copy the shared skill into a
target project's `.agents/skills/` directory. Run from this checkout's root,
replacing the target path:

```bash
target_project=/absolute/path/to/your/project
mkdir -p "$target_project/.agents/skills"
test ! -e "$target_project/.agents/skills/karpathy-guidelines" &&
  cp -R skills/karpathy-guidelines "$target_project/.agents/skills/karpathy-guidelines"
```

The command refuses an existing destination. Avoid installing both the
plugin and a separate copy unless you intentionally want duplicate entries.

## Set up persistent guidance

Installing the plugin makes its skills available on demand. To put compact summaries and reference retrieval instructions into Codex startup instructions, run the plugin's **Setup** action
or explicitly invoke:

```text
Use $monolithic-agent-guidelines:setup to configure persistent Codex guidance.
```

Setup offers global scope (recommended) or a project directory. Global guidance
normally goes in `~/.codex/AGENTS.md`; a custom `CODEX_HOME` is respected. An
active nonempty `AGENTS.override.md` is selected instead so the result is not
hidden by an override. Project guidance goes in the selected project's effective
instruction file. Later project instructions can refine global guidance.

Setup previews the target and diff, waits for authorization, and then writes a
marked section with principle summaries and versioned retrieval paths. It preserves surrounding bytes,
backs up an existing file beside the target, and is safe to repeat. Changed
previews are refused; malformed sections and symlink instruction files require
manual resolution. Backups are never automatically removed. Existing project
requirements and approval gates take precedence over the principles.

The installer needs Python 3.9 or newer and must run on the intended Codex machine.
Running it in a cloud executor does not configure your local computer. It does
not configure persistent instructions for ordinary ChatGPT conversations.

### Manual setup from this checkout

Preview global installation without creating any files:

```bash
python3 skills/setup/scripts/install_guidelines.py
```

Read the JSON `target`, `diff`, `backup_required`, and `digest`. After approving
the displayed change, repeat with that digest:

```bash
python3 skills/setup/scripts/install_guidelines.py --apply --expected-digest DIGEST_FROM_APPROVED_PREVIEW
```

For a project, include the same arguments on **both** calls:

```bash
python3 skills/setup/scripts/install_guidelines.py --scope project --project /absolute/path/to/project
```

Use `--codex-home PATH` to explicitly choose a different global directory.
Do not use it to point to a cloud home when the intended target is your computer.
The apply response reports the actual `backup` path, if one was necessary.
An unchanged installation produces no additional backup.

Avoid editing the instruction file concurrently while applying setup. The
installer rechecks the effective target and content before atomic replacement,
but cannot coordinate writes from unrelated editors after that final check.

After setup, start a fresh Codex session **without invoking a skill** and ask:

```text
Summarize the four Monolithic Agent Guidelines from your initial instructions.
Do not browse, run commands, or modify files. If absent, report that and stop.
```

## Development checks

```bash
python3 -m unittest discover -s tests -v
```

Tests use temporary instruction directories; they do not edit real global files.
For optional branch coverage, install the development-only `coverage` package,
then run:

```bash
MONOLITHIC_TEST_COVERAGE=1 python3 -m coverage run --branch --parallel-mode --source=skills/setup/scripts -m unittest discover -s tests -v
python3 -m coverage combine
python3 -m coverage report
```

Python itself is the only installer runtime dependency.

## Verify installation in your client

Ask the installed skill to review a small proposed change. Confirm it can
load the four principles and identify success criteria without making edits.
For persistent guidance, separately ask Codex which instruction files it
loaded from the target project.

Static package validation cannot prove client installation or model behavior.

## Packaging references

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Skills](https://learn.chatgpt.com/docs/build-skills)
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Based on upstream commit `2c606141936f1eeef17fa3043a72095b4765b9c2` from
[multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills).
Original author metadata and MIT declarations are preserved. This adaptation
does not claim authorship by Andrej Karpathy or endorsement by upstream.


## Version 1.3.1 candidate and hook support

This checkout is the unreleased 1.3.1 candidate. Until a v1.3.1 tag is published,
register `--ref feat/on-demand-guidance` once that branch is pushed, or use a local
checkout. The versioned installation example above applies after release.

See [HOOKS.md](HOOKS.md) for hook trust, supported hosts and local checks.
Codex discovers the explicit `./hooks/codex.json` compatibility-manifest entry.
It does not need a global hook configuration written by setup. Review the exact
hook definition through the host's hook review interface. Setup reports
`hook_status: unverified`; only a successful live host smoke test establishes
that hooks ran in that environment. This plugin cannot verify trust merely from
its own installed files.

Standalone skill copies keep the four embedded principles but do not include
the reference engine or hooks. Copy/install the complete plugin to use those
features. Cloud-orchestrated ChatGPT sessions do not run these local command
hooks. Ordinary ChatGPT conversations remain outside their scope.


## Codex 0.166.0 hook discovery regression

Version 1.3.0 installed skills but did not expose hooks in this client. Version
1.3.1 routes the Codex marketplace to a generated legacy-format package. Do not
manually edit dist/codex: edit the authoritative source, then run:

```bash
python3 scripts/build_codex_package.py
python3 scripts/build_codex_package.py --check
python3 -m unittest discover -s tests -q
python3 tests/native_codex_discovery.py /absolute/path/to/codex
```

Run these development commands from the repository checkout, not the installed
plugin cache. The optional native test installs into a disposable CODEX_HOME and queries the
real app-server hooks/list registry. It requires no model, account or credentials.
It must discover six enabled, untrusted hooks with no errors. It does not trust
hooks or certify live tool interception. After upgrading to v1.3.1, restart Codex,
open /hooks, review/trust this package's hooks, then repeat the pwd smoke test.
Rerun setup to refresh any absolute paths in your existing global guidance.


## Verifier state access (1.3.2)

Use the full verifier command emitted by the current hook, including --state-dir.
The hook's environment can differ from shell tools. The explicit directory keeps
both processes on the same existing session record. If sandbox access is denied,
review the directory printed by the verifier and grant only that directory.
For local CLI use, restart with `codex --add-dir /exact/state/directory` and
repeat the test in the new session using its new hook-supplied command. This
does not modify an existing desktop session; approve equivalent scoped access in
that session when supported. Do not use full-access mode to test this plugin.
