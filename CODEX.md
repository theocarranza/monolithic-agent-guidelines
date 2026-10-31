# Monolithic Agent Guidelines for Codex and ChatGPT

This adaptation adds OpenAI packaging around the original, unchanged
`skills/karpathy-guidelines/SKILL.md`. Claude Code and Cursor files remain
available. The new OpenAI package is version 1.1.0; original Claude metadata
retains version 1.0.0. These additions are not an upstream release.

## Install the local plugin

Use a checkout containing this adaptation. From its root, register the
repository marketplace with a Codex client that supports plugins:

```bash
codex plugin marketplace add .
codex plugin marketplace list
```

Registration makes the marketplace available; it does not itself activate
the skill. In the ChatGPT desktop Plugins Directory, select **Monolithic Agent Guidelines**
and install **Monolithic Agent Guidelines**. Local marketplace availability
depends on the client. Refresh or reopen the directory if needed.

The marketplace's `source.path` is relative to the repository root, so `./`
selects this repository's root plugin. The portable root manifest discovers
`skills/`; `.codex-plugin/plugin.json` supplies OpenAI compatibility metadata.
The existing `.claude-plugin/` files continue serving Claude Code.

This project has not been published to the public ChatGPT plugin directory.
Local installation does not publish it. Register this fork's implementation branch with:

```bash
codex plugin marketplace add theocarranza/monolithic-agent-guidelines --ref feat/codex-support
```

Do not use the upstream URL expecting these additions to be present.
The new OpenAI plugin is named `monolithic-agent-guidelines`; its shared skill
retains the original `karpathy-guidelines` name. Claude's original plugin
identity is unchanged.

## Use the skill

In Codex CLI or the editor extension, select it through `/skills` or mention:

```text
Use $karpathy-guidelines to fix the bug described below.
```

In ChatGPT where the plugin is installed and available, use the `@` selector
to choose Karpathy Guidelines. Automatic activation depends on the task
matching the skill description. Installation does not guarantee activation
for every task and does not grant editing or deletion authorization.

## Install only the skill in a local Codex project

As an alternative to plugin installation, copy the shared skill into a
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

## Optional persistent project guidance

Skills are selected when relevant. For persistent coding guidance, review
`CLAUDE.md` and merge its four principles into the target project's existing
`AGENTS.md`, or use it as the starting content for a new `AGENTS.md`.
Do not overwrite existing instructions. Preserve project requirements and
explicit approval boundaries; reconcile conflicts during the merge.
Installing this plugin does not perform that merge automatically.

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
