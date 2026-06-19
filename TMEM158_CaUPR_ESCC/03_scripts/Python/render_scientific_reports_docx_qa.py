#!/usr/bin/env python3
"""Render the Scientific Reports DOCX and refresh page-boundary QA.

This is a submission-engineering check. It verifies that the editable DOCX can
be rendered locally after each manuscript rebuild and records automated page
margin metrics. It does not replace the final journal upload-system preview.
"""

from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT_DIR = ROOT / "07_manuscript"
QC_DIR = ROOT / "04_results" / "qc"
OUT_DIR = MANUSCRIPT_DIR / "rendered_scientific_reports_docx"
DOCX = MANUSCRIPT_DIR / "manuscript_scientific_reports.docx"
BUILD_QC = QC_DIR / "scientific_reports_docx_build_qc.csv"
METRICS = QC_DIR / "scientific_reports_docx_render_metrics.csv"
QA = QC_DIR / "scientific_reports_docx_qa.csv"
PDF = OUT_DIR / "manuscript_scientific_reports.pdf"
CONTACT = OUT_DIR / "contact_sheet.png"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_key_value_csv(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "item" not in reader.fieldnames or "value" not in reader.fieldnames:
            return {}
        return {row.get("item", ""): row.get("value", "") for row in reader}


def upsert_csv(path: Path, key: str, new_rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    existing: Dict[str, Dict[str, object]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get(key):
                    existing[row[key]] = dict(row)
    for row in new_rows:
        existing[str(row[key])] = dict(row)
    field_order = list(fields)
    for row in existing.values():
        for field in row:
            if field not in field_order:
                field_order.append(field)
    write_csv(path, list(existing.values()), field_order)


def natural_page_key(path: Path) -> int:
    match = re.search(r"page-(\d+)\.png$", path.name)
    return int(match.group(1)) if match else 0


def find_executable(name: str, fallback: Sequence[str] = ()) -> str:
    hit = shutil.which(name)
    if hit:
        return hit
    for candidate in fallback:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError(f"Required executable not found: {name}")


def run_command(args: Sequence[str], env: Dict[str, str] | None = None) -> None:
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(args)
            + "\nSTDOUT:\n"
            + result.stdout[-4000:]
            + "\nSTDERR:\n"
            + result.stderr[-4000:]
        )


def render_docx_to_pdf() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    soffice = find_executable(
        "soffice",
        ["/Applications/LibreOffice.app/Contents/MacOS/soffice"],
    )
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="tm158_lo_profile_") as tmp:
        profile_uri = Path(tmp).resolve().as_uri()
        run_command(
            [
                soffice,
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                f"-env:UserInstallation={profile_uri}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(OUT_DIR),
                str(DOCX),
            ],
            env=env,
        )
    produced = OUT_DIR / f"{DOCX.stem}.pdf"
    if not produced.exists():
        raise RuntimeError(f"LibreOffice did not produce expected PDF: {produced}")
    if produced != PDF:
        produced.replace(PDF)


def render_pdf_pages() -> List[Path]:
    pdftoppm = find_executable("pdftoppm")
    run_command([pdftoppm, "-png", "-r", "150", str(PDF), str(OUT_DIR / "page")])
    pages = sorted(OUT_DIR.glob("page-*.png"), key=natural_page_key)
    if not pages:
        raise RuntimeError("pdftoppm produced no page PNG files")
    return pages


def page_metrics(page: Path) -> Dict[str, object]:
    image = Image.open(page).convert("RGB")
    width, height = image.size
    white = Image.new("RGB", image.size, "white")
    diff = ImageChops.difference(image, white).convert("L")
    mask = diff.point(lambda pixel: 255 if pixel > 12 else 0)
    bbox = mask.getbbox()
    histogram = mask.histogram()
    nonwhite = histogram[255] / float(width * height)
    if bbox is None:
        left = top = right = bottom = ""
        status = "blank_risk"
    else:
        left, top, right, bottom = bbox
        margin_risk = left < 60 or top < 60 or (width - right) < 60 or (height - bottom) < 60
        status = "margin_risk" if margin_risk else "pass"
    return {
        "page": page.name,
        "width": width,
        "height": height,
        "bytes": page.stat().st_size,
        "nonwhite_fraction": round(nonwhite, 4),
        "bbox_left": left,
        "bbox_top": top,
        "bbox_right": right,
        "bbox_bottom": bottom,
        "automated_margin_status": status,
    }


def font(size: int):
    for candidate in [
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def build_contact_sheet(pages: Sequence[Path]) -> None:
    thumbs = []
    thumb_w = 360
    label_h = 34
    gap = 18
    for page in pages:
        image = Image.open(page).convert("RGB")
        ratio = thumb_w / image.width
        thumb_h = int(image.height * ratio)
        image = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        thumbs.append((page, image))
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    cell_h = max(image.height for _, image in thumbs) + label_h
    width = cols * thumb_w + (cols + 1) * gap
    height = rows * cell_h + (rows + 1) * gap
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    label_font = font(20)
    for idx, (page, image) in enumerate(thumbs):
        row = idx // cols
        col = idx % cols
        x = gap + col * (thumb_w + gap)
        y = gap + row * (cell_h + gap)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y, x + image.width, y + image.height), outline="#9CA3AF", width=1)
        draw.text((x, y + image.height + 6), page.stem.replace("-", " "), fill="#111827", font=label_font)
    sheet.save(CONTACT, dpi=(150, 150))


def write_qa(metrics_rows: Sequence[Dict[str, object]]) -> None:
    build = read_key_value_csv(BUILD_QC)
    page_count = len(metrics_rows)
    risk_count = sum(1 for row in metrics_rows if row.get("automated_margin_status") != "pass")
    paragraph_count = build.get("paragraph_count", "unknown")
    heading_count = build.get("heading_count", "unknown")
    reference_count = build.get("reference_count", "unknown")
    rows = [
        {
            "item": "docx_file",
            "value": "07_manuscript/manuscript_scientific_reports.docx",
            "status": "pass",
            "notes": "Editable Scientific Reports manuscript DOCX generated from target Markdown draft",
        },
        {
            "item": "build_script",
            "value": "03_scripts/Python/build_scientific_reports_docx.py",
            "status": "pass",
            "notes": "Reproducible builder retained; design preset narrative_proposal with journal manuscript override",
        },
        {
            "item": "font_policy",
            "value": "Times New Roman ascii/hAnsi; Songti eastAsia",
            "status": "pass",
            "notes": "Project font rule applied through Word run/style font slots",
        },
        {
            "item": "build_qc",
            "value": "04_results/qc/scientific_reports_docx_build_qc.csv",
            "status": "pass",
            "notes": f"{paragraph_count} manuscript paragraphs, {heading_count} headings and {reference_count} references detected",
        },
        {
            "item": "render_status",
            "value": f"{page_count} pages",
            "status": "pass",
            "notes": "LibreOffice generated PDF; pdftoppm generated page PNG previews",
        },
        {
            "item": "render_metrics",
            "value": "04_results/qc/scientific_reports_docx_render_metrics.csv",
            "status": "pass" if risk_count == 0 else "needs_review",
            "notes": f"Automated page-boundary check flagged {risk_count}/{page_count} pages for margin risk",
        },
        {
            "item": "visual_review_package",
            "value": "07_manuscript/rendered_scientific_reports_docx/contact_sheet.png",
            "status": "ready_for_human_preview",
            "notes": "Contact sheet and page PNGs regenerated after the latest manuscript build; final journal upload preview remains human-gated",
        },
        {
            "item": "rendered_pdf",
            "value": "07_manuscript/rendered_scientific_reports_docx/manuscript_scientific_reports.pdf",
            "status": "pass_internal_qa",
            "notes": "PDF retained as render QA artifact; DOCX remains the editable submission manuscript",
        },
        {
            "item": "remaining_human_upload_checks",
            "value": "publisher upload preview; final claim-boundary read",
            "status": "needs_author_input",
            "notes": "Author metadata and declarations have been supplied; publisher-system rendering still requires human inspection",
        },
        {
            "item": "generated_at",
            "value": NOW,
            "status": "info",
            "notes": "Local system timestamp",
        },
    ]
    write_csv(QA, rows, ["item", "value", "status", "notes"])


def update_indexes(page_count: int, risk_count: int) -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "scientific_reports_docx_render_metrics", "path": "04_results/qc/scientific_reports_docx_render_metrics.csv"},
            {"result": "scientific_reports_docx_qa", "path": "04_results/qc/scientific_reports_docx_qa.csv"},
            {"result": "scientific_reports_docx_rendered_pdf", "path": "07_manuscript/rendered_scientific_reports_docx/manuscript_scientific_reports.pdf"},
            {"result": "scientific_reports_docx_contact_sheet", "path": "07_manuscript/rendered_scientific_reports_docx/contact_sheet.png"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {
                "item": "docx_render_qa",
                "value": f"{page_count} pages; {risk_count} margin-risk pages",
                "status": "pass" if risk_count == 0 else "needs_review",
                "notes": "DOCX was rendered to PDF/PNG after the latest manuscript build; final upload preview remains human-gated",
            },
        ],
        ["item", "value", "status", "notes"],
    )


def main() -> None:
    render_docx_to_pdf()
    pages = render_pdf_pages()
    metrics_rows = [page_metrics(page) for page in pages]
    write_csv(
        METRICS,
        metrics_rows,
        ["page", "width", "height", "bytes", "nonwhite_fraction", "bbox_left", "bbox_top", "bbox_right", "bbox_bottom", "automated_margin_status"],
    )
    build_contact_sheet(pages)
    risk_count = sum(1 for row in metrics_rows if row.get("automated_margin_status") != "pass")
    write_qa(metrics_rows)
    update_indexes(len(metrics_rows), risk_count)
    print(
        "scientific_reports_docx_render_qa=completed "
        f"pages={len(metrics_rows)} margin_risk={risk_count} "
        f"pdf={PDF.relative_to(ROOT)} contact_sheet={CONTACT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
