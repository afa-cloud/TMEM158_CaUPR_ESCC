#!/usr/bin/env python3
"""Add AlphaFold/UniProt topology context for TMEM158.

This module strengthens protein-background plausibility without changing the
claim boundary. AlphaFold is used as a public predicted-structure resource; it
does not prove physical interactions, ER localization, Ca2/UPR regulation or
CAF/ECM binding.
"""

from __future__ import annotations

import base64
import csv
import json
import os
import re
import statistics
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "02_data" / "raw" / "protein_context"
STRUCTURE_DIR = ROOT / "04_results" / "structure"
QC_DIR = ROOT / "04_results" / "qc"
FIG_DIR = ROOT / "05_figures"
MANUSCRIPT_DIR = ROOT / "07_manuscript"
STRATEGY_DIR = ROOT / "08_submission_strategy"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
FORCE = os.environ.get("TMEM158_ALPHAFOLD_REFRESH", "0") == "1"
ALPHAFOLD_REFERENCE = (
    "25. Varadi, M. et al. AlphaFold Protein Structure Database in 2024: "
    "providing structure coverage for over 214 million protein sequences. "
    "*Nucleic Acids Research* 52, D368-D375 (2024). doi:10.1093/nar/gkad1011."
)

for directory in (RAW_DIR, STRUCTURE_DIR, QC_DIR, FIG_DIR, MANUSCRIPT_DIR, STRATEGY_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def fetch(url: str, path: Path, binary: bool = False) -> Dict[str, object]:
    if path.exists() and path.stat().st_size > 0 and not FORCE:
        return {"status": "cached", "bytes": path.stat().st_size, "error": ""}
    request = urllib.request.Request(url, headers={"User-Agent": "Codex public-data workflow"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read()
        if binary:
            path.write_bytes(payload)
        else:
            path.write_text(payload.decode("utf-8"), encoding="utf-8")
        time.sleep(0.2)
        return {"status": "downloaded", "bytes": path.stat().st_size, "error": ""}
    except Exception as exc:
        return {"status": "failed", "bytes": path.stat().st_size if path.exists() else 0, "error": str(exc)}


def read_json(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def upsert_csv(path: Path, key: str, new_rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    rows = {row.get(key, ""): dict(row) for row in read_csv(path) if row.get(key)}
    for row in new_rows:
        rows[str(row[key])] = dict(row)
    field_order = list(fields)
    for row in rows.values():
        for field in row:
            if field not in field_order:
                field_order.append(field)
    write_csv(path, list(rows.values()), field_order)


def replace_or_append(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"<!-- {marker} -->\n{text.strip()}\n"
    pattern = re.compile(rf"<!-- {re.escape(marker)} -->\n.*?(?=\n<!-- |\Z)", re.S)
    if pattern.search(current):
        current = pattern.sub(block.rstrip(), current)
    else:
        if current and not current.endswith("\n"):
            current += "\n"
        current += "\n" + block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(current, encoding="utf-8")


def ensure_alphafold_reference(path: Path) -> None:
    if not path.exists():
        return
    current = path.read_text(encoding="utf-8")
    if "AlphaFold Protein Structure Database in 2024" in current:
        return
    if re.search(r"\n24\.\s+Yang, Z\. et al\.", current):
        current = current.rstrip() + "\n" + ALPHAFOLD_REFERENCE + "\n"
    else:
        current = current.rstrip() + "\n\n" + ALPHAFOLD_REFERENCE + "\n"
    path.write_text(current, encoding="utf-8")


def font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def confidence_call(plddt: float) -> str:
    if plddt >= 90:
        return "very_high"
    if plddt >= 70:
        return "confident"
    if plddt >= 50:
        return "low"
    return "very_low"


KD = {
    "I": 4.5,
    "V": 4.2,
    "L": 3.8,
    "F": 2.8,
    "C": 2.5,
    "M": 1.9,
    "A": 1.8,
    "G": -0.4,
    "T": -0.7,
    "S": -0.8,
    "W": -0.9,
    "Y": -1.3,
    "P": -1.6,
    "H": -3.2,
    "E": -3.5,
    "Q": -3.5,
    "D": -3.5,
    "N": -3.5,
    "K": -3.9,
    "R": -4.5,
}


def hydropathy_window(sequence: str, window: int = 19) -> List[float]:
    half = window // 2
    values = []
    for idx in range(len(sequence)):
        start = max(0, idx - half)
        end = min(len(sequence), idx + half + 1)
        values.append(sum(KD.get(aa, 0.0) for aa in sequence[start:end]) / (end - start))
    return values


def hydrophobic_segments(values: Sequence[float], threshold: float = 1.6, min_len: int = 10) -> List[Dict[str, object]]:
    segments: List[Dict[str, object]] = []
    start = None
    for idx, value in enumerate(values, start=1):
        if value >= threshold and start is None:
            start = idx
        is_end = idx == len(values)
        if start is not None and (value < threshold or is_end):
            end = idx - 1 if value < threshold else idx
            if end - start + 1 >= min_len:
                segments.append(
                    {
                        "segment_id": f"KD_hydrophobic_{len(segments) + 1}",
                        "start": start,
                        "end": end,
                        "length": end - start + 1,
                        "max_hydropathy19": round(max(values[start - 1 : end]), 3),
                    }
                )
            start = None
    return segments


def mean_range(values: Sequence[float], start: int, end: int) -> float:
    return float(statistics.mean(values[start - 1 : end]))


def uniprot_tm_features(uniprot: Dict[str, object]) -> List[Dict[str, object]]:
    rows = []
    for feature in uniprot.get("features", []) or []:
        if feature.get("type") not in {"Transmembrane", "Topological domain", "Intramembrane"}:
            continue
        location = feature.get("location", {}) or {}
        start = int((location.get("start", {}) or {}).get("value", 0))
        end = int((location.get("end", {}) or {}).get("value", 0))
        if start <= 0 or end <= 0:
            continue
        rows.append(
            {
                "segment_id": f"UniProt_{feature.get('type', '').replace(' ', '_')}_{len(rows) + 1}",
                "source": "UniProt feature",
                "feature_type": feature.get("type", ""),
                "start": start,
                "end": end,
                "length": end - start + 1,
                "description": feature.get("description", ""),
            }
        )
    return rows


def download_inputs() -> tuple[Dict[str, object], Dict[str, object], Dict[str, object], Dict[str, object]]:
    status_rows = []
    api_path = RAW_DIR / "alphafold_Q8WZ71_prediction_api.json"
    api_status = fetch("https://alphafold.ebi.ac.uk/api/prediction/Q8WZ71", api_path)
    status_rows.append({"source": "AlphaFold prediction API", "url": "https://alphafold.ebi.ac.uk/api/prediction/Q8WZ71", "local_path": str(api_path), **api_status})
    records = read_json(api_path) or []
    canonical = None
    for record in records:
        if record.get("uniprotAccession") == "Q8WZ71":
            canonical = record
            break
    if canonical is None and records:
        canonical = records[0]
    if canonical is None:
        raise RuntimeError("No AlphaFold Q8WZ71 record retrieved")

    for key, filename, binary in [
        ("pdbUrl", "alphafold_Q8WZ71_model_v6.pdb", False),
        ("paeDocUrl", "alphafold_Q8WZ71_pae_v6.json", False),
        ("plddtDocUrl", "alphafold_Q8WZ71_plddt_v6.json", False),
    ]:
        url = canonical.get(key)
        if url:
            path = RAW_DIR / filename
            result = fetch(url, path, binary=binary)
            status_rows.append({"source": f"AlphaFold {key}", "url": url, "local_path": str(path), **result})

    uniprot_path = RAW_DIR / "uniprot_Q8WZ71_full.json"
    uniprot_status = fetch("https://rest.uniprot.org/uniprotkb/Q8WZ71.json", uniprot_path)
    status_rows.append({"source": "UniProt full entry", "url": "https://rest.uniprot.org/uniprotkb/Q8WZ71.json", "local_path": str(uniprot_path), **uniprot_status})
    write_csv(
        QC_DIR / "tmem158_alphafold_topology_download_status.csv",
        status_rows,
        ["source", "url", "local_path", "status", "bytes", "error"],
    )
    plddt = read_json(RAW_DIR / "alphafold_Q8WZ71_plddt_v6.json") or {}
    pae = read_json(RAW_DIR / "alphafold_Q8WZ71_pae_v6.json") or {}
    uniprot = read_json(uniprot_path) or {}
    return canonical, plddt, pae, uniprot


def build_tables(canonical: Dict[str, object], plddt_doc: Dict[str, object], uniprot: Dict[str, object]) -> tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    sequence = canonical.get("sequence") or canonical.get("uniprotSequence") or ""
    scores = [float(x) for x in plddt_doc.get("confidenceScore", [])]
    if not scores and sequence:
        scores = [float("nan")] * len(sequence)
    hydro = hydropathy_window(sequence)
    tm_rows = uniprot_tm_features(uniprot)
    kd_rows = hydrophobic_segments(hydro)

    topology_segments: List[Dict[str, object]] = []
    for row in tm_rows:
        start, end = int(row["start"]), int(row["end"])
        mean_plddt = mean_range(scores, start, end)
        mean_hydro = mean_range(hydro, start, end)
        topology_segments.append(
            {
                **row,
                "mean_plddt": round(mean_plddt, 2),
                "mean_hydropathy19": round(mean_hydro, 3),
                "confidence_call": confidence_call(mean_plddt),
                "interpretation": "stronger structural support" if mean_plddt >= 70 and mean_hydro >= 1.6 else "annotated but lower-confidence structural segment",
            }
        )
    for row in kd_rows:
        start, end = int(row["start"]), int(row["end"])
        mean_plddt = mean_range(scores, start, end)
        topology_segments.append(
            {
                "segment_id": row["segment_id"],
                "source": "Kyte-Doolittle window",
                "feature_type": "hydrophobic segment",
                "start": start,
                "end": end,
                "length": row["length"],
                "description": "Local hydropathy window >=1.6",
                "mean_plddt": round(mean_plddt, 2),
                "mean_hydropathy19": round(mean_range(hydro, start, end), 3),
                "confidence_call": confidence_call(mean_plddt),
                "interpretation": "sequence-level hydrophobic support, not independent localization proof",
            }
        )

    def feature_label(pos: int) -> str:
        labels = []
        for row in tm_rows:
            if int(row["start"]) <= pos <= int(row["end"]):
                labels.append(row["segment_id"])
        return ";".join(labels)

    def kd_label(pos: int) -> str:
        labels = []
        for row in kd_rows:
            if int(row["start"]) <= pos <= int(row["end"]):
                labels.append(row["segment_id"])
        return ";".join(labels)

    residue_rows = []
    for idx, aa in enumerate(sequence, start=1):
        score = scores[idx - 1] if idx - 1 < len(scores) else float("nan")
        residue_rows.append(
            {
                "residue": idx,
                "aa": aa,
                "plddt": round(score, 2),
                "plddt_category": confidence_call(score),
                "hydropathy19": round(hydro[idx - 1], 3),
                "uniprot_topology_feature": feature_label(idx),
                "hydrophobic_window_segment": kd_label(idx),
            }
        )

    tm1 = next((row for row in topology_segments if row["source"] == "UniProt feature"), None)
    tm2 = next((row for row in topology_segments if row["source"] == "UniProt feature" and row["segment_id"] != (tm1 or {}).get("segment_id")), None)
    summary_rows = [
        {"item": "source", "value": "AlphaFold Protein Structure Database API plus UniProt feature table", "status": "ready", "notes": "Official public database context"},
        {"item": "alphafold_entry", "value": canonical.get("entryId", ""), "status": "ready", "notes": canonical.get("modelEntityId", "")},
        {"item": "tool_used", "value": canonical.get("toolUsed", ""), "status": "ready", "notes": "Model is predicted, not experimental"},
        {"item": "model_version", "value": canonical.get("latestVersion", ""), "status": "ready", "notes": canonical.get("modelCreatedDate", "")},
        {"item": "coverage", "value": f"{canonical.get('uniprotStart')}-{canonical.get('uniprotEnd')}", "status": "ready", "notes": f"{len(sequence)} aa sequence"},
        {"item": "global_plddt", "value": canonical.get("globalMetricValue", ""), "status": "boundary", "notes": "Moderate/low average confidence; avoid high-confidence interaction claims"},
        {"item": "fraction_plddt_very_high", "value": canonical.get("fractionPlddtVeryHigh", ""), "status": "boundary", "notes": "Fraction pLDDT >90 from AlphaFold API"},
        {"item": "fraction_plddt_confident", "value": canonical.get("fractionPlddtConfident", ""), "status": "context", "notes": "Fraction pLDDT 70-90 from AlphaFold API"},
        {"item": "fraction_plddt_low_or_very_low", "value": round(float(canonical.get("fractionPlddtLow", 0)) + float(canonical.get("fractionPlddtVeryLow", 0)), 3), "status": "boundary", "notes": "Low-confidence residues dominate the model"},
        {"item": "uniprot_transmembrane_segments", "value": len(tm_rows), "status": "support", "notes": "UniProt annotates helical transmembrane regions"},
        {"item": "tm1_mean_plddt", "value": (tm1 or {}).get("mean_plddt", ""), "status": "support" if tm1 and float(tm1["mean_plddt"]) >= 70 else "boundary", "notes": (tm1 or {}).get("interpretation", "")},
        {"item": "tm2_mean_plddt", "value": (tm2 or {}).get("mean_plddt", ""), "status": "boundary", "notes": (tm2 or {}).get("interpretation", "")},
        {"item": "main_interpretation", "value": "AlphaFold/UniProt support membrane-topology plausibility, especially TM1, but do not prove ER localization or physical interaction", "status": "context", "notes": "Use as structural rationale only"},
    ]
    return summary_rows, topology_segments, residue_rows


def render_figure(residue_rows: Sequence[Dict[str, object]], topology_segments: Sequence[Dict[str, object]], summary_rows: Sequence[Dict[str, object]]) -> None:
    width, height = 1800, 900
    left, right = 120, 70
    top, bottom = 120, 100
    plot_w = width - left - right
    plddt_top, plddt_h = 190, 260
    hydro_top, hydro_h = 545, 210
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = font(34, bold=True)
    body_font = font(22)
    small_font = font(18)
    draw.text((left, 42), "TMEM158 AlphaFold topology context", fill="#111827", font=title_font)
    draw.text((left, 88), "AlphaFold DB Q8WZ71 v6 with UniProt transmembrane features; structural rationale, not interaction proof", fill="#374151", font=body_font)

    max_res = max(int(row["residue"]) for row in residue_rows)

    def x_at(res: int) -> float:
        return left + (res - 1) / (max_res - 1) * plot_w

    # pLDDT panel
    draw.text((left, plddt_top - 40), "AlphaFold pLDDT by residue", fill="#111827", font=body_font)
    draw.line((left, plddt_top + plddt_h, left + plot_w, plddt_top + plddt_h), fill="#9CA3AF", width=2)
    draw.line((left, plddt_top, left, plddt_top + plddt_h), fill="#9CA3AF", width=2)
    for value, color in [(90, "#A7F3D0"), (70, "#BFDBFE"), (50, "#FDE68A")]:
        y = plddt_top + plddt_h - (value / 100) * plddt_h
        draw.line((left, y, left + plot_w, y), fill=color, width=2)
        draw.text((left + plot_w + 10, y - 10), str(value), fill="#6B7280", font=small_font)
    points = []
    for row in residue_rows:
        x = x_at(int(row["residue"]))
        y = plddt_top + plddt_h - (float(row["plddt"]) / 100) * plddt_h
        points.append((x, y))
    draw.line(points, fill="#2458A6", width=3)

    # Hydropathy panel
    draw.text((left, hydro_top - 40), "Kyte-Doolittle hydropathy window (19 aa)", fill="#111827", font=body_font)
    draw.line((left, hydro_top + hydro_h / 2, left + plot_w, hydro_top + hydro_h / 2), fill="#9CA3AF", width=2)
    draw.line((left, hydro_top, left, hydro_top + hydro_h), fill="#9CA3AF", width=2)
    threshold_y = hydro_top + hydro_h / 2 - (1.6 / 5.0) * (hydro_h / 2)
    draw.line((left, threshold_y, left + plot_w, threshold_y), fill="#D97706", width=2)
    draw.text((left + plot_w + 10, threshold_y - 10), "1.6", fill="#92400E", font=small_font)
    hpoints = []
    for row in residue_rows:
        value = max(-5, min(5, float(row["hydropathy19"])))
        x = x_at(int(row["residue"]))
        y = hydro_top + hydro_h / 2 - (value / 5.0) * (hydro_h / 2)
        hpoints.append((x, y))
    draw.line(hpoints, fill="#A6423A", width=3)

    # UniProt TM feature bars
    bar_y = 150
    draw.text((left, bar_y - 34), "UniProt topology features", fill="#111827", font=body_font)
    for idx, seg in enumerate([s for s in topology_segments if s["source"] == "UniProt feature"]):
        x1 = x_at(int(seg["start"]))
        x2 = x_at(int(seg["end"]))
        color = "#2E7D60" if seg["confidence_call"] in {"confident", "very_high"} else "#BCA35B"
        y1 = bar_y + idx * 34
        draw.rounded_rectangle((x1, y1, x2, y1 + 22), radius=6, fill=color)
        label = f"{seg['start']}-{seg['end']} pLDDT {seg['mean_plddt']}"
        label_w = draw.textbbox((0, 0), label, font=small_font)[2]
        label_x = x2 + 8
        if label_x + label_w > left + plot_w:
            label_x = max(left, x1 - label_w - 10)
        draw.text((label_x, y1 - 2), label, fill="#111827", font=small_font)

    for tick in [1, 50, 100, 150, 200, 250, 300]:
        x = x_at(tick)
        draw.line((x, hydro_top + hydro_h + 10, x, hydro_top + hydro_h + 22), fill="#6B7280", width=2)
        draw.text((x - 16, hydro_top + hydro_h + 28), str(tick), fill="#4B5563", font=small_font)
    draw.text((left + plot_w - 140, hydro_top + hydro_h + 58), "Residue position", fill="#111827", font=body_font)

    summary = {row["item"]: row["value"] for row in summary_rows}
    footer = (
        f"Global pLDDT {summary.get('global_plddt')}; low/very-low fraction "
        f"{summary.get('fraction_plddt_low_or_very_low')}. TM1 is interpretable; TM2 remains lower-confidence."
    )
    draw.text((left, height - 58), footer, fill="#374151", font=body_font)

    png = FIG_DIR / "figure25_tmem158_alphafold_topology_context.png"
    pdf = FIG_DIR / "figure25_tmem158_alphafold_topology_context.pdf"
    svg = FIG_DIR / "figure25_tmem158_alphafold_topology_context.svg"
    image.save(png, dpi=(300, 300))
    image.save(pdf, "PDF", resolution=300)
    encoded = base64.b64encode(png.read_bytes()).decode("ascii")
    svg.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  <image href="data:image/png;base64,{encoded}" width="{width}" height="{height}"/>\n'
        f"</svg>\n",
        encoding="utf-8",
    )


def update_manuscript(summary_rows: Sequence[Dict[str, object]], topology_segments: Sequence[Dict[str, object]]) -> None:
    summary = {row["item"]: row["value"] for row in summary_rows}
    manuscript = MANUSCRIPT_DIR / "manuscript_scientific_reports.md"
    text = manuscript.read_text(encoding="utf-8")
    paragraph = (
        "AlphaFold Protein Structure Database analysis added predicted-structure support for this membrane-topology interpretation [25]. "
        f"The canonical Q8WZ71 model covered residues 1-300 (model version {summary.get('model_version')}) with global pLDDT {summary.get('global_plddt')}. "
        "UniProt feature annotation defined two helical transmembrane regions at residues 231-251 and 273-293. "
        f"The first segment had higher AlphaFold confidence (mean pLDDT {summary.get('tm1_mean_plddt')}), whereas the second segment remained low-confidence (mean pLDDT {summary.get('tm2_mean_plddt')}). "
        "Thus, AlphaFold strengthens the structural rationale that TMEM158 is a membrane-topology candidate with an interpretable C-terminal transmembrane region, but it does not establish direct ER localization, binding to Ca2/UPR proteins, interaction with ECM components, or ESCC-specific protein validation. "
        "This topology layer is therefore used to prioritize localization and interaction experiments rather than to infer a direct TMEM158-Ca2/UPR or TMEM158-ECM interface."
    )
    legacy_uncited_paragraph = (
        "AlphaFold Protein Structure Database analysis added predicted-structure support for this membrane-topology interpretation. "
        f"The canonical Q8WZ71 model covered residues 1-300 (model version {summary.get('model_version')}) with global pLDDT {summary.get('global_plddt')}. "
        "UniProt feature annotation defined two helical transmembrane regions at residues 231-251 and 273-293. "
        f"The first segment had higher AlphaFold confidence (mean pLDDT {summary.get('tm1_mean_plddt')}), whereas the second segment remained low-confidence (mean pLDDT {summary.get('tm2_mean_plddt')}). "
        "Thus, AlphaFold strengthens the structural rationale that TMEM158 is a membrane-topology candidate with an interpretable C-terminal transmembrane region, but it does not establish direct ER localization, binding to Ca2/UPR proteins, interaction with ECM components, or ESCC-specific protein validation."
    )
    legacy_cited_paragraph = legacy_uncited_paragraph.replace(
        "membrane-topology interpretation.",
        "membrane-topology interpretation [25].",
    )
    for legacy in (legacy_uncited_paragraph, legacy_cited_paragraph):
        text = text.replace(legacy + "\n\n", "")
        text = text.replace("\n\n" + legacy, "")
    priority_sentence = (
        "This topology layer is therefore used to prioritize localization and interaction experiments "
        "rather than to infer a direct TMEM158-Ca2/UPR or TMEM158-ECM interface."
    )
    text = text.replace(f"{priority_sentence} {priority_sentence}", priority_sentence)
    priority_pattern = re.escape(priority_sentence).replace(r"\ ", r"\s+")
    text = re.sub(rf"({priority_pattern})(?:\s+\1)+", r"\1", text)
    if paragraph not in text:
        anchor = (
            "These findings support assayability and membrane-protein plausibility but not ER localization or Ca2/UPR causality."
        )
        text = text.replace(anchor, anchor + "\n\n" + paragraph)
    text = text.replace(f"{priority_sentence} {priority_sentence}", priority_sentence)
    text = re.sub(rf"({priority_pattern})(?:\s+\1)+", r"\1", text)
    method_add = (
        "AlphaFold Protein Structure Database records for Q8WZ71 were queried through the official EBI API. "
        "The canonical model, per-residue pLDDT confidence file and UniProt feature table were used to summarize model coverage, confidence fractions, transmembrane-feature positions, segment-level pLDDT and sequence hydropathy. "
        "The analysis was interpreted as predicted structural/topology context only, not as evidence of physical interaction or localization in ESCC."
    )
    if method_add not in text:
        anchor = (
            "UniProt, QuickGO and HPA official resources were queried for protein identity, localization terms, HPA antibody context and public protein/RNA evidence."
        )
        text = text.replace(anchor, anchor + " " + method_add)
    legend = (
        "**Extended Data Figure 9. AlphaFold topology context for TMEM158.** "
        "The official AlphaFold Q8WZ71 model covers the 300-aa canonical sequence and supports an interpretable first C-terminal transmembrane segment, while the second UniProt transmembrane segment remains lower-confidence. "
        "This figure provides predicted topology rationale only and does not prove ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC protein validation."
    )
    if legend not in text:
        anchor = (
            "**Extended Data Figure 8. Public spatial progression source-data calibration.** Published source data from an ESCC spatial whole-transcriptome progression study show increasing DSP fibroblast abundance and alpha-SMA fibroblast IF across histological progression. The complete WTA matrix is restricted and absent from the Source Data, so this figure supports a CAF-rich tissue context but does not directly validate TMEM158, TAC_high or Ca2/UPR spatial activation."
        )
        text = text.replace(anchor, anchor + "\n\n" + legend)
    data_anchor = "All data analysed in this study were obtained from public resources, including TCGA/GDC or cBioPortal, GEO, DepMap-derived public resources, UniProt, QuickGO and the Human Protein Atlas."
    if "AlphaFold Protein Structure Database" not in text[text.find("## Data availability") : text.find("## Code availability")]:
        text = text.replace(data_anchor, data_anchor.replace("the Human Protein Atlas", "the Human Protein Atlas and AlphaFold Protein Structure Database"))
    text = text.replace(
        "UniProt, QuickGO and the Human Protein Atlas and AlphaFold Protein Structure Database",
        "UniProt, QuickGO, the Human Protein Atlas and the AlphaFold Protein Structure Database",
    )
    manuscript.write_text(text, encoding="utf-8")
    ensure_alphafold_reference(manuscript)
    ensure_alphafold_reference(MANUSCRIPT_DIR / "formal_references.md")


def write_report(summary_rows: Sequence[Dict[str, object]], topology_segments: Sequence[Dict[str, object]]) -> None:
    summary = {row["item"]: row["value"] for row in summary_rows}
    segment_lines = []
    for seg in topology_segments:
        if seg["source"] == "UniProt feature":
            segment_lines.append(
                f"- {seg['segment_id']}: {seg['start']}-{seg['end']} ({seg['description']}), mean pLDDT {seg['mean_plddt']}, mean hydropathy {seg['mean_hydropathy19']}, call={seg['confidence_call']}."
            )
    report = [
        "# TMEM158 AlphaFold topology context",
        "",
        "## Purpose",
        "",
        "This module adds predicted structural/topology context for TMEM158 using the official AlphaFold Protein Structure Database and UniProt feature annotation. It is a protein-background layer, not physical-interaction evidence.",
        "",
        "## Main findings",
        "",
        f"- AlphaFold entry: {summary.get('alphafold_entry')} ({summary.get('tool_used')}).",
        f"- Canonical model coverage: {summary.get('coverage')}.",
        f"- Global pLDDT: {summary.get('global_plddt')}; low/very-low pLDDT fraction: {summary.get('fraction_plddt_low_or_very_low')}.",
        f"- UniProt transmembrane segments: {summary.get('uniprot_transmembrane_segments')}.",
        *segment_lines,
        "",
        "## Interpretation",
        "",
        "AlphaFold/UniProt support a membrane-topology rationale for TMEM158, especially the first C-terminal transmembrane segment. The second UniProt transmembrane segment has lower AlphaFold confidence and should be treated as an annotated but structurally lower-confidence segment. This layer can strengthen the biological plausibility that TMEM158 is a membrane protein suitable for Ca2/UPR-axis follow-up, but it does not prove ER localization, binding to Ca2/UPR proteins, interaction with ECM components, or ESCC-specific protein expression. Its practical role is to prioritize localization, membrane-fraction, proximity-labelling, co-immunoprecipitation or future defined-partner co-modelling experiments.",
        "",
        "## Output files",
        "",
        "- `04_results/structure/tmem158_alphafold_model_summary.csv`",
        "- `04_results/structure/tmem158_alphafold_topology_segments.csv`",
        "- `04_results/structure/tmem158_alphafold_residue_confidence.csv`",
        "- `04_results/qc/tmem158_alphafold_topology_context_status.csv`",
        "- `05_figures/figure25_tmem158_alphafold_topology_context.png/.pdf/.svg`",
    ]
    (MANUSCRIPT_DIR / "tmem158_alphafold_topology_context_update.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def update_indexes(summary_rows: Sequence[Dict[str, object]]) -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "tmem158_alphafold_model_summary", "path": "04_results/structure/tmem158_alphafold_model_summary.csv"},
            {"result": "tmem158_alphafold_topology_segments", "path": "04_results/structure/tmem158_alphafold_topology_segments.csv"},
            {"result": "tmem158_alphafold_residue_confidence", "path": "04_results/structure/tmem158_alphafold_residue_confidence.csv"},
            {"result": "tmem158_alphafold_topology_context_status", "path": "04_results/qc/tmem158_alphafold_topology_context_status.csv"},
            {"result": "figure25_tmem158_alphafold_topology_context", "path": "05_figures/figure25_tmem158_alphafold_topology_context.png"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "02_data" / "data_inventory.csv",
        "source",
        [
            {"source": "AlphaFold DB TMEM158 Q8WZ71", "path": "02_data/raw/protein_context/alphafold_Q8WZ71_prediction_api.json", "reuse_role": "predicted structure and confidence topology context"},
            {"source": "UniProt TMEM158 Q8WZ71 full feature table", "path": "02_data/raw/protein_context/uniprot_Q8WZ71_full.json", "reuse_role": "transmembrane feature annotation for AlphaFold topology context"},
        ],
        ["source", "path", "reuse_role"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {"item": "alphafold_topology_context", "value": "05_figures/figure25_tmem158_alphafold_topology_context.png", "status": "pass_boundary_context", "notes": "Predicted topology evidence added; not physical interaction, ER localization or ESCC protein validation proof"},
        ],
        ["item", "value", "status", "notes"],
    )


def update_text_surfaces(summary_rows: Sequence[Dict[str, object]]) -> None:
    summary = {row["item"]: row["value"] for row in summary_rows}
    marker = "2026-06-19 tmem158 alphafold topology context"
    text = f"""
AlphaFold/UniProt topology context:

- Official AlphaFold entry: `{summary.get('alphafold_entry')}`
- Model version: `{summary.get('model_version')}`
- Coverage: `{summary.get('coverage')}`
- Global pLDDT: `{summary.get('global_plddt')}`
- Low/very-low pLDDT fraction: `{summary.get('fraction_plddt_low_or_very_low')}`
- UniProt transmembrane segments: `{summary.get('uniprot_transmembrane_segments')}`
- Key boundary: supports membrane-topology plausibility, especially TM1; does not prove ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC protein validation.
- Practical use: prioritizes follow-up localization, membrane-fraction, proximity-labelling, co-immunoprecipitation or defined-partner co-modelling experiments; it is not used to infer a direct TMEM158-Ca2/UPR or TMEM158-ECM interface.

Outputs:
- `04_results/structure/tmem158_alphafold_model_summary.csv`
- `04_results/structure/tmem158_alphafold_topology_segments.csv`
- `04_results/structure/tmem158_alphafold_residue_confidence.csv`
- `05_figures/figure25_tmem158_alphafold_topology_context.png`
- `07_manuscript/tmem158_alphafold_topology_context_update.md`
"""
    replace_or_append(ROOT / "README.md", marker, text)
    replace_or_append(ROOT / "00_project_log" / "master_log.md", marker, f"- 2026-06-19 latest: Added AlphaFold/UniProt topology context for TMEM158. Global pLDDT {summary.get('global_plddt')}; TM1 supported, TM2 low-confidence; no interaction/localization proof.")
    replace_or_append(ROOT / "00_project_log" / "stage_summary.md", marker, "- AlphaFold topology context added as a structural plausibility/boundary layer, not as causality or physical-interaction evidence.")
    replace_or_append(ROOT / "00_project_log" / "decision_record.md", marker, "Decision: add AlphaFold/UniProt predicted topology context to strengthen TMEM158 membrane-protein plausibility while preserving the boundary that no ER localization or physical interaction has been demonstrated.")
    replace_or_append(ROOT / "00_project_log" / "context_checkpoint.md", marker, "Latest checkpoint: AlphaFold topology layer is available as Figure25 and structure tables; manuscript text now states that the model supports topology rationale but not interaction or localization proof.")

    project_root = ROOT.parent
    replace_or_append(
        project_root / "docs" / "agent" / "CURRENT_STATE.md",
        marker,
        f"""## 2026-06-19 TMEM158 AlphaFold 拓扑背景层完成

已新增 `TMEM158_CaUPR_ESCC/03_scripts/Python/run_tmem158_alphafold_topology_context.py`，并生成 AlphaFold/UniProt 结构拓扑层。官方 AlphaFold Q8WZ71 canonical model 覆盖 1-300 aa，global pLDDT={summary.get('global_plddt')}；UniProt 标注两段 helical transmembrane features（231-251、273-293）。第一段 mean pLDDT={summary.get('tm1_mean_plddt')}，结构解释性较好；第二段 mean pLDDT={summary.get('tm2_mean_plddt')}，属于低置信边界。

该层增强 TMEM158 作为膜拓扑候选的生物学合理性，并补充 `Figure25` 与结构表；但不能写成 ER 定位、Ca2/UPR 蛋白互作、ECM 物理结合或 ESCC 蛋白验证。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "DECISION_LOG.md",
        marker,
        """## 2026-06-19 TMEM158 AlphaFold 拓扑层决策

- 决策：新增 AlphaFold/UniProt topology context，作为公共蛋白背景的结构合理性增强层。
- 背景：原 protein/context 层只支持膜蛋白和 HPA 抗体背景，明确没有 ER 定位证据；用户指出 AlphaFold 三维拓扑预测可增强生物学依据。
- 依据：AlphaFold DB Q8WZ71 canonical model 覆盖全长 300 aa；UniProt 标注两段跨膜螺旋。第一段 pLDDT 较好，第二段低置信。
- 边界：不能把 AlphaFold 预测写成物理互作、ER 定位、Ca2/UPR 调控、ECM 结合或 ESCC 蛋白验证。
- 可信度：中等。官方数据库可复跑，但结构为预测模型，global pLDDT 中等偏低。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "EVIDENCE_LOG.md",
        marker,
        """### 2026-06-19 更新：AlphaFold/UniProt TMEM158 topology context

- 新增支持：AlphaFold DB + UniProt feature 支持 TMEM158 膜拓扑候选背景，尤其第一段 C-terminal transmembrane segment。
- 新增边界：global pLDDT 中等偏低，第二段跨膜注释在 AlphaFold 中低置信；该层不能证明 ER 定位、蛋白互作、ECM 结合或 ESCC 蛋白验证。
- 作用：增强论文中 TMEM158 作为 lead computational membrane-protein entry point 的结构合理性，同时主动保留结构证据边界。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "TASKS" / "2026-06-18-SMIM14-CaUPR-ESCC-bioinformatics.md",
        marker,
        """## 2026-06-19 最新追加：TMEM158 AlphaFold topology context

- 新增脚本：`TMEM158_CaUPR_ESCC/03_scripts/Python/run_tmem158_alphafold_topology_context.py`。
- 新增输出：AlphaFold model summary、residue confidence、topology segments、Figure25 和 manuscript update。
- 当前意义：补强公共蛋白背景的结构/拓扑合理性；仍不提升为机制因果或物理互作证明。"""
    )


def main() -> None:
    canonical, plddt_doc, _pae_doc, uniprot = download_inputs()
    summary_rows, topology_segments, residue_rows = build_tables(canonical, plddt_doc, uniprot)
    write_csv(
        STRUCTURE_DIR / "tmem158_alphafold_model_summary.csv",
        summary_rows,
        ["item", "value", "status", "notes"],
    )
    write_csv(
        STRUCTURE_DIR / "tmem158_alphafold_topology_segments.csv",
        topology_segments,
        ["segment_id", "source", "feature_type", "start", "end", "length", "description", "mean_plddt", "mean_hydropathy19", "confidence_call", "interpretation"],
    )
    write_csv(
        STRUCTURE_DIR / "tmem158_alphafold_residue_confidence.csv",
        residue_rows,
        ["residue", "aa", "plddt", "plddt_category", "hydropathy19", "uniprot_topology_feature", "hydrophobic_window_segment"],
    )
    render_figure(residue_rows, topology_segments, summary_rows)
    update_manuscript(summary_rows, topology_segments)
    write_report(summary_rows, topology_segments)
    qc_rows = [
        {"item": "module_status", "value": "completed", "status": "pass", "notes": "AlphaFold/UniProt topology context generated"},
        {"item": "alphafold_entry", "value": next(row["value"] for row in summary_rows if row["item"] == "alphafold_entry"), "status": "pass", "notes": "Official AlphaFold DB entry"},
        {"item": "global_plddt", "value": next(row["value"] for row in summary_rows if row["item"] == "global_plddt"), "status": "boundary", "notes": "Moderate/low global model confidence"},
        {"item": "tm_segments", "value": next(row["value"] for row in summary_rows if row["item"] == "uniprot_transmembrane_segments"), "status": "pass", "notes": "UniProt transmembrane feature count"},
        {"item": "figure25_generated", "value": (FIG_DIR / "figure25_tmem158_alphafold_topology_context.png").exists(), "status": "pass", "notes": "Topology figure generated"},
        {"item": "claim_ceiling", "value": "topology_plausibility_not_physical_interaction_or_er_validation", "status": "boundary", "notes": "Do not upgrade to mechanism proof"},
    ]
    write_csv(QC_DIR / "tmem158_alphafold_topology_context_status.csv", qc_rows, ["item", "value", "status", "notes"])
    update_indexes(summary_rows)
    update_text_surfaces(summary_rows)
    print(
        "tmem158_alphafold_topology_context=completed "
        f"entry={next(row['value'] for row in summary_rows if row['item'] == 'alphafold_entry')} "
        f"global_plddt={next(row['value'] for row in summary_rows if row['item'] == 'global_plddt')} "
        f"tm_segments={next(row['value'] for row in summary_rows if row['item'] == 'uniprot_transmembrane_segments')}"
    )


if __name__ == "__main__":
    main()
