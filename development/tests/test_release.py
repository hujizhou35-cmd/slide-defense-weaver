import importlib.util
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('builder',ROOT/'development/scripts/build_release.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ReleaseTest(unittest.TestCase):
    def test_client_manifest_identity_and_prompt_limit(self):
        import json
        codex=json.loads((ROOT/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        claude=json.loads((ROOT/'.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        for key in ('name','version','author','license'):
            self.assertEqual(codex[key],claude[key])
        self.assertLessEqual(len(codex['interface']['defaultPrompt']),128)

    def test_repeat_build_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as temp:
            a,b=Path(temp)/'a',Path(temp)/'b'
            self.assertEqual(builder.build(ROOT,a),builder.build(ROOT,b))

    def test_all_formats_share_runtime_and_exclude_development(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);builder.build(ROOT,out)
            with ZipFile(out/'slide-defense-weaver-v1.0.0.skill') as skill, ZipFile(out/'slide-defense-weaver-plugin-v1.0.0.zip') as plugin:
                for name in skill.namelist():
                    if name.endswith('/LICENSE'):continue
                    self.assertEqual(skill.read(name),plugin.read('skills/'+name))
                for names in (skill.namelist(),plugin.namelist()):
                    self.assertFalse(any('development/' in n or 'tests/' in n or '__pycache__' in n for n in names))

    def test_portable_contains_references_and_no_relative_links(self):
        import re
        text=builder.portable(ROOT/'skills/slide-defense-weaver')
        self.assertNotRegex(text,r'\]\((?!https?://|#)[^)]+\)')
        self.assertIn('不附带Python脚本',text)
        self.assertIn('无声翻过',text)
        self.assertIn('用户指定的工作流程',text)
        for anchor in re.findall(r'\]\(#([^)]*)\)',text):
            self.assertIn(f'id="{anchor}"',text)


if __name__=='__main__':unittest.main()
