from __future__ import annotations

import json
import shutil
from pathlib import Path

import win32com.client  # type: ignore


DOC_PATH = Path(r"C:\Users\挣谋\Downloads\毕设论文.doc")
WORK_ROOT = Path(r"E:\CTpath-master")
OUT_DIR = WORK_ROOT / "_tmp_doc_images"
HTML_DIR = OUT_DIR / "html"
META_PATH = OUT_DIR / "image_map.json"


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def paragraph_text(paragraphs, index: int) -> str:
    if index < 1 or index > paragraphs.Count:
        return ""
    return paragraphs(index).Range.Text.replace("\r", "").replace("\x07", "").strip()


def main() -> None:
    ensure_clean_dir(OUT_DIR)
    ensure_clean_dir(HTML_DIR)

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(str(DOC_PATH), ReadOnly=True)
        # Save as filtered HTML so Word exports embedded images to a sibling folder.
        html_path = HTML_DIR / "thesis.html"
        doc.SaveAs(str(html_path), FileFormat=10)

        paragraphs = doc.Paragraphs
        mappings: list[dict[str, object]] = []

        for idx in range(1, doc.InlineShapes.Count + 1):
            shape = doc.InlineShapes(idx)
            anchor_para_index = shape.Range.Paragraphs(1).Range.Information(3)  # wdFirstCharacterLineNumber? fallback-ish
            # Better paragraph lookup from Range
            para_idx = shape.Range.Paragraphs(1).Range.Paragraphs(1).Index
            mappings.append(
                {
                    "shape_index": idx,
                    "paragraph_index": para_idx,
                    "prev_text": paragraph_text(paragraphs, para_idx - 1),
                    "caption_text": paragraph_text(paragraphs, para_idx),
                    "next_text": paragraph_text(paragraphs, para_idx + 1),
                }
            )

        exported_media = []
        media_dir = HTML_DIR / "thesis.files"
        if media_dir.exists():
            for item in sorted(media_dir.iterdir()):
                if item.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wmf", ".emf"}:
                    target = OUT_DIR / item.name
                    shutil.copy2(item, target)
                    exported_media.append(target.name)

        result = {
            "doc_path": str(DOC_PATH),
            "exported_images": exported_media,
            "inline_shapes": mappings,
        }
        META_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(META_PATH))
        print(f"exported_images={len(exported_media)}")
        print(f"inline_shapes={len(mappings)}")
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()


if __name__ == "__main__":
    main()
