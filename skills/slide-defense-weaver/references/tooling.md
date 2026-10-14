# 轻量辅助脚本

脚本只需Python 3标准库，无需联网或额外安装。使用当前环境提供的Python；以下命令以技能目录为工作目录。路径由任务实际文件决定，不写死案例路径。

```text
python scripts/inspect_inputs.py "项目.pptx" --out "ppt-inventory.json"
python scripts/inspect_inputs.py "计划书.docx" --out "document-inventory.json"
python scripts/check_alignment.py "最终PPT.pptx" "rehearsal.json"
```

`inspect_inputs.py`默认将JSON写到标准输出；`--out`只创建新文件，拒绝覆盖已有文件，包括原始输入。不会打开外部链接，也不会修改PPT或Word。暂不支持旧版PPT/DOC、PDF或在线文档，使用环境中的相应阅读工具处理，不把扩展名改一下冒充转换。

## 能与不能检查的内容

- 按 `presentation.xml` 的真实顺序解析页面关系，不能按 `slide1.xml` 文件名排序。
- 输出每页物理页码、内部slide_id、源part、文本、备注、图表文字/数值、图片数量、媒体和外链线索、隐藏状态；整份文件计算SHA-256供版本核对。
- 所有页面保持 `unclassified` 并要求视觉审查，绝不自动把无文本页归为章节页。
- Word输出正文段落（包括表格内段落）及段落索引，不伪造纸张页码。图片、公式、脚注、页眉、修订等需另外检查。
- 不执行OCR、渲染、媒体时长检测、证据验证或语言评分。XML中的文本顺序不等于视觉阅读顺序，母版/布局文字和动画需另看。

## 计时检查输入

`rehearsal.json` 是内部排稿记录，不必交付用户。由代理根据已确认信息填入；它记录用户决定，不能取代对话中的真实确认。下面仅为结构示例，哈希和ID必须换成实际读取值，条目必须覆盖实际全部页面。

```json
{
  "schema_version": 1,
  "deck_sha256": "从最终PPT读取的实际SHA256",
  "presentation_seconds": 300,
  "question_seconds": 120,
  "buffer_ratio": 0.1,
  "team_mode": "brief",
  "slides": [
    {
      "page": 1,
      "slide_id": "256",
      "role": "cover",
      "mode": "speak",
      "narration": "各位评委老师好，今天汇报的是……",
      "speech_seconds": 10,
      "non_speech_seconds": 1,
      "media_seconds": 0,
      "demo_seconds": 0,
      "media_handling": "none"
    }
  ]
}
```

所有时间单位是秒，必须有限且非负，不接受字符串、布尔值、NaN或用null代表已知的零。问题时长未知要先问，没有提问环节经用户明确后才填0。`presentation_seconds`只放已分配给正式陈述的时间。

`team_mode`：`absent`（材料中没有团队部分）、`brief`、`detailed`、`forbidden`。`role`由看过页面的代理确定，支持 `cover/content/chapter/team/closing/appendix`。`mode`：`speak`（讲述）、`silent`（无声翻过）、`media`（媒体为主，可有口播）、`skip`（主讲不展示）。纯章节页只能silent或skip，无正文、无口播时间。skip须写`handling_note`解释原因，并且计入陈述的时间全为0。

每页 `speech_seconds` 是估算或排练的口播用时；`non_speech_seconds` 是不与口播重叠、计入正式陈述的全部媒体、演示、翻页和停顿时间。`media_seconds`、可选的`demo_seconds`是其中媒体和演示的独占时间，**它们是子集，不再加到总时间上**。同一独占时段不可同时记入media和demo。

检测到媒体时必须明确 `media_handling`：

| 值 | 需要记录 |
| --- | --- |
| `play` | `playback_seconds`实际播放总秒数、`overlap_speech_seconds`其中与口播重叠的秒数，以及`handling_note`。`media_seconds = playback_seconds − overlap_speech_seconds` |
| `not_played` | `handling_note`解释为什么不用；媒体计时为0，不能默认忽略 |
| `outside_clock` | `playback_seconds`及`handling_note`说明用户确认不占正式陈述；媒体计时为0 |
| `none` | 仅用于没有媒体安排的页面 |

例如视频总40秒，其中15秒一边播放一边讲，`media_seconds=25`，口播时间包含这15秒，`non_speech_seconds`至少25秒。外部媒体可在未嵌入PPT的页面手动记录；脚本不会自动发现现场演示安排。

隐藏页默认skip。用户确认要用于主讲时，在对应条目记 `hidden_use_confirmed: true` 并记录具体操作；此标记只记录决定，不能自动取消隐藏或证明已经获得同意。

## 结果解释

检查器每次直接读取实际PPT，核对哈希、内部ID、顺序和完整覆盖，检查无声章节页、隐藏页安排和计时矛盾，给出逐页/累计时间。退出码0表示这些机械检查通过；1表示检查不通过；2表示输入或读取失败。

哈希变化即重新读取并核对，即使只是修改了PPT文字也不自动忽略。章节角色和团队政策由代理填写，因此检查器不能发现所有误分类、身份泄露或缺失证据。`passed: true`不证明故事连贯、Word美观、用户已确认，也不证明实际排练不超时。
