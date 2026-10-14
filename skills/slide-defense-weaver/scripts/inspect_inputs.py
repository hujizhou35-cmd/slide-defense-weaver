#!/usr/bin/env python3
"""Read OOXML source text/order without modifying documents or loading external links.

Standard library only. This is an inventory, not OCR, rendering or a semantic audit.
"""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import sys
from urllib.parse import unquote
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_part(source, target):
    target = unquote(target).replace("\\", "/")
    part = posixpath.normpath(
        target.lstrip("/") if target.startswith("/")
        else posixpath.join(posixpath.dirname(source), target)
    )
    if part == ".." or part.startswith("../"):
        raise ValueError("Relationship points outside the OOXML package")
    return part


def relationships(archive, source):
    directory, name = posixpath.split(source)
    rel_path = posixpath.join(directory, "_rels", name + ".rels")
    if rel_path not in archive.namelist():
        return {}
    result = {}
    for item in ET.fromstring(archive.read(rel_path)):
        external = item.get("TargetMode") == "External"
        target = item.get("Target", "")
        result[item.get("Id")] = {
            "type": item.get("Type", "").rsplit("/", 1)[-1],
            "target": target if external else target_part(source, target),
            "external": external,
        }
    return result


def drawing_paragraphs(root):
    return [
        "".join(node.text or "" for node in p.findall(".//a:t", NS))
        for p in root.findall(".//a:p", NS)
    ]


def inspect_pptx(path):
    with ZipFile(path) as archive:
        part = "ppt/presentation.xml"
        presentation = ET.fromstring(archive.read(part))
        rels = relationships(archive, part)
        slide_list = presentation.find("p:sldIdLst", NS)
        if slide_list is None:
            raise ValueError("No supported presentation slide list found")
        slides = []
        for index, slide_id in enumerate(slide_list, 1):
            rid = slide_id.get("{" + NS["r"] + "}id")
            rel = rels[rid]
            if rel["external"] or rel["type"] != "slide":
                raise ValueError("Invalid slide relationship")
            slide_part = rel["target"]
            root = ET.fromstring(archive.read(slide_part))
            slide_rels = relationships(archive, slide_part)
            notes = []
            charts = []
            for link in slide_rels.values():
                if not link["external"] and link["type"] == "notesSlide":
                    notes.extend(drawing_paragraphs(ET.fromstring(archive.read(link["target"]))))
                if not link["external"] and link["type"] == "chart":
                    chart = ET.fromstring(archive.read(link["target"]))
                    charts.append({
                        "part": link["target"],
                        "text": [n.text for n in chart.iter()
                                 if n.tag.rsplit("}", 1)[-1] in {"t", "v"} and n.text],
                    })
            media = [link for link in slide_rels.values()
                     if link["type"].lower() in {"video", "audio", "media"}]
            media_nodes = [n.tag.rsplit("}", 1)[-1] for n in root.iter()
                           if n.tag.rsplit("}", 1)[-1] in
                           {"videoFile", "audioFile", "wavAudioFile", "media"}]
            paragraphs = [s for s in drawing_paragraphs(root) if s.strip()]
            slides.append({
                "page": index,
                "slide_id": slide_id.get("id"),
                "part": slide_part,
                "hidden": root.get("show", "1").lower() in {"0", "false", "off"},
                "text": paragraphs,
                "notes": [s for s in notes if s.strip()],
                "picture_count": len(root.findall(".//p:pic", NS)),
                "alt_text": [n.get("descr") for n in root.findall(".//p:cNvPr", NS)
                             if n.get("descr")],
                "charts": charts,
                "has_media": bool(media or media_nodes),
                "media": media,
                "external_links": [link for link in slide_rels.values() if link["external"]],
                "requires_visual_review": True,
                "classification": "unclassified",
            })
    return {
        "schema_version": 1, "kind": "pptx", "file_name": Path(path).name,
        "sha256": sha256(path), "slide_count": len(slides), "slides": slides,
        "limitations": [
            "No OCR or rendering; missing text never means an empty/section slide.",
            "Text order inside a slide is XML order, not guaranteed visual reading order.",
            "No media playback/duration measurement; no external links are opened.",
            "Layout/master text, animations and embedded objects need visual inspection.",
        ],
    }


def inspect_docx(path):
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        body = root.find("w:body", NS)
        if body is None:
            raise ValueError("No supported Word document body found")
        paragraphs = []
        for index, p in enumerate(body.findall(".//w:p", NS), 1):
            text = "".join(node.text or "" for node in p.findall(".//w:t", NS))
            if text.strip():
                paragraphs.append({"paragraph": index, "text": text})
        return {
            "schema_version": 1, "kind": "docx", "file_name": Path(path).name,
            "sha256": sha256(path), "paragraphs": paragraphs,
            "drawing_count": len(root.findall(".//w:drawing", NS)),
            "has_tracked_changes": bool(root.findall(".//w:ins", NS) or root.findall(".//w:del", NS)),
            "limitations": [
                "Body text only, including table paragraphs; no rendered page numbers.",
                "Images, equations, headers, footnotes and tracked changes need separate review.",
            ],
        }


def inspect(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".pptx":
        return inspect_pptx(path)
    if suffix == ".docx":
        return inspect_docx(path)
    raise ValueError("Only .pptx and .docx are supported; use a document tool for other formats")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, help="New JSON file; refuses to overwrite any existing file")
    args = parser.parse_args()
    try:
        result = inspect(args.input)
        data = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            with args.out.open("x", encoding="utf-8") as output:
                output.write(data + "\n")
        else:
            print(data)
    except (OSError, ValueError, KeyError, ET.ParseError, BadZipFile) as exc:
        parser.exit(2, f"Inspection failed: {exc}\n")


if __name__ == "__main__":
    main()
