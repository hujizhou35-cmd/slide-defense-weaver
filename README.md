# Slide Defense Weaver

**Tell one coherent story across your slides.**

English · [简体中文](docs/README.zh-CN.md)

![Slide Defense Weaver — turn separate slides into a connected story](docs/assets/hero.svg)

Your defense should help an audience follow an idea from the problem to the evidence and its meaning. Slide Defense Weaver reads your project materials and PPT, identifies that central story, and discusses slide order with you **before drafting**.

You decide whether to revise the slides or keep the current order. Then it prepares three separate Word documents for your defense and rehearsal.

[![Release](https://img.shields.io/github/v/release/hujizhou35-cmd/slide-defense-weaver?color=176B65)](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/latest)
[![MIT](https://img.shields.io/badge/license-MIT-9B7638)](LICENSE)
[![Feedback welcome](https://img.shields.io/badge/feedback-Issues-176B65)](https://github.com/hujizhou35-cmd/slide-defense-weaver/issues)

## Get started

| Download | Choose this when… |
| --- | --- |
| [Full Skill `.skill`](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/slide-defense-weaver-v1.0.0.skill) | You want the skill folder, references, and checking scripts |
| [Plugin `.zip`](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/slide-defense-weaver-plugin-v1.0.0.zip) | You use Codex or Claude Code and want the plugin package |
| [Standalone `SKILL.md`](https://github.com/hujizhou35-cmd/slide-defense-weaver/releases/download/v1.0.0/SKILL.md) | Your AI can read an instruction file; the writing references are included inline |

See the short [installation guide](docs/install.md) for Codex, Claude Code, and other AI tools. The standalone file uses equivalent checklists instead of the packaged Python helpers.

Provide your **project plan, report, or equivalent explanation**, plus your **PPT**. Tell the skill your speaking and Q&A time, or let it ask first. It also checks video time, event rules, and whether team introductions should be brief, detailed, or omitted.

```text
Use Slide Defense Weaver with my project report and PPT.
I have 5 minutes to present and 2 minutes for Q&A, timed separately.
First explain the story you see and suggest any changes to slide order.
Wait for my choice before writing the three defense documents.
```

## Three documents, three ways to prepare

| Output | What you get |
| --- | --- |
| **Slide-by-slide defense script** | Speech matched to the actual PPT pages, connected transitions, timing, and clearly separate slide-change cues |
| **Mock Q&A** | Likely project questions, what the panel is asking, concise answers, follow-up points, and supporting material |
| **Tough-question rehearsal** | Practice for uncomfortable questions about your work, contribution, or evidence, with calm and direct responses |

That third document is also the author's little mischievous touch. Questions such as **“Did you actually do this yourself?”** are easier to face after you have practiced an honest answer. The goal is composure and clarity, not clever put-downs.

## How the story takes shape

![Workflow: confirm time, understand the project, discuss story and order, make your choice, prepare three documents](docs/assets/workflow.svg)

1. **Set the time.** Confirm speaking time and Q&A time, including how videos and demos are counted.
2. **Understand the project.** Read the report and every slide, including important visual content. Ask about missing or conflicting information.
3. **Discuss the story and order.** Explain the full narrative and each slide's job. Recommend specific moves or merges with reasons.
4. **Make your choice.** Revise the PPT first, yourself or with AI assistance, or draft against the current actual order.
5. **Prepare and rehearse.** Deliver the script, mock Q&A, and tough questions as separate Word files.

Pure chapter-divider slides receive **no spoken text**. The transition belongs in the neighboring content pages. Team introductions follow your chosen level of detail and the event's rules.

## A small example

*Fictional project: an equipment handover log.*

**Separate starts**

> “Next, I will introduce the system features. The system records handovers.”
>
> “Next, I will introduce our trial. We ran a user trial.”

**A connected argument**

> “We put the record into the handover step, so it can be captured when equipment changes hands.”
>
> “We then checked whether people could complete that workflow. Ten testers completed the assigned steps; we have not yet measured time savings or long-term use.”

The connection comes from what the work did and what the trial can show. Adding a transition word alone cannot create that relationship.

**Slide-order suggestion:** move the workflow explanation before the trial results, so the audience knows what was tested. If you keep the current order, the script introduces the prototype before reporting the limited result and explains its mechanism afterward.

See the [full short example](docs/example.md), including a tough question and its answer.

## What to expect

- Best suited to project competitions, with support for thesis and research defenses.
- Scripts default to Chinese; request English or another language. Documentation is English-first with a complete Chinese version.
- The AI needs tools to read your files, inspect slides, create Word documents, and render them for layout checking. The package does not install Office, an OCR engine, or a document renderer.
- The Python helpers check page mapping and supplied time budgets. Actual rehearsal is still needed to confirm delivery time.
- Supplied materials and your confirmed explanations support the facts. Missing results or personal contributions are not invented.

## Feedback and source

Have a broken installation, an awkward transition, or a better rehearsal idea? [Open an issue](https://github.com/hujizhou35-cmd/slide-defense-weaver/issues). English and Chinese are both welcome. Use fictional or redacted examples when sharing material.

The current skill lives in `skills/`; package builders and tests live in `development/`. Most users can start with a Release download.

Created by **Jizhou Hu** · [MIT License](LICENSE)
