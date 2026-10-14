# 安装与使用

[English](install.md) · [项目主页](README.zh-CN.md)

选择一种方式即可。同一个客户端同时安装独立 Skill 和 Plugin，可能显示重复的技能。

## Codex 插件

在支持插件的 Codex CLI 中执行：

```sh
codex plugin marketplace add hujizhou35-cmd/slide-defense-weaver
codex plugin add slide-defense-weaver@slide-defense-weaver
```

开启新聊天，要求使用 **Slide Defense Weaver**。包内技能名称为 `slide-defense-weaver`。

使用本地下载时，把 [Plugin ZIP](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/slide-defense-weaver-plugin-v1.0.0.zip) 解压到独立目录，再将第一条命令里的仓库名称换成该目录路径。包中包含本地插件目录清单和插件元数据。

## Claude Code 插件

在 Claude Code 中执行：

```text
/plugin marketplace add hujizhou35-cmd/slide-defense-weaver
/plugin install slide-defense-weaver@slide-defense-weaver
```

开启新会话，通过 `/slide-defense-weaver:slide-defense-weaver` 调用，或直接要求使用该技能。终端命令对应 `claude plugin marketplace add ...` 和 `claude plugin install ...`。

只想在单次会话中加载时，下载 Plugin ZIP，然后执行：

```sh
claude --plugin-dir ./slide-defense-weaver-plugin-v1.0.0.zip
```

插件没有 hooks、MCP 服务，也不需要另外配置 API Key。

## 完整 Skill 目录

[`.skill` 文件](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/slide-defense-weaver-v1.0.0.skill) 实际是 ZIP 压缩包，内部只有一个 `slide-defense-weaver/` 目录。客户端提供兼容的技能导入入口时可直接导入；否则用 ZIP 工具解压。若压缩工具不识别，可把文件副本的后缀改为 `.zip`。

项目内安装时，将该目录放入 Codex 的 `.agents/skills/`，或 Claude Code 的 `.claude/skills/`。保留 `references/`、`scripts/`、`agents/` 等文件，随后在该项目中开启新会话。Codex 可用 `$slide-defense-weaver` 调用，Claude Code 的独立技能可用 `/slide-defense-weaver` 调用。

## 其他 AI

下载[独立 `SKILL.md`](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/SKILL.md)，上传给能够读取指令文件的 AI，并要求按其中流程执行。写作参考已内联，检查清单替代 Python 辅助脚本，不会假称已经运行脚本。

## 需要的材料与工具

提供 PPT，以及项目报告、计划书、论文或等价说明，并确认陈述和提问时长。讲稿默认中文，可要求其他语言。

AI 所在环境需能读取文件、检查幻灯片画面、生成 Word 并渲染检查。两个可选的 Python 辅助脚本需要 Python 3.10+ 及其标准库；安装插件不会自动安装 Office、LibreOffice、OCR 或其他文档工具。

## 验证范围

发布检查验证包结构、技能资源一致性、文档引用和辅助脚本测试。客户端检查单独验证清单能否接受、插件能否安装及技能能否发现。这些检查不代表所有客户端都具备文档渲染工具，也不代表未来所有答辩都能自动满足时限。

安装失败可[提交 Issue](https://github.com/hujizhou35-cmd/slide-defense-weaver/issues)，说明客户端版本、使用的文件及简短报错。请不要附带凭据或保密项目文件。
