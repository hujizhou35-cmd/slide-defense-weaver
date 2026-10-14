# Install and use

[简体中文](install.zh-CN.md) · [Project homepage](../README.md)

Choose one route. Installing both the standalone skill and the plugin in the same client may expose duplicate copies.

## Codex plugin

With a Codex CLI that supports plugins:

```sh
codex plugin marketplace add hujizhou35-cmd/slide-defense-weaver
codex plugin add slide-defense-weaver@slide-defense-weaver
```

Start a new chat and ask to use **Slide Defense Weaver**. The packaged skill is named `slide-defense-weaver`.

For a local download, extract the [Plugin ZIP](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/slide-defense-weaver-plugin-v1.0.0.zip) into a folder, then replace the first command's repository name with that folder's path. It contains the local marketplace catalog and plugin metadata.

## Claude Code plugin

In Claude Code:

```text
/plugin marketplace add hujizhou35-cmd/slide-defense-weaver
/plugin install slide-defense-weaver@slide-defense-weaver
```

Start a new session and invoke `/slide-defense-weaver:slide-defense-weaver`, or ask to use the skill by name. CLI equivalents are `claude plugin marketplace add ...` and `claude plugin install ...`.

To load only for one session, download the Plugin ZIP and run:

```sh
claude --plugin-dir ./slide-defense-weaver-plugin-v1.0.0.zip
```

The plugin uses no hooks, MCP server, or separate API key.

## Full skill folder

The [`.skill` file](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/slide-defense-weaver-v1.0.0.skill) is a ZIP archive containing one `slide-defense-weaver/` folder. If your client provides a compatible Skill import, use it. Otherwise extract it with a ZIP tool; renaming a copy from `.skill` to `.zip` may help your archive tool recognize it.

For a project-local install, place that folder under `.agents/skills/` for Codex, or `.claude/skills/` for Claude Code. Keep its `references/`, `scripts/`, and `agents/` contents together. Open a new session in that project. Codex can invoke `$slide-defense-weaver`; the standalone Claude Code skill can invoke `/slide-defense-weaver`.

## Another AI tool

Download [standalone `SKILL.md`](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/SKILL.md), upload it to an AI that can read instruction files, and ask it to follow the workflow. Its writing references are inline. Its manual checklists replace the Python helpers; it does not pretend those helpers ran.

## Files and tools you need

Supply a PPT and a project report, plan, thesis, or equivalent explanation. Confirm speaking time and Q&A time. Scripts default to Chinese; specify another language if needed.

The AI environment must support file reading, visual slide inspection, Word generation, and document rendering. The two optional Python helpers need Python 3.10+ and its standard library. A plugin installation does not install Office, LibreOffice, OCR, or other document tools.

## Validation scope

Release checks verify package structure, matching skill resources, references, and the deterministic helper tests. Client checks separately verify manifest acceptance, plugin installation, and skill discovery. These checks do not establish that every client has document-rendering tools, or that every future defense will meet its time limit.

If installation fails, [open an issue](https://github.com/hujizhou35-cmd/slide-defense-weaver/issues) with your client version, chosen file, and a short error message. Please omit credentials and confidential project files.
