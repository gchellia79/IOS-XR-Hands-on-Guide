#!/usr/bin/env python3
"""Extract a Word lab guide into Markdown plus numbered images.

Walks the document body in order and writes:
  _import/draft.md
  _import/images/imageNN.<ext>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentType
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

IMAGE_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/x-emf": ".emf",
    "image/x-wmf": ".wmf",
    "image/svg+xml": ".svg",
}

MONO_FONTS = {
    "consolas",
    "courier",
    "courier new",
    "menlo",
    "monaco",
    "source code pro",
    "cascadia code",
    "cascadia mono",
    "lucida console",
    "andale mono",
    "inconsolata",
    "fira code",
    "fira mono",
    "roboto mono",
    "jetbrains mono",
    "dejavu sans mono",
    "liberation mono",
    "nimbus mono",
    "pt mono",
    "ubuntu mono",
    "droid sans mono",
}

CREDENTIAL_KEYS = ("password", "passwd", "secret", "token")
CREDENTIAL_RE = re.compile(
    r"(?i)\b("
    + "|".join(CREDENTIAL_KEYS)
    + r")\b(?:\s+with)?(\s*[=:]\s*|\s+)(\S+)"
)
HEADING_NUMBERED_RE = re.compile(r"^(\d+\.\d+)\s*(.*)$")
EXERCISE_RE = re.compile(r"^Exercise\s+[\d.]+", re.I)
STEP_RE = re.compile(r"^Step\s*:?\s*\d+", re.I)
CLI_START_RE = re.compile(
    r"^(RP/|cisco@|!!|%\s|"
    r"interface\s|class-map\s|class\s|policy-map\s|"
    r"taskgroup\s|usergroup\s|username\s|router\s|"
    r"int\s+lo|ip\s+address\s|ipv4\s+address\s|"
    r"commit(?:\s|$)|show\s|configure\s|conf\s+t|process\s+restart|"
    r"match\s+|bandwidth\s+|task\s+|group\s+|secret\s+|"
    r"end$|!$|exit$|"
    r"JID\s|Job Id:|PID:|Process name:|"
    r"Current Configuration Session|"
    r"\*\s+vty|vty\d|"
    r"<Delete>|"
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s)"
)
CLI_CONT_RE = re.compile(
    r"^(\s+\S|WORD\s|<[\d\-]+>|<\d+|ipv4\s|exit$|commit$|end$|!$)"
)


def mask_credentials(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}<masked>"

    return CREDENTIAL_RE.sub(repl, text)


def looks_like_cli(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if CLI_START_RE.match(stripped) or CLI_CONT_RE.match(stripped):
        return True
    return False


def inferred_heading_level(paragraph: Paragraph, text: str) -> int | None:
    style = paragraph.style
    name = (style.name or "") if style is not None else ""
    match = re.match(r"^(Heading|Titre)\s+(\d+)$", name, re.I)
    if match:
        return int(match.group(2))
    style_id = ""
    try:
        style_id = paragraph.style.style_id or ""
    except Exception:
        pass
    match = re.match(r"^Heading(\d+)$", style_id, re.I)
    if match:
        return int(match.group(1))
    outline = paragraph._p.pPr
    if outline is not None and outline.outlineLvl is not None:
        val = outline.outlineLvl.val
        if val is not None:
            return int(val) + 1

    if not text:
        return None
    numbered = HEADING_NUMBERED_RE.match(text)
    if numbered and len(text) < 80:
        return 2
    if EXERCISE_RE.match(text) and len(text) < 40:
        return 3
    if STEP_RE.match(text) and len(text) < 20:
        return 4
    if text in {"Configs"}:
        return 4

    is_list, ilvl, _kind = is_list_paragraph(paragraph)
    if is_list and text and len(text) <= 60 and not text.endswith((".", "?", ";")):
        # Word used List Paragraph for chapter titles (numId=1).
        num_id = None
        pPr = paragraph._p.pPr
        if pPr is not None and pPr.numPr is not None and pPr.numPr.numId is not None:
            num_id = pPr.numPr.numId.val
        if num_id == 1:
            return 1 if ilvl == 0 else 2
        if num_id == 4:
            return 3
    return None


def heading_level(paragraph: Paragraph) -> int | None:
    return inferred_heading_level(paragraph, paragraph_plain_text(paragraph).strip())


def is_list_paragraph(paragraph: Paragraph) -> tuple[bool, int, str]:
    """Return (is_list, level, kind) where kind is 'ul' or 'ol'."""
    pPr = paragraph._p.pPr
    if pPr is None or pPr.numPr is None:
        style = paragraph.style
        name = (style.name or "") if style is not None else ""
        if name.lower().startswith("list bullet"):
            return True, 0, "ul"
        if name.lower().startswith("list number"):
            return True, 0, "ol"
        return False, 0, "ul"
    numPr = pPr.numPr
    ilvl = 0
    if numPr.ilvl is not None and numPr.ilvl.val is not None:
        ilvl = int(numPr.ilvl.val)
    kind = "ul"
    try:
        numbering = paragraph.part.numbering_part.element
        num_id = numPr.numId.val if numPr.numId is not None else None
        if num_id is not None:
            num = numbering.find(qn("w:num") + f'[@w:numId="{num_id}"]')
            if num is None:
                for candidate in numbering.findall(qn("w:num")):
                    if candidate.get(qn("w:numId")) == str(num_id):
                        num = candidate
                        break
            abstract_id = None
            if num is not None:
                abs_el = num.find(qn("w:abstractNumId"))
                if abs_el is not None:
                    abstract_id = abs_el.get(qn("w:val"))
            if abstract_id is not None:
                abstract = None
                for candidate in numbering.findall(qn("w:abstractNum")):
                    if candidate.get(qn("w:abstractNumId")) == str(abstract_id):
                        abstract = candidate
                        break
                if abstract is not None:
                    for lvl in abstract.findall(qn("w:lvl")):
                        if int(lvl.get(qn("w:ilvl") or "0")) == ilvl:
                            fmt = lvl.find(qn("w:numFmt"))
                            if fmt is not None:
                                fmt_val = (fmt.get(qn("w:val")) or "").lower()
                                if fmt_val in {"decimal", "lowerletter", "upperletter", "lowerroman", "upperroman", "ordinal"}:
                                    kind = "ol"
                            break
    except Exception:
        pass
    return True, ilvl, kind


def run_font_name(run) -> str:
    name = ""
    if run.font is not None and run.font.name:
        name = run.font.name
    rPr = run._r.rPr
    if rPr is not None:
        rFonts = rPr.rFonts
        if rFonts is not None:
            name = (
                rFonts.get(qn("w:ascii"))
                or rFonts.get(qn("w:hAnsi"))
                or rFonts.get(qn("w:cs"))
                or rFonts.get(qn("w:eastAsia"))
                or name
            )
    return name or ""


def is_mono_font(name: str) -> bool:
    lowered = name.strip().lower()
    if not lowered:
        return False
    if lowered in MONO_FONTS:
        return True
    return "mono" in lowered or "courier" in lowered or "console" in lowered


def paragraph_is_monospaced(paragraph: Paragraph) -> bool:
    style = paragraph.style
    name = (style.name or "") if style is not None else ""
    lowered = name.lower()
    if any(token in lowered for token in ("code", "preformatted", "html pre", "source", "console", "verbatim")):
        return True
    runs = [run for run in paragraph.runs if run.text and run.text.strip()]
    if not runs:
        return False
    fonts = [run_font_name(run) for run in runs]
    return bool(fonts) and all(is_mono_font(font) for font in fonts)


def paragraph_plain_text(paragraph: Paragraph) -> str:
    return mask_credentials(paragraph.text.replace("\u00a0", " "))


def markdown_escape_cell(text: str) -> str:
    return mask_credentials(text.replace("\n", " ").replace("|", "\\|")).strip()


class Extractor:
    def __init__(self, doc: DocumentType, out_dir: Path) -> None:
        self.doc = doc
        self.out_dir = out_dir
        self.image_dir = out_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.lines: list[str] = []
        self.image_count = 0
        self.table_count = 0
        self.headings: list[tuple[int, str]] = []
        self.seen_blips: set[str] = set()
        self._list_open: list[str] | None = None
        self._code_open = False

    def close_list(self) -> None:
        if self._list_open is not None:
            self.lines.append("")
            self._list_open = None
        self.close_code()

    def close_code(self) -> None:
        if self._code_open:
            self.lines.append("```")
            self.lines.append("")
            self._code_open = False

    def emit_code_line(self, text: str) -> None:
        if self._list_open is not None:
            self.lines.append("")
            self._list_open = None
        if not self._code_open:
            self.lines.append("```text")
            self._code_open = True
        self.lines.append(text)

    def emit(self, text: str = "") -> None:
        self.lines.append(text)

    def image_ext(self, part) -> str:
        ctype = getattr(part, "content_type", "") or ""
        if ctype in IMAGE_CONTENT_TYPES:
            return IMAGE_CONTENT_TYPES[ctype]
        filename = getattr(part, "filename", "") or ""
        suffix = Path(filename).suffix.lower()
        if suffix:
            return suffix
        return ".png"

    def save_image_part(self, r_id: str, container) -> str | None:
        if not r_id:
            return None
        try:
            part = container.part.related_parts[r_id]
        except KeyError:
            try:
                part = self.doc.part.related_parts[r_id]
            except KeyError:
                return None
        self.image_count += 1
        ext = self.image_ext(part)
        name = f"image{self.image_count:02d}{ext}"
        path = self.image_dir / name
        path.write_bytes(part.blob)
        return name

    def extract_images_from_element(self, element, container) -> list[str]:
        names: list[str] = []
        for blip in element.xpath(".//*[local-name()='blip']"):
            embed = blip.get(qn("r:embed")) or blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            link = blip.get(qn("r:link")) or blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link")
            r_id = embed or link
            if not r_id:
                continue
            key = f"{id(container)}:{r_id}:{blip.sourceline}"
            if key in self.seen_blips:
                continue
            self.seen_blips.add(key)
            saved = self.save_image_part(r_id, container)
            if saved:
                names.append(saved)
        for imagedata in element.xpath(".//*[local-name()='imagedata']"):
            r_id = imagedata.get(qn("r:id")) or imagedata.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            if not r_id:
                continue
            key = f"{id(container)}:vml:{r_id}:{imagedata.sourceline}"
            if key in self.seen_blips:
                continue
            self.seen_blips.add(key)
            saved = self.save_image_part(r_id, container)
            if saved:
                names.append(saved)
        return names

    def emit_images(self, names: list[str]) -> None:
        for name in names:
            stem = Path(name).stem
            self.emit(f"![{stem}](images/{name})")
            self.emit("")

    def textbox_elements(self, element) -> list:
        return element.xpath(".//*[local-name()='txbxContent']")

    def extract_textbox_text(self, txbx) -> str:
        texts: list[str] = []
        for node in txbx.iter():
            if node.tag == qn("w:t") and node.text:
                texts.append(node.text)
            if node.tail and node.tag == qn("w:t"):
                pass
            if node.tag == qn("w:br"):
                texts.append("\n")
            if node.tag == qn("w:p"):
                texts.append("\n")
        raw = "".join(texts)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return mask_credentials(raw.strip())

    def handle_textboxes(self, element, container) -> bool:
        boxes = self.textbox_elements(element)
        if not boxes:
            return False
        handled = False
        for box in boxes:
            images = self.extract_images_from_element(box, container)
            text = self.extract_textbox_text(box)
            self.close_list()
            if text:
                self.emit("```text")
                self.emit(text)
                self.emit("```")
                self.emit("")
                handled = True
            if images:
                self.emit_images(images)
                handled = True
        # Images in the parent that are not inside the text box
        parent_images = [
            name
            for name in self.extract_images_from_element(element, container)
            if True
        ]
        # extract_images_from_element skips already-seen blips
        if parent_images:
            self.close_list()
            self.emit_images(parent_images)
            handled = True
        return handled

    def handle_paragraph(self, paragraph: Paragraph) -> None:
        element = paragraph._p
        if self.textbox_elements(element):
            self.handle_textboxes(element, paragraph)
            return

        images = self.extract_images_from_element(element, paragraph)
        raw = paragraph_plain_text(paragraph).rstrip()
        text = raw.strip()
        level = inferred_heading_level(paragraph, text)

        if not text:
            if images:
                self.close_list()
                self.emit_images(images)
            elif self._code_open:
                # Preserve a blank line inside a CLI block.
                self.lines.append("")
            return

        if level:
            self.close_list()
            self.headings.append((level, text))
            self.emit(f"{'#' * min(level, 6)} {text}")
            self.emit("")
            if images:
                self.emit_images(images)
            return

        if paragraph_is_monospaced(paragraph) or looks_like_cli(text):
            self.emit_code_line(raw)
            if images:
                self.close_code()
                self.emit_images(images)
            return

        is_list, ilvl, kind = is_list_paragraph(paragraph)
        if is_list:
            self.close_code()
            marker = "-" if kind == "ul" else "1."
            indent = "    " * ilvl
            self.emit(f"{indent}{marker} {text}")
            self._list_open = kind
            if images:
                self.close_list()
                self.emit_images(images)
            return

        self.close_list()
        self.emit(text)
        self.emit("")
        if images:
            self.emit_images(images)

    def handle_table(self, table: Table) -> None:
        self.close_list()
        self.table_count += 1
        images_after: list[str] = []
        rows: list[list[str]] = []
        for row in table.rows:
            cells: list[str] = []
            for cell in row.cells:
                images_after.extend(self.extract_images_from_element(cell._tc, cell))
                for box in self.textbox_elements(cell._tc):
                    # text boxes inside table cells: include their text in the cell
                    extra = self.extract_textbox_text(box)
                    if extra and extra not in (cell.text or ""):
                        pass
                cell_text = markdown_escape_cell(cell.text or "")
                cells.append(cell_text)
            rows.append(cells)
        if not rows:
            return
        width = max(len(row) for row in rows)
        normalized = [row + [""] * (width - len(row)) for row in rows]
        header = normalized[0]
        self.emit("| " + " | ".join(header) + " |")
        self.emit("| " + " | ".join("---" for _ in header) + " |")
        for row in normalized[1:]:
            self.emit("| " + " | ".join(row) + " |")
        self.emit("")
        if images_after:
            self.emit_images(images_after)

    def iter_body(self):
        body = self.doc.element.body
        for child in body.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, self.doc)
            elif isinstance(child, CT_Tbl):
                yield Table(child, self.doc)
            else:
                # Drawings / alternate content sitting directly on the body
                if self.textbox_elements(child) or child.xpath(".//*[local-name()='blip']") or child.xpath(".//*[local-name()='imagedata']"):
                    yield ("raw", child)

    def run(self) -> None:
        for item in self.iter_body():
            if isinstance(item, tuple) and item[0] == "raw":
                self.close_list()
                self.handle_textboxes(item[1], self.doc)
                images = self.extract_images_from_element(item[1], self.doc)
                if images:
                    self.emit_images(images)
            elif isinstance(item, Paragraph):
                self.handle_paragraph(item)
            elif isinstance(item, Table):
                self.handle_table(item)
        self.close_list()
        # Trailing whitespace cleanup
        text = "\n".join(self.lines)
        text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
        (self.out_dir / "draft.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a .docx lab guide to Markdown.")
    parser.add_argument("docx", type=Path, help="Path to the Word document")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("_import"),
        help="Output directory (default: _import)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.docx.exists():
        print(f"error: {args.docx} not found", file=sys.stderr)
        return 1
    args.output.mkdir(parents=True, exist_ok=True)
    doc = Document(str(args.docx))
    extractor = Extractor(doc, args.output)
    extractor.run()
    print(f"Wrote {args.output / 'draft.md'}")
    print(f"Images: {extractor.image_count}")
    print(f"Tables: {extractor.table_count}")
    print("Headings:")
    if not extractor.headings:
        print("  (none)")
    for level, title in extractor.headings:
        print(f"{'  ' * (level - 1)}{'#' * level} {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
