#!/usr/bin/env python3
"""Check the public source allowlist, local links, manifests, and release payloads."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
NAME='slide-defense-weaver'
FIXED={
    'README.md','LICENSE','.gitignore','.gitattributes',
    '.codex-plugin/plugin.json','.claude-plugin/plugin.json','.claude-plugin/marketplace.json',
    '.agents/plugins/marketplace.json','.github/workflows/check.yml',
    '.github/ISSUE_TEMPLATE/bug.yml','.github/ISSUE_TEMPLATE/idea.yml','.github/ISSUE_TEMPLATE/config.yml',
    'docs/README.zh-CN.md','docs/install.md','docs/install.zh-CN.md','docs/example.md',
    'docs/example.zh-CN.md','docs/releases/v1.0.0.zh-CN.md',
    'docs/assets/hero.svg','docs/assets/workflow.svg','development/acceptance.md',
    'development/scripts/build_release.py','development/scripts/verify_public.py',
    'development/tests/test_helpers.py','development/tests/test_release.py',
    'skills/slide-defense-weaver/SKILL.md','skills/slide-defense-weaver/agents/openai.yaml',
    'skills/slide-defense-weaver/references/storycraft.md',
    'skills/slide-defense-weaver/references/deliverables.md',
    'skills/slide-defense-weaver/references/qa-guide.md',
    'skills/slide-defense-weaver/references/tooling.md',
    'skills/slide-defense-weaver/scripts/inspect_inputs.py',
    'skills/slide-defense-weaver/scripts/check_alignment.py',
}


def verify(dist=None):
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    unexpected=set(tracked)-FIXED
    missing=FIXED-set(tracked)
    assert not unexpected, f'Unexpected public files: {unexpected}'
    assert not missing, f'Missing public files: {missing}'
    for name in tracked:
        p=ROOT/name
        text=p.read_text(encoding='utf-8')
        # Public files must not expose local user paths or real project source documents.
        assert not re.search(r'[A-Z]:[\\/]',text),name
        assert not any(s in text for s in ('LENO'+'VO','智护'+'脑康')),name
        if p.suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if '://' in link or link.startswith('#') or link.startswith('mailto:'):continue
                assert (p.parent/link.split('#')[0]).exists(),f'{name}: broken link {link}'
    codex=json.loads((ROOT/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    claude=json.loads((ROOT/'.claude-plugin/plugin.json').read_text(encoding='utf-8'))
    for key in ('name','version','author','license'):assert codex[key]==claude[key],key
    if dist:
        version=codex['version']
        expected={'SKILL.md',f'{NAME}-v{version}.skill',f'{NAME}-plugin-v{version}.zip'}
        assert {p.name for p in dist.iterdir() if p.is_file()}==expected,'Release must have exactly three assets'
        for archive in dist.iterdir():
            if archive.suffix not in {'.zip','.skill'}:continue
            with ZipFile(archive) as z:
                assert z.testzip() is None
                names=z.namelist()
                assert not any(s in n for n in names for s in ('__pycache__','development/','example/','.git/','tests/'))
                assert not any(n.startswith('/') or '..' in n.split('/') for n in names)
                if archive.suffix=='.skill':
                    assert NAME+'/SKILL.md' in names
                    assert NAME+'/LICENSE' in names
                else:
                    assert '.codex-plugin/plugin.json' in names and '.claude-plugin/plugin.json' in names
        portable=(dist/'SKILL.md').read_text(encoding='utf-8')
        assert portable.startswith('---\nname: '+NAME)
        assert not re.search(r'\]\((?!https?://|#)[^)]+\)',portable),'Portable instructions still depend on local files'
        assert '本文件已内联写作参考' in portable
        for critical in ('无声翻过','等待答复','不卑不亢','三个独立Word文件'):assert critical in portable,critical
    return {'public_files':len(tracked),'distribution_checked':bool(dist),'passed':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.dist.resolve() if args.dist else None),ensure_ascii=False))
