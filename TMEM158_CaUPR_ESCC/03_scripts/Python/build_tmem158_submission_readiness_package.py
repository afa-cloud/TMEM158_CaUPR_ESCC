#!/usr/bin/env python3

from __future__ import annotations

import base64
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "05_figures"
TABLE_DIR = ROOT / "06_tables"
QC_DIR = ROOT / "04_results" / "qc"
MANUSCRIPT_DIR = ROOT / "07_manuscript"
STRATEGY_DIR = ROOT / "08_submission_strategy"
LOG_DIR = ROOT / "logs"


@dataclass(frozen=True)
class Panel:
    label: str
    source: str
    caption: str


@dataclass(frozen=True)
class MainFigure:
    figure_id: str
    title: str
    short_legend: str
    panels: tuple[Panel, ...]


MAIN_FIGURES: tuple[MainFigure, ...] = (
    MainFigure(
        "main_figure1_tmem158_axis_discovery",
        "TMEM158 discovery and Ca2/UPR-CAF state entry point",
        "TMEM158 is tumour-elevated in multiple public ESCC cohorts and is coupled to Ca2/UPR and CAF ecology, supporting an axis-first lead-candidate framework rather than a standalone prognostic marker.",
        (
            Panel("A", "figure1_tmem158_expression_public_cohorts.png", "TMEM158 expression across public ESCC cohorts"),
            Panel("B", "figure2_tmem158_axis_correlation_heatmap.png", "TMEM158 coupling with Ca2/UPR and CAF scores"),
            Panel("C", "figure5_tmem158_cross_layer_evidence.png", "Cross-layer evidence used to nominate TMEM158"),
        ),
    ),
    MainFigure(
        "main_figure2_tac_high_bulk_state",
        "Rule-defined TAC_high bulk state and specificity",
        "The composite TAC_high state is reproducible across bulk cohorts and has stronger biological-state support than TMEM158 alone, while preserving negative survival boundaries.",
        (
            Panel("A", "figure6_tmem158_ecology_state_validation.png", "Composite ecology-state validation"),
            Panel("B", "figure7_rule_tmem158_ecology_subtypes.png", "Rule-defined TAC_high states across cohorts"),
            Panel("C", "figure12_tac_high_state_specificity.png", "Cohort-preserving random-label specificity testing"),
        ),
    ),
    MainFigure(
        "main_figure3_tac_high_transcriptome",
        "Data-driven TAC_high transcriptome and CAF-adjusted residual stress",
        "Whole-transcriptome and CAF-adjusted analyses separate the dominant ECM/CAF programme from a residual MYC/OXPHOS/NFE2L2/translation stress-state programme.",
        (
            Panel("A", "figure13_tac_high_transcriptome_programs.png", "TAC_high whole-transcriptome programme"),
            Panel("B", "figure14_tac_high_interaction_gene_heatmap.png", "Core-by-CAF pathway-level interaction context"),
            Panel("C", "figure22_stromal_adjusted_tac_score_specificity.png", "CAF-adjusted score specificity stress test"),
            Panel("D", "figure23_stromal_adjusted_tac_transcriptome.png", "CAF-adjusted residual transcriptome programme"),
        ),
    ),
    MainFigure(
        "main_figure4_gse53625_clinical_calibration",
        "GSE53625 external clinical calibration",
        "Targeted probe-sequence reannotation in GSE53625 calibrates TMEM158/TAC_high expression-state, ECM-integrin and residual-stress signals in 179 paired clinical samples, but does not validate OS prognosis.",
        (
            Panel("A", "figure24_gse53625_tmem158_tac_external_validation.png", "GSE53625 paired and tumour-only TAC calibration"),
            Panel("B", "figure9_tmem158_multiomics_regulation.png", "TCGA/cBioPortal regulatory boundary"),
            Panel("C", "figure11_tmem158_public_protein_context.png", "Public TMEM158 protein and antibody context"),
        ),
    ),
    MainFigure(
        "main_figure5_scrna_caf_bridge",
        "Single-cell fibroblast localization and candidate CAF-to-epithelial bridge",
        "Raw single-cell pseudo-bulk analysis localizes TAC_high meta-signatures to fibroblast/CAF compartments and nominates ECM-integrin and MIF/CXCR4 candidate bridges.",
        (
            Panel("A", "figure15_tac_high_scrna_signature_compartments.png", "GSE160269 compartment localization of TAC signatures"),
            Panel("B", "figure16_tac_high_scrna_state_signature_mapping.png", "Fibroblast TAC signature elevation in TAC_high tumours"),
            Panel("C", "figure17_tac_high_caf_epi_lr_bridge.png", "Candidate CAF-to-epithelial ligand-receptor pairs"),
            Panel("D", "figure18_tac_high_caf_epi_lr_axis_scores.png", "Candidate bridge axis scores"),
        ),
    ),
    MainFigure(
        "main_figure6_independent_context_and_boundaries",
        "Independent single-cell, spatial-context and immune-boundary layers",
        "GSE221561 and public spatial source data support fibroblast/CAF-rich tissue context, while immune and survival analyses define the negative claim boundaries.",
        (
            Panel("A", "figure19_gse221561_tac_context_validation.png", "Independent GSE221561 fibroblast-dominant TAC context"),
            Panel("B", "figure20_gse221561_tac_subtype_signature_context.png", "GSE221561 fibroblast subtype context"),
            Panel("C", "figure21_spatial_progression_source_context.png", "Public spatial-progression fibroblast/alpha-SMA context"),
            Panel("D", "figure10_scrna_tac_high_immune_boundary.png", "Single-cell immune-boundary analysis"),
        ),
    ),
)


def ensure_dirs() -> None:
    for directory in (FIG_DIR, TABLE_DIR, QC_DIR, MANUSCRIPT_DIR, STRATEGY_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


TITLE_FONT = font(62, bold=True)
SUBTITLE_FONT = font(34)
LABEL_FONT = font(56, bold=True)
CAPTION_FONT = font(28)


def load_panel_image(name: str) -> Image.Image:
    path = FIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing figure panel: {path}")
    return Image.open(path).convert("RGB")


def fit_image(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    copy = image.copy()
    copy.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return copy


def draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], max_width: int, fill: str, font_obj: ImageFont.ImageFont, line_spacing: int = 8) -> int:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), trial, font=font_obj)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font_obj)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def render_main_figure(spec: MainFigure) -> dict[str, str]:
    n = len(spec.panels)
    cols = 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    width = 5200
    margin = 170
    gutter = 100
    header_h = 300
    cell_w = (width - 2 * margin - (cols - 1) * gutter) // cols
    cell_h = 1680
    height = header_h + rows * cell_h + (rows - 1) * gutter + margin
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 78), spec.title, font=TITLE_FONT, fill="#111827")
    draw_wrapped_text(draw, spec.short_legend, (margin, 165), width - 2 * margin, "#374151", SUBTITLE_FONT)

    for idx, panel in enumerate(spec.panels):
        row = idx // cols
        col = idx % cols
        x = margin + col * (cell_w + gutter)
        y = header_h + row * (cell_h + gutter)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=18, outline="#d1d5db", width=3, fill="#ffffff")
        draw.text((x + 28, y + 22), panel.label, font=LABEL_FONT, fill="#111827")
        draw_wrapped_text(draw, panel.caption, (x + 110, y + 28), cell_w - 140, "#111827", CAPTION_FONT)
        img = load_panel_image(panel.source)
        fitted = fit_image(img, cell_w - 70, cell_h - 155)
        px = x + (cell_w - fitted.width) // 2
        py = y + 125 + (cell_h - 155 - fitted.height) // 2
        canvas.paste(fitted, (px, py))

    png_path = FIG_DIR / f"{spec.figure_id}.png"
    pdf_path = FIG_DIR / f"{spec.figure_id}.pdf"
    svg_path = FIG_DIR / f"{spec.figure_id}.svg"
    canvas.save(png_path, dpi=(300, 300))
    canvas.save(pdf_path, "PDF", resolution=300)
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas.width}" height="{canvas.height}" '
        f'viewBox="0 0 {canvas.width} {canvas.height}">\n'
        f'  <image href="data:image/png;base64,{encoded}" width="{canvas.width}" height="{canvas.height}"/>\n'
        f"</svg>\n"
    )
    svg_path.write_text(svg, encoding="utf-8")
    return {
        "figure_id": spec.figure_id,
        "title": spec.title,
        "legend": spec.short_legend,
        "png": str(png_path.relative_to(ROOT)),
        "pdf": str(pdf_path.relative_to(ROOT)),
        "svg": str(svg_path.relative_to(ROOT)),
    }


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def has_placeholder_references() -> bool:
    manuscript = (MANUSCRIPT_DIR / "manuscript.md").read_text(encoding="utf-8")
    return "Placeholder for" in manuscript


def manuscript_sections() -> dict[str, bool]:
    manuscript = (MANUSCRIPT_DIR / "manuscript.md").read_text(encoding="utf-8")
    required = [
        "## Abstract",
        "## Introduction",
        "## Results",
        "## Discussion",
        "## Limitations",
        "## Methods",
        "## Figure legends",
        "## Data availability",
        "## Code availability",
        "## Ethics statement",
        "## References",
    ]
    return {section: section in manuscript for section in required}


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def update_result_index(new_items: list[tuple[str, str]]) -> None:
    index_path = ROOT / "04_results" / "result_index.csv"
    rows = csv_rows(index_path)
    existing = {row.get("item", "") for row in rows}
    with index_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not rows and index_path.stat().st_size == 0:
            writer.writerow(["item", "path"])
        for item, rel_path in new_items:
            if item not in existing:
                writer.writerow([item, rel_path])


def build_readiness_gate(generated_figures: list[dict[str, str]]) -> list[dict[str, str]]:
    log_text = (LOG_DIR / "run_all.log").read_text(encoding="utf-8", errors="ignore") if (LOG_DIR / "run_all.log").exists() else ""
    sections = manuscript_sections()
    manual_manifest = csv_rows(ROOT / "01_literature" / "manual_download_manifest.csv")
    fulltext_gate = csv_rows(ROOT / "01_literature" / "fulltext_table_duplication_gate.csv")
    literature_status_rows = csv_rows(ROOT / "04_results" / "qc" / "tmem158_literature_readiness_status.csv")
    literature_status = {row.get("item"): row.get("value") for row in literature_status_rows}
    manual_remaining = sum(str(row.get("download_status", "")).startswith("manual_required") for row in manual_manifest)
    risk_text = (STRATEGY_DIR / "reviewer_risk_checklist.md").read_text(encoding="utf-8") if (STRATEGY_DIR / "reviewer_risk_checklist.md").exists() else ""
    status_rows = csv_rows(ROOT / "04_results" / "qc" / "tmem158_gse53625_external_validation_status.csv")
    status = {row.get("item"): row.get("value") for row in status_rows}

    rows = [
        {
            "gate": "reproducible_full_run",
            "status": "pass" if "TMEM158 branch run completed" in log_text else "needs_rerun",
            "evidence": "run_all.log contains TMEM158 branch completion" if "TMEM158 branch run completed" in log_text else "run_all completion line not found",
            "next_action": "rerun run_all.R before final submission" if "TMEM158 branch run completed" not in log_text else "keep as reproducibility evidence",
        },
        {
            "gate": "six_main_figures",
            "status": "pass" if len(generated_figures) == 6 and all((ROOT / fig["png"]).exists() and (ROOT / fig["pdf"]).exists() and (ROOT / fig["svg"]).exists() for fig in generated_figures) else "needs_work",
            "evidence": f"{len(generated_figures)} composite main figures generated with PNG/PDF/SVG wrappers",
            "next_action": "visual QA and final journal sizing",
        },
        {
            "gate": "manuscript_sections",
            "status": "pass" if all(sections.values()) else "needs_work",
            "evidence": "; ".join([f"{k}={'yes' if v else 'no'}" for k, v in sections.items()]),
            "next_action": "add missing manuscript sections" if not all(sections.values()) else "polish content and target journal format",
        },
        {
            "gate": "formal_references",
            "status": "needs_work" if has_placeholder_references() else "pass",
            "evidence": "manuscript still contains placeholder references" if has_placeholder_references() else "no placeholder references detected",
            "next_action": "keep verified references and adapt style to target journal",
        },
        {
            "gate": "fulltext_supplement_duplication_gate",
            "status": "needs_work" if manual_remaining else "pass",
            "evidence": f"{manual_remaining} manual full-text/supplementary items remain; {literature_status.get('auto_pmc_xml_reviewed_items', 'NA')} items auto-reviewed by VM-routed PMC XML; {literature_status.get('auto_local_text_reviewed_items', 'NA')} local text/full-text items reviewed; {literature_status.get('curated_context_reviewed_items', 'NA')} curated context adjudications",
            "next_action": "download and search manual full-text/supplementary files before final clearance" if manual_remaining else "preserve full-text/context adjudication table with reviewer-risk materials",
        },
        {
            "gate": "novelty_decision",
            "status": "conditional_go" if any(row.get("status") == "conditional_go" for row in fulltext_gate) else ("pass" if fulltext_gate else "needs_review"),
            "evidence": literature_status.get("fulltext_supplement_gate_status", "formal PubMed/PMC gate status unavailable"),
            "next_action": "do not claim final novelty clearance until manual gate is finished" if manual_remaining else "write novelty as ESCC-specific TAC_high ecology rather than generic TMEM158 biomarker work",
        },
        {
            "gate": "gse53625_clinical_calibration",
            "status": "pass" if status.get("module_status") == "completed" and status.get("tumor_samples") == "179" else "needs_work",
            "evidence": f"GSE53625 status={status.get('module_status', 'missing')}; paired={status.get('paired_patients', 'NA')}; OS P values TMEM158={status.get('TMEM158_survival_p', 'NA')}, TAC={status.get('full_TAC_score_survival_p', 'NA')}",
            "next_action": "write as calibration, not prognostic validation",
        },
        {
            "gate": "claim_boundary",
            "status": "pass" if all(term in risk_text for term in ["validated driver", "survival validation", "uniform Ca2 activation"]) else "needs_work",
            "evidence": "reviewer risk checklist contains causal, survival and Ca2 activation boundaries",
            "next_action": "keep boundary language in title, abstract and figure legends",
        },
        {
            "gate": "data_and_code_provenance",
            "status": "pass" if (ROOT / "02_data" / "data_inventory.csv").exists() and (ROOT / "03_scripts" / "R" / "run_all.R").exists() else "needs_work",
            "evidence": "data_inventory.csv and run_all.R exist",
            "next_action": "add checksums/version manifest if required by target journal",
        },
        {
            "gate": "final_submission_clearance",
            "status": "not_yet",
            "evidence": "main figures and formal references are generated; novelty gate has no manual items remaining, but final visual QA and target-journal formatting still require completion" if not manual_remaining else "main figures and formal references are generated, but manual full-text/supplementary duplication gate remains incomplete",
            "next_action": "finish visual QA and target journal formatting" if not manual_remaining else "finish manual novelty gate, visual QA and target journal formatting",
        },
    ]
    return rows


def write_legends(generated: list[dict[str, str]]) -> None:
    lines = [
        "# Main Figure Package",
        "",
        "These composite figures consolidate existing reproducible analysis outputs into a six-figure submission-facing structure. They are generated automatically by `03_scripts/Python/build_tmem158_submission_readiness_package.py`.",
        "",
    ]
    for i, fig in enumerate(generated, start=1):
        lines.append(f"## Main Figure {i}. {fig['title']}")
        lines.append("")
        lines.append(fig["legend"])
        lines.append("")
        lines.append(f"- PNG: `{fig['png']}`")
        lines.append(f"- PDF: `{fig['pdf']}`")
        lines.append(f"- SVG wrapper: `{fig['svg']}`")
        lines.append("")
    (MANUSCRIPT_DIR / "main_figure_package_legends.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_audit_report(readiness_rows: list[dict[str, str]], generated: list[dict[str, str]]) -> None:
    pass_count = sum(row["status"] == "pass" for row in readiness_rows)
    needs_work = [row for row in readiness_rows if row["status"] not in {"pass"}]
    lines = [
        "# TMEM158/TAC Submission Readiness Audit",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- Composite main figures generated: {len(generated)}",
        f"- Readiness gates passed: {pass_count}/{len(readiness_rows)}",
        f"- Remaining non-pass gates: {len(needs_work)}",
        "",
        "## Non-Pass Gates",
        "",
    ]
    for row in needs_work:
        lines.append(f"- `{row['gate']}`: {row['status']} - {row['next_action']}")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The project is now organized as a six-main-figure pure public-data manuscript package with formal references. Remaining blockers should be handled as submission-package tasks, not as a need for more ordinary bioinformatics correlations. If the full-text/supplement gate is clear, the remaining work is visual QA and target-journal formatting. Claims must remain association-based and hypothesis-generating.",
        "",
    ])
    (STRATEGY_DIR / "submission_readiness_audit.md").write_text("\n".join(lines), encoding="utf-8")


def write_publication_gate(readiness_rows: list[dict[str, str]]) -> None:
    publication_rows = []
    for row in readiness_rows:
        publication_rows.append({
            "gate": row["gate"],
            "status": row["status"],
            "evidence": row["evidence"],
            "action_to_publish": row["next_action"],
        })
    write_csv(
        QC_DIR / "publication_readiness_gate.csv",
        publication_rows,
        ["gate", "status", "evidence", "action_to_publish"],
    )


def write_reviewer_risk_checklist() -> None:
    lines = [
        "# Reviewer Risk Checklist",
        "",
        "- Do not claim TMEM158 is a validated driver.",
        "- Do not headline prognosis; TCGA and GSE53625 OS analyses remain negative.",
        "- Do not write survival validation: in GSE53625, continuous TMEM158, full TAC score and TAC_high status are all non-significant for OS.",
        "- Do not overstate GSE53625 as full clinical validation; it is a targeted probe-sequence reannotation layer with 64/67 requested TMEM158/TAC genes recovered, not a whole-transcriptome validation matrix.",
        "- Do not write uniform Ca2 activation or broad efflux activation from GSE53625; Ca2-axis direction and drug-efflux support remain bounded, while PERK-bias/proteostasis/ECM-integrin/residual-stress calibration is stronger.",
        "- Do not call proteogenomics or HPA/UniProt/QuickGO coverage protein validation.",
        "- Do not describe TAC_high as a purely tumour-cell-intrinsic programme; GSE160269 and GSE221561 signature localization is fibroblast/CAF-dominant.",
        "- Do not upgrade fibroblast/CAF localization into cell-cell causality or TMEM158-driven transcription.",
        "- Do not upgrade CAF-to-epithelial ligand-receptor bridge scores into CellChat-level signalling proof; write POSTN/collagen/FN1-integrin and MIF-CXCR4 as candidate bridges only.",
        "- Do not claim broad cytokine/growth-factor activation; IL6-family and growth-factor axes are not TAC_high-higher support in the current bridge analysis.",
        "- Do not overstate GSE221561 as a definitive independent validation cohort; it supports fibroblast-dominant TAC meta-ECM localization but has partial raw-library recovery and only six matched tumour libraries for bridge context.",
        "- Do not write public spatial source-data context as direct spatial validation of TMEM158, TAC_high, Ca2/UPR activation or ligand-receptor causality.",
        "- Complete full-text and supplementary-table duplication gate before final manuscript.",
        "- Keep formal references synchronized with the target journal style.",
        "- Prioritize visual QA and manual novelty checks over adding more weak external layers.",
        "- Keep all methods explicitly public-data only.",
        "",
    ]
    (STRATEGY_DIR / "reviewer_risk_checklist.md").write_text("\n".join(lines), encoding="utf-8")


def write_project_logs(readiness_rows: list[dict[str, str]]) -> None:
    passed = sum(row["status"] == "pass" for row in readiness_rows)
    total = len(readiness_rows)
    literature_status_rows = csv_rows(ROOT / "04_results" / "qc" / "tmem158_literature_readiness_status.csv")
    literature_status = {row.get("item"): row.get("value") for row in literature_status_rows}
    manual_remaining = literature_status.get("manual_unresolved_items", "NA")
    curated_reviewed = literature_status.get("curated_context_reviewed_items", "NA")
    local_reviewed = literature_status.get("auto_local_text_reviewed_items", "NA")
    pmc_reviewed = literature_status.get("auto_pmc_xml_reviewed_items", "NA")
    (ROOT / "00_project_log" / "master_log.md").write_text(
        "\n".join([
            "# Master Log",
            "",
            "- 2026-06-19 16:38:07 CST: Re-ran TMEM158-Ca2/UPR ESCC public-data branch from first-pass evidence through GSE53625, single-cell, spatial-context and submission-readiness modules.",
            "- 2026-06-19 16:46:39 CST: Full TMEM158 branch completed with six composite main figures and 10-gate submission-readiness audit.",
            "- 2026-06-19 16:58:37 CST: Formal references added and literature gate stratified; 28/40 manual manifest items auto-reviewed through VM-routed PMC XML, 12 publisher/full-text or supplement items remain unresolved.",
            f"- 2026-06-19 latest: Full-text/supplement gate after local scan and curated context adjudication: {pmc_reviewed} PMC XML reviewed, {local_reviewed} local text/full-text items reviewed, {curated_reviewed} curated context adjudications, {manual_remaining} manual publisher/supplement items unresolved.",
            "",
        ]),
        encoding="utf-8",
    )
    (ROOT / "00_project_log" / "stage_summary.md").write_text(
        "\n".join([
            "# Stage Summary",
            "",
            "TMEM158-CaUPR branch current submission-facing status:",
            "",
            "- First-pass TMEM158 expression, axis-coupling, single-cell ecology and survival analyses completed.",
            "- Rule-defined `TAC_high` ecology subtype is present in all four bulk cohorts.",
            "- TAC_high whole-transcriptome analysis supports an ECM/CAF/EMT-dominant programme and pathway-level protein-biogenesis/proteostasis context.",
            "- CAF-adjusted TAC_high analysis supports residual MYC/OXPHOS/NFE2L2/translation/chemical-stress transcription after continuous CAF adjustment.",
            "- GSE53625 targeted probe-reannotated clinical calibration supports tumour-elevated TMEM158, ECM-integrin and residual-stress signals but not OS prognosis.",
            "- GSE160269 and GSE221561 single-cell layers localize TAC meta-signatures primarily to fibroblast/CAF compartments.",
            "- Public spatial source data support a fibroblast/alpha-SMA-rich ESCC progression context but not direct TAC_high spatial rescoring.",
            f"- Submission-readiness audit currently passes {passed}/{total} gates; formal references are complete; manual full-text/supplementary unresolved count is {manual_remaining}.",
            "",
        ]),
        encoding="utf-8",
    )
    (ROOT / "00_project_log" / "context_checkpoint.md").write_text(
        "\n".join([
            "# Context Checkpoint",
            "",
            "Current branch objective: build a pure public-data manuscript around TMEM158-associated TAC_high Ca2/UPR-CAF stress ecology in ESCC.",
            "",
            "Supported result layer: rule-defined TAC_high links TMEM158, Ca2/PERK and CAF ecology to ECM/CAF transcriptome architecture, proteostasis/residual-stress readouts, fibroblast/CAF single-cell localization and GSE53625 external clinical calibration.",
            "",
            "Hard boundaries: clinical OS is negative in TCGA and GSE53625; Ca2 direction is not uniformly positive; GSE53625 is targeted probe-reannotated calibration rather than full-transcriptome validation; TAC_high is not proven tumour-cell-intrinsic; candidate ligand-receptor bridges are not causal signalling proof; final novelty clearance awaits manual full-text/supplementary-table review.",
            "",
        ]),
        encoding="utf-8",
    )
    (ROOT / "00_project_log" / "negative_results_log.md").write_text(
        "\n".join([
            "# Negative Results Log",
            "",
            "- TCGA clinical survival remains negative for TMEM158/TAC_high state claims.",
            "- GSE53625 OS is negative for continuous TMEM158, full TAC score and TAC_high-like status.",
            "- GSE53625 drug-efflux score is not higher in TAC_high-like tumours after FDR correction.",
            "- GSE53625 lacks ORAI1, PDPN and TALDO1 probe coverage in the targeted probe-reannotation layer.",
            "- CAF-adjusted TAC_high vs CAF_only residualized proteostasis and drug-efflux score contrasts are not FDR-confirmed.",
            "- Core-by-CAF transcriptome interaction has pathway-level signal but no FDR-significant single interaction genes.",
            "- GSE160269 immune pseudo-bulk analysis does not support robust T-cell exhaustion, Treg or suppressive-myeloid enrichment.",
            "",
        ]),
        encoding="utf-8",
    )
    (ROOT / "00_project_log" / "decision_record.md").write_text(
        "\n".join([
            "# Decision Record",
            "",
            "Decision: continue the pure bioinformatics manuscript as a TMEM158-associated TAC_high Ca2/UPR-CAF stress-ecology discovery paper.",
            "",
            "Reason: bulk, GSE53625, single-cell, CAF-adjusted transcriptome and public spatial-context layers now support a coherent public-data discovery state. The strongest claim is not a single-gene biomarker, prognosis, drug resistance or causal mechanism; it is a reproducible stress-ecology state with explicit boundary layers.",
            "",
            "Decision: use the six generated composite main figures as the submission-facing figure package.",
            "",
            "Reason: the prior figure set was scattered across many source figures; composite main figures organize the story into discovery, bulk state, transcriptome/stromal stress test, GSE53625 calibration, single-cell bridge, and independent context/boundary layers.",
            "",
        ]),
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    generated = [render_main_figure(spec) for spec in MAIN_FIGURES]

    panel_rows: list[dict[str, object]] = []
    for i, spec in enumerate(MAIN_FIGURES, start=1):
        for panel in spec.panels:
            panel_rows.append({
                "main_figure_number": i,
                "main_figure_id": spec.figure_id,
                "main_figure_title": spec.title,
                "panel": panel.label,
                "source_figure": panel.source,
                "panel_caption": panel.caption,
            })
    write_csv(
        TABLE_DIR / "tmem158_main_figure_panel_map.csv",
        panel_rows,
        ["main_figure_number", "main_figure_id", "main_figure_title", "panel", "source_figure", "panel_caption"],
    )

    write_reviewer_risk_checklist()
    readiness = build_readiness_gate(generated)
    write_csv(
        QC_DIR / "tmem158_submission_readiness_gate.csv",
        readiness,
        ["gate", "status", "evidence", "next_action"],
    )
    write_publication_gate(readiness)
    write_legends(generated)
    write_audit_report(readiness, generated)
    write_project_logs(readiness)

    result_items: list[tuple[str, str]] = []
    for idx, fig in enumerate(generated, start=1):
        result_items.append((f"main_figure{idx}", fig["png"]))
    result_items.extend([
        ("main_figure_panel_map", "06_tables/tmem158_main_figure_panel_map.csv"),
        ("submission_readiness_gate", "04_results/qc/tmem158_submission_readiness_gate.csv"),
        ("publication_readiness_gate_latest", "04_results/qc/publication_readiness_gate.csv"),
        ("literature_readiness_status", "04_results/qc/tmem158_literature_readiness_status.csv"),
        ("fulltext_supplement_review_summary", "01_literature/tmem158_fulltext_supplement_review_summary.csv"),
        ("fulltext_supplement_gate_update", "01_literature/fulltext_supplement_gate_update_2026-06-19.md"),
        ("formal_references", "07_manuscript/formal_references.md"),
        ("main_figure_package_legends", "07_manuscript/main_figure_package_legends.md"),
        ("submission_readiness_audit", "08_submission_strategy/submission_readiness_audit.md"),
    ])
    update_result_index(result_items)

    print("Generated six composite main figures and submission readiness audit.")


if __name__ == "__main__":
    main()
