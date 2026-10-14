"""Behavioral invariants for OOXML extraction and timing; no model-quality claims."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "slide-defense-weaver"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from inspect_inputs import inspect, inspect_pptx, sha256
from check_alignment import check

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def fixture(path):
    with ZipFile(path, "w") as z:
        z.writestr("ppt/presentation.xml", f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>'
                   '<p:sldId id="901" r:id="rA"/><p:sldId id="202" r:id="rB"/>'
                   '<p:sldId id="707" r:id="rC"/></p:sldIdLst></p:presentation>')
        z.writestr("ppt/_rels/presentation.xml.rels", f'<Relationships xmlns="{PKG}">'
                   f'<Relationship Id="rA" Type="{R}/slide" Target="slides/slide9.xml"/>'
                   f'<Relationship Id="rB" Type="{R}/slide" Target="slides/slide2.xml"/>'
                   f'<Relationship Id="rC" Type="{R}/slide" Target="/ppt/slides/slide7.xml"/>'
                   '</Relationships>')
        z.writestr("ppt/slides/slide9.xml", f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld>'
                   '<a:p><a:r><a:t>第一章</a:t></a:r></a:p></p:cSld></p:sld>')
        z.writestr("ppt/slides/slide2.xml", f'<p:sld xmlns:p="{P}" xmlns:a="{A}" show="0">'
                   '<p:cSld><a:p><a:r><a:t>研究证据</a:t></a:r></a:p></p:cSld></p:sld>')
        z.writestr("ppt/slides/slide7.xml", f'<p:sld xmlns:p="{P}" xmlns:a="{A}">'
                   '<p:cSld><p:pic><p:nvPicPr><p:cNvPr id="1" name="video" descr="演示画面"/>'
                   '</p:nvPicPr></p:pic><a:videoFile/></p:cSld></p:sld>')
        z.writestr("ppt/slides/_rels/slide7.xml.rels", f'<Relationships xmlns="{PKG}">'
                   f'<Relationship Id="video" Type="{R}/video" Target="../media/clip.mp4"/>'
                   f'<Relationship Id="ext" Type="{R}/hyperlink" Target="https://example.invalid/never-open" TargetMode="External"/>'
                   f'<Relationship Id="notes" Type="{R}/notesSlide" Target="../notesSlides/notesSlide1.xml"/>'
                   '</Relationships>')
        z.writestr("ppt/notesSlides/notesSlide1.xml", f'<p:notes xmlns:p="{P}" xmlns:a="{A}">'
                   '<a:p><a:r><a:t>先确认播放时间</a:t></a:r></a:p></p:notes>')
        z.writestr("ppt/media/clip.mp4", b"synthetic-media-not-playable")


def rehearsal(deck):
    return {
        "schema_version": 1, "deck_sha256": deck["sha256"],
        "presentation_seconds": 100, "question_seconds": 60,
        "team_mode": "absent", "buffer_ratio": 0.1,
        "slides": [
            {"page": 1, "slide_id": "901", "role": "chapter", "mode": "silent",
             "narration": "", "speech_seconds": 0, "non_speech_seconds": 1, "media_seconds": 0},
            {"page": 2, "slide_id": "202", "role": "appendix", "mode": "skip",
             "narration": "", "speech_seconds": 0, "non_speech_seconds": 0,
             "media_seconds": 0, "handling_note": "备用，不展示"},
            {"page": 3, "slide_id": "707", "role": "content", "mode": "media",
             "narration": "这里展示已经完成的操作。", "speech_seconds": 20,
             "non_speech_seconds": 30, "media_seconds": 30, "media_handling": "play",
             "playback_seconds": 40, "overlap_speech_seconds": 10,
             "handling_note": "视频40秒，其中10秒与口播重叠"},
        ],
    }


class HelpersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "测试.pptx"
        fixture(self.path)
        self.deck = inspect_pptx(self.path)
        self.plan = rehearsal(self.deck)

    def assertFails(self, text):
        result = check(self.deck, self.plan)
        self.assertFalse(result["passed"])
        self.assertIn(text, "\n".join(result["errors"]))

    def test_physical_order_not_filename_order(self):
        self.assertEqual([s["part"] for s in self.deck["slides"]],
                         ["ppt/slides/slide9.xml", "ppt/slides/slide2.xml", "ppt/slides/slide7.xml"])
        self.assertEqual([s["slide_id"] for s in self.deck["slides"]], ["901", "202", "707"])

    def test_image_video_page_never_classified_as_blank(self):
        slide = self.deck["slides"][2]
        self.assertEqual(slide["text"], [])
        self.assertTrue(slide["has_media"])
        self.assertEqual(slide["classification"], "unclassified")
        self.assertTrue(slide["requires_visual_review"])
        self.assertEqual(slide["picture_count"], 1)
        self.assertEqual(slide["notes"], ["先确认播放时间"])
        self.assertEqual(slide["media"][0]["target"], "ppt/media/clip.mp4")
        self.assertTrue(slide["external_links"][0]["external"])

    def test_hidden_slide_is_preserved(self):
        self.assertTrue(self.deck["slides"][1]["hidden"])
        self.assertEqual(self.deck["slide_count"], 3)

    def test_valid_budget_does_not_double_count_media_or_add_qa(self):
        result = check(self.deck, self.plan)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["timing"]["planned_seconds"], 51)
        self.assertEqual(result["timing"]["reserve_seconds"], 7)
        self.assertEqual(result["timing"]["target_seconds"], 93)
        self.assertEqual(result["timeline"][-1]["cumulative_seconds"], 51)

    def test_missing_duplicate_and_reordered_pages(self):
        for rows in [self.plan["slides"][:-1], self.plan["slides"] + self.plan["slides"][:1],
                     list(reversed(self.plan["slides"]))]:
            with self.subTest(rows=rows):
                plan = copy.deepcopy(self.plan)
                plan["slides"] = rows
                self.assertFalse(check(self.deck, plan)["passed"])

    def test_changed_ppt_requires_new_mapping(self):
        self.plan["deck_sha256"] = "old hash"
        self.assertFails("hash changed")

    def test_id_mismatch(self):
        self.plan["slides"][0]["slide_id"] = "202"
        self.assertFails("slide_id does not match")

    def test_chapter_cannot_have_speech(self):
        self.plan["slides"][0].update(narration="下面进入第一章", speech_seconds=5)
        self.assertFails("chapter page must have no narration")

    def test_unknown_negative_bool_and_nonfinite_times_rejected(self):
        for value in [None, -1, True, float("nan"), float("inf"), "60"]:
            with self.subTest(value=value):
                plan = copy.deepcopy(self.plan)
                plan["question_seconds"] = value
                self.assertFalse(check(self.deck, plan)["passed"])

    def test_hidden_page_cannot_be_activated_silently(self):
        self.plan["slides"][1].update(mode="speak", narration="补充结果", speech_seconds=5)
        self.assertFails("hidden slide use")
        self.plan["slides"][1]["hidden_use_confirmed"] = True
        self.assertTrue(check(self.deck, self.plan)["passed"])

    def test_media_cannot_be_ignored(self):
        self.plan["slides"][2]["media_handling"] = "none"
        self.assertFails("media detected")

    def test_overlap_and_exclusive_media_checked(self):
        self.plan["slides"][2]["overlap_speech_seconds"] = 30
        self.assertFails("overlap exceeds")

    def test_media_cannot_exceed_non_speech_container(self):
        self.plan["slides"][2]["non_speech_seconds"] = 10
        self.assertFails("must include exclusive media")

    def test_outside_clock_media_not_added_to_presentation(self):
        self.plan["slides"][2].update(media_handling="outside_clock", media_seconds=0,
                                    non_speech_seconds=0, handling_note="已确认播放不计时")
        result = check(self.deck, self.plan)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["timing"]["planned_seconds"], 21)

    def test_hard_limit_and_reserve_are_separate(self):
        for speech, error in [(100, "hard presentation limit"), (65, "configured reserve")]:
            with self.subTest(speech=speech):
                self.plan["slides"][2]["speech_seconds"] = speech
                self.assertFails(error)

    def test_forbidden_team_requires_actual_deck_resolution(self):
        self.plan["team_mode"] = "forbidden"
        self.plan["slides"][0]["role"] = "team"
        self.assertFails("team page conflicts")

    def test_each_allowed_team_style(self):
        for policy in ["brief", "detailed"]:
            with self.subTest(policy=policy):
                plan = copy.deepcopy(self.plan)
                plan["team_mode"] = policy
                plan["slides"][0].update(role="team", mode="speak", narration="分工说明", speech_seconds=5)
                self.assertTrue(check(self.deck, plan)["passed"])

    def test_demo_reserve_subtracts_only_exclusive_time(self):
        self.plan["slides"][2].update(demo_seconds=5, non_speech_seconds=35)
        result = check(self.deck, self.plan)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["timing"]["reserve_seconds"], 6.5)
        self.assertEqual(result["timing"]["planned_seconds"], 56)

    def test_malformed_rows_report_failure(self):
        for bad in [None, {}, ["bad row"], [1]]:
            with self.subTest(bad=bad):
                plan = copy.deepcopy(self.plan)
                plan["slides"] = bad
                self.assertFalse(check(self.deck, plan)["passed"])

    def test_docx_body_table_and_change_flag(self):
        path = Path(self.tmp.name) / "计划.docx"
        w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        with ZipFile(path, "w") as z:
            z.writestr("word/document.xml", f'<w:document xmlns:w="{w}"><w:body>'
                       '<w:p><w:r><w:t>项目说明</w:t></w:r></w:p><w:tbl><w:tr><w:tc>'
                       '<w:p><w:ins><w:r><w:t>待审核数据</w:t></w:r></w:ins></w:p>'
                       '</w:tc></w:tr></w:tbl></w:body></w:document>')
        result = inspect(path)
        self.assertEqual([p["text"] for p in result["paragraphs"]], ["项目说明", "待审核数据"])
        self.assertTrue(result["has_tracked_changes"])

    def test_cli_never_overwrites_source(self):
        before = sha256(self.path)
        script = SKILL_ROOT / "scripts" / "inspect_inputs.py"
        result = subprocess.run([sys.executable, str(script), str(self.path), "--out", str(self.path)],
                                capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(sha256(self.path), before)

    def test_cli_checker(self):
        plan_path = Path(self.tmp.name) / "rehearsal.json"
        plan_path.write_text(json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")
        script = SKILL_ROOT / "scripts" / "check_alignment.py"
        result = subprocess.run([sys.executable, str(script), str(self.path), str(plan_path)],
                                capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["passed"])


if __name__ == "__main__":
    unittest.main()
