#!/usr/bin/env python3
"""Check physical page coverage and a supplied rehearsal budget against the actual PPTX.

No text is generated. Approval, evidence, visual quality and story coherence are not tested.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile

from inspect_inputs import inspect_pptx


def check(deck, plan):
    errors, warnings = [], []
    if not isinstance(plan, dict):
        return {"passed": False, "errors": ["Plan must be an object"], "warnings": []}
    if type(plan.get("schema_version")) is not int or plan.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if plan.get("deck_sha256") != deck["sha256"]:
        errors.append("PPTX hash changed or missing: re-read and remap the actual deck")

    def number(obj, key, label, default=None):
        value = obj.get(key, default)
        if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
            errors.append(f"{label}.{key} must be a finite nonnegative number (unknown is not zero)")
            return 0.0
        return float(value)

    total = number(plan, "presentation_seconds", "plan")
    question = number(plan, "question_seconds", "plan")
    if total <= 0:
        errors.append("presentation_seconds must be positive and exclude the allocated Q&A time")
    buffer_ratio = number(plan, "buffer_ratio", "plan", 0.1)
    if buffer_ratio >= 1:
        errors.append("buffer_ratio must be less than 1")
    rows = plan.get("slides")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return {"passed": False, "errors": errors + ["slides must be a list of objects"], "warnings": warnings}
    pages = [row.get("page") for row in rows]
    if any(type(p) is not int for p in pages) or pages != list(range(1, deck["slide_count"] + 1)):
        errors.append("Each physical page must occur exactly once, in actual PPTX order")
    team_mode = plan.get("team_mode")
    if team_mode not in ("absent", "brief", "detailed", "forbidden"):
        errors.append("team_mode must be absent, brief, detailed or forbidden")
    if team_mode == "forbidden":
        warnings.append("Manually verify all visible identity clues, cover, notes and competition rules")
    speech_total = extra_total = media_total = demo_total = 0.0
    timeline = []
    actual_pages = {s["page"]: s for s in deck["slides"]}
    for index, row in enumerate(rows, 1):
        label = f"entry {index}"
        page = row.get("page")
        actual = actual_pages.get(page) if type(page) is int else None
        if actual is None:
            errors.append(f"{label}: invalid physical page")
            continue
        if row.get("slide_id") != actual["slide_id"]:
            errors.append(f"{label}: slide_id does not match the current physical page")
        mode, role = row.get("mode"), row.get("role")
        if mode not in ("speak", "silent", "media", "skip"):
            errors.append(f"{label}: invalid mode")
        if role not in ("cover", "content", "chapter", "team", "closing", "appendix"):
            errors.append(f"{label}: invalid role")
        narration = row.get("narration")
        if not isinstance(narration, str):
            errors.append(f"{label}: narration must be a string; use empty string for no speech")
            narration = ""
        speech = number(row, "speech_seconds", label)
        extra = number(row, "non_speech_seconds", label)
        media = number(row, "media_seconds", label)
        demo = number(row, "demo_seconds", label, 0)
        if mode in ("silent", "skip") or role == "chapter":
            if narration.strip() or speech != 0:
                errors.append(f"{label}: silent/skipped/chapter page must have no narration or speech time")
        if role == "chapter" and mode not in ("silent", "skip"):
            errors.append(f"{label}: pure chapter page must be silent or skipped")
        if mode == "speak" and not narration.strip():
            errors.append(f"{label}: spoken page is missing narration")
        if bool(narration.strip()) != (speech > 0):
            errors.append(f"{label}: narration and speech_seconds disagree")
        if mode == "skip" and speech + extra + media + demo > 0:
            errors.append(f"{label}: skipped page must not consume presentation time")
        if mode == "skip" and not str(row.get("handling_note", "")).strip():
            errors.append(f"{label}: explain why the page is excluded from main delivery")
        if actual["hidden"] and mode != "skip" and row.get("hidden_use_confirmed") is not True:
            errors.append(f"{label}: hidden slide use needs an explicit confirmed arrangement")
        if role == "team" and team_mode in ("absent", "forbidden"):
            errors.append(f"{label}: team page conflicts with selected team policy; resolve the actual deck")
        handling = row.get("media_handling", "none")
        if handling not in ("none", "play", "not_played", "outside_clock"):
            errors.append(f"{label}: invalid media_handling")
        if actual["has_media"] and handling == "none":
            errors.append(f"{label}: media detected; confirm playback and timing instead of treating it as blank")
        if handling in ("play", "outside_clock", "not_played"):
            if not str(row.get("handling_note", "")).strip():
                errors.append(f"{label}: media handling needs a note describing the confirmed arrangement")
        if handling != "play" and media > 0:
            errors.append(f"{label}: media_seconds only applies to in-clock playback")
        if handling in ("play", "outside_clock"):
            duration = number(row, "playback_seconds", label)
            if duration <= 0:
                errors.append(f"{label}: playback_seconds must be positive for played media")
            if handling == "play":
                overlap = number(row, "overlap_speech_seconds", label)
                if overlap > min(duration, speech):
                    errors.append(f"{label}: speech/media overlap exceeds playback or speech duration")
                if abs(media - (duration - overlap)) > 0.01:
                    errors.append(f"{label}: media_seconds must equal playback minus overlapping speech")
        if media + demo > extra + 0.01:
            errors.append(f"{label}: non_speech_seconds must include exclusive media and demo time")
        speech_total += speech
        extra_total += extra
        media_total += media
        demo_total += demo
        timeline.append({"page": page, "seconds": round(speech + extra, 2),
                         "cumulative_seconds": round(speech_total + extra_total, 2)})

    exclusive = media_total + demo_total
    if exclusive >= total:
        errors.append("Exclusive media/demo time leaves no usable speech budget")
    reserve = max(0, total - exclusive) * buffer_ratio
    planned = speech_total + extra_total
    target = total - reserve
    if planned > total + 0.01:
        errors.append("Planned presentation exceeds the hard presentation limit")
    elif planned > target + 0.01:
        errors.append("Planned presentation uses the configured reserve; shorten or agree a revised reserve")
    warnings.append("Mechanical check only: verify actual user decisions, evidence, narration, visuals and rehearsal separately")
    return {
        "passed": not errors, "errors": errors, "warnings": warnings,
        "timing": {
            "presentation_seconds": total, "question_seconds": question,
            "speech_seconds": round(speech_total, 2), "non_speech_seconds": round(extra_total, 2),
            "exclusive_media_demo_seconds": round(exclusive, 2),
            "reserve_seconds": round(reserve, 2), "target_seconds": round(target, 2),
            "planned_seconds": round(planned, 2), "remaining_seconds": round(total - planned, 2),
        },
        "timeline": timeline,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="Actual final PPTX; checked again on every run")
    parser.add_argument("plan", type=Path, help="Rehearsal JSON described in references/tooling.md")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        result = check(inspect_pptx(args.pptx), plan)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, ET.ParseError, BadZipFile) as exc:
        parser.exit(2, f"Check failed: {exc}\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
