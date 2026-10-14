#!/usr/bin/env python3
"""Build exactly three deterministic release assets from one Git ref."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
NAME = "slide-defense-weaver"
STAMP = (2026, 1, 1, 0, 0, 0)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def entries(root):
    return sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')


def archive(path, payload):
    with ZipFile(path, 'w', compression=ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(payload.items()):
            info = ZipInfo(name, STAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, content, compress_type=ZIP_DEFLATED, compresslevel=9)


def portable(skill):
    anchors = {'storycraft': 'storycraft', 'deliverables': 'deliverables', 'qa-guide': 'qa-guide', 'tooling': 'portable-checks'}
    def inline_links(text):
        return re.sub(r'\]\(references/([a-z-]+)\.md\)', lambda m: '](#'+anchors[m[1]]+')', text).replace('](qa-guide.md)', '](#qa-guide)')
    main = (skill/'SKILL.md').read_text(encoding='utf-8')
    main = main.replace('可用 [辅助脚本](references/tooling.md) 提取真实页序、文本和媒体清单', '可按 [独立文件检查方法](#portable-checks) 核对真实页序、文本和媒体清单')
    main = main.replace('运行辅助检查；报错修复后重跑。', '按独立文件检查清单逐项核对，修正发现的问题。')
    sections = [inline_links(main).rstrip(),
        '\n<a id="portable-checks"></a>\n# 独立文件使用与检查\n',
        '本文件已内联写作参考，可作为指令文件交给AI读取。它不附带Python脚本；不要执行或声称已执行不存在的辅助文件。若AI能读取PPT并生成Word，使用其现有工具完成；没有相应能力时说明具体限制并索要可读取的材料，不把文本输出冒充Word。',
        '逐页核对：直接读取最终PPT的实际物理顺序，包含隐藏和备用页，每页建立一个条目。核对页序、主题与画面；图片或视频页无文字时仍须视觉检查。章节页正文为空，团队按已确认规则处理。修改PPT后重新核对全部对应关系。',
        '时间核对：陈述和问答按用户确认分配。逐页记录口播、非重叠媒体/演示、停顿及翻页时间；媒体与口播重叠只计一次。求和后按下文时间算法检查上限和缓冲，未知时间先问，不填零。',
        '事实与质量核对：核对材料出处和冲突，再把全部口播连接起来通读；实际生成三个Word文件后渲染并逐页检查。手工核对与工具检查如实区分，不把清单完成说成真人排练。',
    ]
    for name in ('storycraft','deliverables','qa-guide'):
        sections.append(f'\n<a id="{name}"></a>\n')
        sections.append(inline_links((skill/'references'/f'{name}.md').read_text(encoding='utf-8')).rstrip())
    return '\n\n'.join(sections)+'\n'


def build(source, output):
    output.mkdir(parents=True, exist_ok=True)
    codex = json.loads((source/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    claude = json.loads((source/'.claude-plugin/plugin.json').read_text(encoding='utf-8'))
    for key in ('name','version','author','license'):
        if codex[key] != claude[key]: raise ValueError('Plugin metadata mismatch: '+key)
    version = codex['version']
    skill = source/'skills'/NAME
    runtime = {p.relative_to(skill).as_posix(): p.read_bytes() for p in entries(skill)}
    runtime['LICENSE'] = (source/'LICENSE').read_bytes()
    skill_out = output/f'{NAME}-v{version}.skill'
    plugin_out = output/f'{NAME}-plugin-v{version}.zip'
    md_out = output/'SKILL.md'
    archive(skill_out, {NAME+'/'+name: data for name,data in runtime.items()})
    plugin = {'skills/'+NAME+'/'+name:data for name,data in runtime.items() if name!='LICENSE'}
    for name in ('LICENSE','.codex-plugin/plugin.json','.claude-plugin/plugin.json',
                 '.claude-plugin/marketplace.json','.agents/plugins/marketplace.json'):
        plugin[name] = (source/name).read_bytes()
    archive(plugin_out, plugin)
    md_out.write_bytes(portable(skill).encode('utf-8'))
    return {p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in (md_out,skill_out,plugin_out)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='sdw-release-') as temp:
        temp=Path(temp)
        subprocess.run(['git','archive','--format=zip','-o',str(temp/'source.zip'),args.ref],cwd=ROOT,check=True)
        with ZipFile(temp/'source.zip') as z:z.extractall(temp/'source')
        result=build(temp/'source',args.output.resolve())
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
