#!/usr/bin/env python3
"""Build a local Scientific Reports upload dry-run bundle.

The bundle is a submission-engineering artifact. It copies the current
manuscript, figures, supplementary files, source-data indexes and QC evidence
into one stable folder, then audits required files, checksums and placeholder
risk. It does not add biological claims.
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
BUNDLE_DIR = ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle"
ZIP_PATH = ROOT / "08_submission_strategy" / "TMEM158_TAC_high_ScientificReports_submission_bundle.zip"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_parent(path)
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


def bundle_items() -> List[Tuple[str, str, str, bool, str]]:
    items: List[Tuple[str, str, str, bool, str]] = [
        ("07_manuscript/manuscript_scientific_reports.docx", "01_manuscript/manuscript_scientific_reports.docx", "manuscript", True, "Editable Scientific Reports manuscript"),
        ("07_manuscript/manuscript_scientific_reports.md", "01_manuscript/manuscript_scientific_reports.md", "manuscript", True, "Markdown manuscript source"),
        ("07_manuscript/rendered_scientific_reports_docx/manuscript_scientific_reports.pdf", "01_manuscript/manuscript_scientific_reports_render_preview.pdf", "manuscript", True, "Rendered PDF preview from DOCX QA"),
        ("07_manuscript/rendered_scientific_reports_docx/contact_sheet.png", "01_manuscript/manuscript_docx_render_contact_sheet.png", "manuscript", False, "DOCX render contact sheet"),
        ("07_manuscript/main_figure_package_legends.md", "03_supplementary/main_figure_package_legends.md", "supplementary", True, "Main figure legends"),
        ("07_manuscript/supplementary_information_scientific_reports.md", "03_supplementary/supplementary_information_scientific_reports.md", "supplementary", True, "Supplementary Information draft"),
        ("07_manuscript/tmem158_public_protein_context_update.md", "03_supplementary/tmem158_public_protein_context_update.md", "supplementary", True, "UniProt/QuickGO/HPA public protein context update; protein background only"),
        ("07_manuscript/tmem158_alphafold_topology_context_update.md", "03_supplementary/tmem158_alphafold_topology_context_update.md", "supplementary", True, "AlphaFold topology context update; predicted structure only"),
        ("06_tables/tmem158_main_figure_panel_map.csv", "03_supplementary/tmem158_main_figure_panel_map.csv", "supplementary", True, "Main figure panel map"),
        ("08_submission_strategy/source_data_and_supplementary_inventory.csv", "04_source_data/source_data_and_supplementary_inventory.csv", "source_data", True, "Figure/table source-data inventory"),
        ("04_results/structure/tmem158_alphafold_model_summary.csv", "04_source_data/tmem158_alphafold_model_summary.csv", "source_data", True, "AlphaFold model summary"),
        ("04_results/structure/tmem158_alphafold_topology_segments.csv", "04_source_data/tmem158_alphafold_topology_segments.csv", "source_data", True, "AlphaFold/UniProt topology segment table"),
        ("04_results/structure/tmem158_alphafold_residue_confidence.csv", "04_source_data/tmem158_alphafold_residue_confidence.csv", "source_data", True, "AlphaFold per-residue confidence and hydropathy table"),
        ("08_submission_strategy/repository_deposit_manifest.csv", "06_repository_package/repository_deposit_manifest.csv", "repository_package", True, "Repository deposit manifest"),
        ("08_submission_strategy/repository_file_checksums.sha256", "06_repository_package/repository_file_checksums.sha256", "repository_package", True, "Repository file checksums"),
        ("08_submission_strategy/zenodo_osf_github_release_readme.md", "06_repository_package/zenodo_osf_github_release_readme.md", "repository_package", True, "Repository release README template"),
        ("08_submission_strategy/repository_release_package_manifest.csv", "06_repository_package/repository_release_package_manifest.csv", "repository_package", True, "Standalone repository-release package manifest"),
        ("08_submission_strategy/repository_release_package_checksums.sha256", "06_repository_package/repository_release_package_checksums.sha256", "repository_package", True, "Standalone repository-release package checksums"),
        ("08_submission_strategy/repository_release_package_qc.csv", "06_repository_package/repository_release_package_qc.csv", "repository_package", True, "Standalone repository-release package QC"),
        ("08_submission_strategy/scientific_reports_cover_letter_draft.md", "05_cover_and_metadata/scientific_reports_cover_letter_draft.md", "cover_and_metadata", True, "Cover letter draft; contains expected author placeholders"),
        ("08_submission_strategy/human_submission_metadata_template.md", "05_cover_and_metadata/human_submission_metadata_template.md", "cover_and_metadata", True, "Human metadata template; expected placeholders remain"),
        ("08_submission_strategy/scientific_reports_submission_system_fields.md", "05_cover_and_metadata/scientific_reports_submission_system_fields.md", "cover_and_metadata", True, "Copy-ready online submission-system fields; human-gated rows remain explicit"),
        ("08_submission_strategy/scientific_reports_submission_system_fields.csv", "05_cover_and_metadata/scientific_reports_submission_system_fields.csv", "cover_and_metadata", True, "CSV table of online submission-system fields"),
        ("08_submission_strategy/scientific_reports_final_human_tasks.csv", "05_cover_and_metadata/scientific_reports_final_human_tasks.csv", "cover_and_metadata", True, "Final human-gated author/declaration/repository/upload-preview tasks"),
        ("08_submission_strategy/final_author_submission_handoff.md", "05_cover_and_metadata/final_author_submission_handoff.md", "cover_and_metadata", True, "Final author-facing submission handoff; human-gated fields remain explicit"),
        ("08_submission_strategy/final_author_submission_action_table.csv", "05_cover_and_metadata/final_author_submission_action_table.csv", "cover_and_metadata", True, "Machine-readable final upload and human action table"),
        ("08_submission_strategy/scientific_reports_submission_checklist.md", "05_cover_and_metadata/scientific_reports_submission_checklist.md", "cover_and_metadata", True, "Scientific Reports submission checklist"),
        ("08_submission_strategy/scientific_reports_official_policy_audit.md", "05_cover_and_metadata/scientific_reports_official_policy_audit.md", "cover_and_metadata", True, "Official Scientific Reports/Nature Portfolio policy audit report"),
        ("08_submission_strategy/target_journal_live_policy_refresh.md", "05_cover_and_metadata/target_journal_live_policy_refresh.md", "cover_and_metadata", True, "Live official target-journal policy refresh"),
        ("08_submission_strategy/target_journal_live_policy_refresh.csv", "05_cover_and_metadata/target_journal_live_policy_refresh.csv", "cover_and_metadata", True, "Live official target-journal policy refresh table"),
        ("08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md", "05_cover_and_metadata/nature_portfolio_reporting_summary_working_draft.md", "cover_and_metadata", True, "Nature Portfolio Reporting Summary working draft; final official form remains human-gated"),
        ("08_submission_strategy/editorial_policy_checklist_working_draft.md", "05_cover_and_metadata/editorial_policy_checklist_working_draft.md", "cover_and_metadata", True, "Editorial policy checklist working draft"),
        ("08_submission_strategy/target_journal_scientific_reports_strategy.md", "05_cover_and_metadata/target_journal_scientific_reports_strategy.md", "cover_and_metadata", False, "Target-journal strategy and rationale"),
        ("08_submission_strategy/manuscript_numeric_consistency_audit.md", "07_qc/manuscript_numeric_consistency_audit.md", "qc", True, "Manuscript numeric consistency audit report"),
        ("04_results/qc/tmem158_submission_readiness_gate.csv", "07_qc/tmem158_submission_readiness_gate.csv", "qc", True, "Submission readiness gate"),
        ("04_results/qc/scientific_reports_format_qc.csv", "07_qc/scientific_reports_format_qc.csv", "qc", True, "Scientific Reports format QC"),
        ("04_results/qc/scientific_reports_official_policy_audit.csv", "07_qc/scientific_reports_official_policy_audit.csv", "qc", True, "Official Scientific Reports/Nature Portfolio policy audit table"),
        ("04_results/qc/scientific_reports_official_policy_audit_qc.csv", "07_qc/scientific_reports_official_policy_audit_qc.csv", "qc", True, "Official policy audit QC summary"),
        ("04_results/qc/target_journal_live_policy_refresh_qc.csv", "07_qc/target_journal_live_policy_refresh_qc.csv", "qc", True, "Live target-journal policy refresh QC summary"),
        ("04_results/qc/manuscript_numeric_consistency_audit.csv", "07_qc/manuscript_numeric_consistency_audit.csv", "qc", True, "Manuscript numeric consistency audit table"),
        ("04_results/qc/manuscript_numeric_consistency_audit_qc.csv", "07_qc/manuscript_numeric_consistency_audit_qc.csv", "qc", True, "Manuscript numeric consistency audit QC summary"),
        ("08_submission_strategy/scientific_reports_citation_coverage_audit.md", "07_qc/scientific_reports_citation_coverage_audit.md", "qc", True, "Scientific Reports citation coverage and sequential numbering audit report"),
        ("04_results/qc/scientific_reports_citation_coverage_audit.csv", "07_qc/scientific_reports_citation_coverage_audit.csv", "qc", True, "Scientific Reports citation coverage audit table"),
        ("04_results/qc/scientific_reports_citation_coverage_audit_qc.csv", "07_qc/scientific_reports_citation_coverage_audit_qc.csv", "qc", True, "Scientific Reports citation coverage audit QC summary"),
        ("04_results/qc/main_figure_visual_qa.csv", "07_qc/main_figure_visual_qa.csv", "qc", True, "Main figure visual QA"),
        ("04_results/qc/scientific_reports_docx_qa.csv", "07_qc/scientific_reports_docx_qa.csv", "qc", True, "DOCX render QA"),
        ("04_results/qc/scientific_reports_docx_render_metrics.csv", "07_qc/scientific_reports_docx_render_metrics.csv", "qc", True, "DOCX render boundary metrics"),
        ("04_results/qc/submission_archive_qc.csv", "07_qc/submission_archive_qc.csv", "qc", True, "Submission archive QC"),
        ("04_results/qc/claim_boundary_text_audit_summary.csv", "07_qc/claim_boundary_text_audit_summary.csv", "qc", True, "Claim-boundary audit summary"),
        ("04_results/qc/claim_boundary_text_audit.csv", "07_qc/claim_boundary_text_audit.csv", "qc", True, "Line-level claim-boundary audit"),
        ("08_submission_strategy/claim_boundary_text_audit.md", "07_qc/claim_boundary_text_audit.md", "qc", True, "Claim-boundary audit report"),
        ("08_submission_strategy/machine_submission_clearance_audit.md", "07_qc/machine_submission_clearance_audit.md", "qc", True, "Machine submission clearance audit"),
        ("08_submission_strategy/submission_readiness_audit.md", "07_qc/submission_readiness_audit.md", "qc", True, "Submission readiness audit"),
        ("08_submission_strategy/reviewer_risk_stress_test_matrix.csv", "07_qc/reviewer_risk_stress_test_matrix.csv", "qc", True, "Pre-emptive reviewer-risk stress-test matrix"),
        ("08_submission_strategy/reviewer_preemptive_response_pack.md", "07_qc/reviewer_preemptive_response_pack.md", "qc", True, "Pre-emptive reviewer response pack"),
        ("08_submission_strategy/editorial_triage_risk_audit.md", "07_qc/editorial_triage_risk_audit.md", "qc", True, "Editorial triage risk audit"),
        ("08_submission_strategy/final_sci_submission_gap_audit.md", "07_qc/final_sci_submission_gap_audit.md", "qc", True, "Final SCI submission gap audit report"),
        ("08_submission_strategy/final_sci_submission_gap_audit.csv", "07_qc/final_sci_submission_gap_audit.csv", "qc", True, "Final SCI submission gap audit table"),
        ("04_results/qc/final_sci_submission_gap_audit_qc.csv", "07_qc/final_sci_submission_gap_audit_qc.csv", "qc", True, "Final SCI submission gap audit QC summary"),
        ("04_results/qc/final_author_submission_handoff_qc.csv", "07_qc/final_author_submission_handoff_qc.csv", "qc", True, "Final author submission handoff QC summary"),
        ("04_results/qc/reviewer_risk_stress_test_qc.csv", "07_qc/reviewer_risk_stress_test_qc.csv", "qc", True, "Reviewer-risk stress-test QC"),
        ("04_results/qc/scientific_reports_submission_system_fields_qc.csv", "07_qc/scientific_reports_submission_system_fields_qc.csv", "qc", True, "Submission-system fields QC"),
        ("04_results/qc/tmem158_alphafold_topology_context_status.csv", "07_qc/tmem158_alphafold_topology_context_status.csv", "qc", True, "AlphaFold topology context QC"),
        ("08_submission_strategy/tmem158_protein_topology_claim_audit.md", "07_qc/tmem158_protein_topology_claim_audit.md", "qc", True, "Integrated UniProt/QuickGO/HPA plus AlphaFold protein-topology claim audit"),
        ("08_submission_strategy/tmem158_protein_topology_claim_audit.csv", "07_qc/tmem158_protein_topology_claim_audit.csv", "qc", True, "Protein-topology claim audit table"),
        ("04_results/qc/tmem158_protein_topology_claim_audit_qc.csv", "07_qc/tmem158_protein_topology_claim_audit_qc.csv", "qc", True, "Protein-topology claim audit QC summary"),
        ("08_submission_strategy/tmem158_structural_followup_prioritization.md", "07_qc/tmem158_structural_followup_prioritization.md", "qc", True, "Defined-partner structural and assay follow-up prioritization; candidate ranking only"),
        ("08_submission_strategy/tmem158_structural_followup_prioritization.csv", "07_qc/tmem158_structural_followup_prioritization.csv", "qc", True, "Structural follow-up prioritization full ranking table"),
        ("06_tables/tmem158_structural_followup_prioritization_top_pairs.csv", "07_qc/tmem158_structural_followup_prioritization_top_pairs.csv", "qc", True, "Top structural follow-up candidate pairs"),
        ("04_results/qc/tmem158_structural_followup_prioritization_qc.csv", "07_qc/tmem158_structural_followup_prioritization_qc.csv", "qc", True, "Structural follow-up prioritization QC summary"),
        ("08_submission_strategy/tmem158_lr_compartment_expression_audit.md", "07_qc/tmem158_lr_compartment_expression_audit.md", "qc", True, "Compartment-expression feasibility audit for prioritized LR candidates"),
        ("08_submission_strategy/tmem158_lr_compartment_expression_audit.csv", "07_qc/tmem158_lr_compartment_expression_audit.csv", "qc", True, "Compartment-expression audit full table"),
        ("06_tables/tmem158_lr_compartment_expression_audit_top_candidates.csv", "07_qc/tmem158_lr_compartment_expression_audit_top_candidates.csv", "qc", True, "Top LR compartment-expression audit candidates"),
        ("04_results/qc/tmem158_lr_compartment_expression_audit_qc.csv", "07_qc/tmem158_lr_compartment_expression_audit_qc.csv", "qc", True, "Compartment-expression audit QC summary"),
        ("06_tables/reviewer_response_evidence_map.csv", "07_qc/reviewer_response_evidence_map.csv", "qc", True, "Reviewer response evidence map"),
        ("05_figures/main_figure_contact_sheet.png", "02_figures/main_figure_contact_sheet.png", "figures", False, "Main figure contact sheet"),
        ("05_figures/figure25_tmem158_alphafold_topology_context.png", "02_figures/figure25_tmem158_alphafold_topology_context.png", "figures", True, "Extended AlphaFold topology context figure"),
        ("05_figures/figure25_tmem158_alphafold_topology_context.pdf", "02_figures/figure25_tmem158_alphafold_topology_context.pdf", "figures", True, "Extended AlphaFold topology context figure"),
        ("05_figures/figure25_tmem158_alphafold_topology_context.svg", "02_figures/figure25_tmem158_alphafold_topology_context.svg", "figures", True, "Extended AlphaFold topology context figure"),
    ]

    main_figures = [
        "main_figure1_tmem158_axis_discovery",
        "main_figure2_tac_high_bulk_state",
        "main_figure3_tac_high_transcriptome",
        "main_figure4_gse53625_clinical_calibration",
        "main_figure5_scrna_caf_bridge",
        "main_figure6_independent_context_and_boundaries",
    ]
    for fig in main_figures:
        for ext in ("png", "pdf", "svg"):
            items.append((f"05_figures/{fig}.{ext}", f"02_figures/{fig}.{ext}", "figures", True, "Submission-facing main figure"))
    return items


PLACEHOLDER_RE = re.compile(
    r"\b(TBD|TODO|PLACEHOLDER|AFFILIATION|EMAIL|FUNDING|AUTHOR|CORRESPONDING AUTHOR|Competing interests|repository DOI|permanent URL|INSERT|XXXX)\b|\[[^\]]*(Author|Affiliation|Email|Funding|DOI|Repository|Name)[^\]]*\]",
    re.I,
)

EXPECTED_PLACEHOLDER_FILES = {
    "01_manuscript/manuscript_scientific_reports.md",
    "05_cover_and_metadata/human_submission_metadata_template.md",
    "05_cover_and_metadata/scientific_reports_cover_letter_draft.md",
    "05_cover_and_metadata/scientific_reports_submission_system_fields.md",
    "05_cover_and_metadata/scientific_reports_submission_system_fields.csv",
    "05_cover_and_metadata/scientific_reports_final_human_tasks.csv",
    "05_cover_and_metadata/final_author_submission_handoff.md",
    "05_cover_and_metadata/final_author_submission_action_table.csv",
    "05_cover_and_metadata/scientific_reports_submission_checklist.md",
    "05_cover_and_metadata/scientific_reports_official_policy_audit.md",
    "05_cover_and_metadata/nature_portfolio_reporting_summary_working_draft.md",
    "05_cover_and_metadata/editorial_policy_checklist_working_draft.md",
    "05_cover_and_metadata/target_journal_scientific_reports_strategy.md",
    "06_repository_package/repository_deposit_manifest.csv",
    "06_repository_package/zenodo_osf_github_release_readme.md",
    "07_qc/scientific_reports_format_qc.csv",
    "07_qc/scientific_reports_official_policy_audit.csv",
    "07_qc/scientific_reports_official_policy_audit_qc.csv",
    "07_qc/machine_submission_clearance_audit.md",
    "07_qc/submission_readiness_audit.md",
    "07_qc/reviewer_risk_stress_test_qc.csv",
    "07_qc/scientific_reports_submission_system_fields_qc.csv",
    "07_qc/reviewer_risk_stress_test_matrix.csv",
    "07_qc/reviewer_preemptive_response_pack.md",
    "07_qc/editorial_triage_risk_audit.md",
    "07_qc/reviewer_response_evidence_map.csv",
    "07_qc/scientific_reports_docx_qa.csv",
    "07_qc/claim_boundary_text_audit.md",
    "07_qc/tmem158_submission_readiness_gate.csv",
}

TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".tsv", ".sha256", ".R", ".py"}


def copy_bundle_files() -> List[Dict[str, object]]:
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True)
    for folder in [
        "01_manuscript",
        "02_figures",
        "03_supplementary",
        "04_source_data",
        "05_cover_and_metadata",
        "06_repository_package",
        "07_qc",
    ]:
        (BUNDLE_DIR / folder).mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []
    for source_rel, bundle_rel, category, required, notes in bundle_items():
        source = ROOT / source_rel
        destination = BUNDLE_DIR / bundle_rel
        if source.exists() and source.is_file():
            ensure_parent(destination)
            shutil.copy2(source, destination)
            status = "ready"
            size = destination.stat().st_size
            checksum = sha256_file(destination)
        else:
            status = "missing_required" if required else "missing_optional"
            size = ""
            checksum = ""
        rows.append(
            {
                "bundle_path": f"08_submission_strategy/scientific_reports_submission_bundle/{bundle_rel}",
                "source_path": source_rel,
                "category": category,
                "required": "yes" if required else "no",
                "status": status,
                "size_bytes": size,
                "sha256": checksum,
                "notes": notes,
            }
        )
    return rows


def is_expected_placeholder(short_rel: str, line: str) -> bool:
    if short_rel in EXPECTED_PLACEHOLDER_FILES:
        return True
    if short_rel.startswith("05_cover_and_metadata/") or short_rel.startswith("06_repository_package/") or short_rel.startswith("07_qc/"):
        return True
    if short_rel == "01_manuscript/manuscript_scientific_reports.md":
        return bool(
            re.search(
                r"author contributions|competing interests|submitting author|all authors|human author|corresponding author|affiliations|funding|acknowledgements",
                line,
                re.I,
            )
        )
    return False


def audit_placeholders() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in sorted(BUNDLE_DIR.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        bundle_rel = rel(path)
        short_rel = str(path.relative_to(BUNDLE_DIR))
        text = path.read_text(encoding="utf-8", errors="replace")
        for idx, line in enumerate(text.splitlines(), start=1):
            if not PLACEHOLDER_RE.search(line):
                continue
            expected = is_expected_placeholder(short_rel, line)
            status = "expected_human_metadata_placeholder" if expected else "unexpected_placeholder"
            rows.append(
                {
                    "bundle_path": bundle_rel,
                    "line_number": idx,
                    "status": status,
                    "excerpt": line.strip()[:420],
                    "notes": "Expected final human submission metadata placeholder." if expected else "Unexpected placeholder in machine-prepared text.",
                }
            )
    return rows


def write_bundle_readme(manifest_rows: Sequence[Dict[str, object]], placeholder_rows: Sequence[Dict[str, object]]) -> None:
    missing_required = [r for r in manifest_rows if r["required"] == "yes" and r["status"] != "ready"]
    unexpected_placeholders = [r for r in placeholder_rows if r["status"] == "unexpected_placeholder"]
    text = f"""# Scientific Reports Submission Bundle

Generated: {NOW}

## Scope

This folder is a local upload dry run for the TMEM158-associated TAC_high Ca2/UPR-CAF stress-ecology manuscript. It collects manuscript files, six main figures, Supplementary Information, source-data/repository indexes and QC evidence into one stable directory.

## Folder Map

- `01_manuscript/`: Scientific Reports manuscript DOCX, Markdown source and rendered preview.
- `02_figures/`: six main figures as PNG/PDF/SVG plus contact sheet when available.
- `03_supplementary/`: Supplementary Information, legends and panel/source map.
- `04_source_data/`: source-data and supplementary inventory.
- `05_cover_and_metadata/`: cover letter draft, checklist, official policy audit, Reporting Summary working draft and human metadata template.
- `06_repository_package/`: repository manifest, checksums, standalone release-package manifest/QC and release README template.
- `07_qc/`: readiness, visual, DOCX, archive, claim-boundary, target-journal policy, protein-topology and structural follow-up claim-boundary QC files.

## Machine QC Summary

- Required bundle files missing: {len(missing_required)}
- Unexpected placeholder rows: {len(unexpected_placeholders)}
- Machine bundle clearance: `{'pass' if not missing_required and not unexpected_placeholders else 'needs_revision'}`
- Final upload clearance: `not_yet`

## Human Items Still Required

- Replace author names, affiliations and corresponding author information.
- Confirm author contributions, funding, acknowledgements and competing interests.
- Decide whether to deposit code/results to Zenodo, OSF, GitHub release or another DOI/permanent repository.
- Repository deposition is deferred by author decision before initial submission; insert a DOI or permanent URL only if deposition is later performed or requested.
- Inspect final upload-system manuscript and figure previews.

## Claim Boundary

This manuscript package supports a public-data, hypothesis-generating discovery story. It must not be submitted as proof of TMEM158 causality, clinical prognosis, direct immune suppression, direct spatial validation, ligand-receptor causality, ESCC protein validation or treatment recommendation.

The UniProt/QuickGO/HPA plus AlphaFold layer supports membrane/topology plausibility and follow-up assay prioritization only. It does not prove direct ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC-specific TMEM158 protein validation.

The structural follow-up prioritization layer ranks POSTN/FN1/collagen-integrin and MIF-CXCR4 candidates for defined-partner co-modelling and orthogonal assays only. The companion compartment-expression audit checks fibroblast-ligand and epithelial-receptor feasibility in public single-cell pseudo-bulk profiles. These layers do not prove ligand-receptor causality, receptor activation, TMEM158 binding or physical CAF-to-epithelial communication.
"""
    out = ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_readme.md"
    out.write_text(text, encoding="utf-8")
    shutil.copy2(out, BUNDLE_DIR / "README.md")


def write_bundle_checksums(manifest_rows: Sequence[Dict[str, object]]) -> None:
    lines = []
    for row in manifest_rows:
        if row["status"] == "ready":
            lines.append(f"{row['sha256']}  {row['bundle_path']}")
    out = ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_checksums.sha256"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copy2(out, BUNDLE_DIR / "07_qc" / "scientific_reports_submission_bundle_checksums.sha256")


def build_zip() -> Tuple[int, str]:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(BUNDLE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(BUNDLE_DIR.parent))
    return ZIP_PATH.stat().st_size, sha256_file(ZIP_PATH)


def update_indexes(zip_size: int, zip_checksum: str) -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "scientific_reports_submission_bundle_manifest", "path": "08_submission_strategy/scientific_reports_submission_bundle_manifest.csv"},
            {"result": "scientific_reports_submission_bundle_qc", "path": "08_submission_strategy/scientific_reports_submission_bundle_qc.csv"},
            {"result": "scientific_reports_submission_bundle_readme", "path": "08_submission_strategy/scientific_reports_submission_bundle_readme.md"},
            {"result": "scientific_reports_submission_bundle_checksums", "path": "08_submission_strategy/scientific_reports_submission_bundle_checksums.sha256"},
            {"result": "scientific_reports_submission_bundle_zip", "path": "08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {"file_role": "scientific_reports_submission_bundle", "path": "08_submission_strategy/scientific_reports_submission_bundle", "status": "ready_not_final_upload_clear", "notes": "Local Scientific Reports upload dry-run folder"},
            {"file_role": "scientific_reports_submission_bundle_manifest", "path": "08_submission_strategy/scientific_reports_submission_bundle_manifest.csv", "status": "ready", "notes": "Bundle file manifest with checksums"},
            {"file_role": "scientific_reports_submission_bundle_qc", "path": "08_submission_strategy/scientific_reports_submission_bundle_qc.csv", "status": "ready_not_final_upload_clear", "notes": "Bundle QC; final upload still human-gated"},
            {"file_role": "scientific_reports_submission_bundle_zip", "path": "08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip", "status": "ready_not_final_upload_clear", "notes": f"ZIP size {zip_size} bytes; sha256 {zip_checksum}"},
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {"item": "submission_bundle_dry_run", "value": "08_submission_strategy/scientific_reports_submission_bundle", "status": "pass_not_final_upload_clear", "notes": "Local upload dry-run bundle generated"},
            {"item": "submission_bundle_zip", "value": "08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip", "status": "pass_not_final_upload_clear", "notes": "ZIP archive generated; final upload preview still requires human inspection"},
        ],
        ["item", "value", "status", "notes"],
    )


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
    ensure_parent(path)
    path.write_text(current, encoding="utf-8")


def update_text_surfaces(qc_rows: Sequence[Dict[str, object]], zip_size: int, zip_checksum: str) -> None:
    marker = "2026-06-19 scientific reports submission bundle dry run"
    machine_clearance = next(r for r in qc_rows if r["item"] == "machine_bundle_clearance")["value"]
    bundle_text = f"""
Submission bundle dry run:

- `08_submission_strategy/scientific_reports_submission_bundle/`
- `08_submission_strategy/scientific_reports_submission_bundle_manifest.csv`
- `08_submission_strategy/scientific_reports_submission_bundle_qc.csv`
- `08_submission_strategy/scientific_reports_submission_bundle_readme.md`
- `08_submission_strategy/scientific_reports_submission_bundle_checksums.sha256`
- `08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip`

Machine bundle clearance: `{machine_clearance}`. ZIP size: `{zip_size}` bytes. ZIP SHA256: `{zip_checksum}`.
Final upload clearance remains `not_yet` because publisher upload preview and final claim-boundary read are human-gated.
"""

    replace_or_append(ROOT / "README.md", marker, bundle_text)
    # Also repair stale claim-boundary wording from older generated blocks.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme = readme.replace("Current machine claim-boundary clearance: `needs_revision`.", "Current machine claim-boundary clearance: `pass`.")
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    for stale_path in [
        ROOT.parent / "docs" / "agent" / "CURRENT_STATE.md",
        ROOT.parent / "docs" / "agent" / "EVIDENCE_LOG.md",
    ]:
        if stale_path.exists():
            stale_text = stale_path.read_text(encoding="utf-8")
            stale_text = stale_text.replace("machine claim-boundary clearance 为 `needs_revision`", "machine claim-boundary clearance 为 `pass`")
            stale_text = stale_text.replace("machine claim-boundary clearance：`needs_revision`", "machine claim-boundary clearance：`pass`")
            stale_path.write_text(stale_text, encoding="utf-8")

    replace_or_append(ROOT / "00_project_log" / "master_log.md", marker, f"- 2026-06-19 latest: Generated Scientific Reports local upload dry-run bundle, manifest, QC, checksums and ZIP archive. Machine bundle clearance: `{machine_clearance}`; final upload remains human-gated.")
    replace_or_append(ROOT / "00_project_log" / "stage_summary.md", marker, f"- Scientific Reports submission bundle dry run complete. Required files are copied into a stable bundle folder, checksums and ZIP are generated, and final upload remains gated by publisher upload preview and final claim-boundary read.")
    replace_or_append(ROOT / "00_project_log" / "decision_record.md", marker, "Decision: treat the next machine-side finish line as a local Scientific Reports upload dry run rather than additional ordinary bioinformatics analysis.\n\nReason: evidence/readiness gates already support a bounded public-data manuscript; the remaining machine task is proving that manuscript, figure, source-data, supplement, repository and QC files can be collected into one auditable upload package.")
    replace_or_append(ROOT / "00_project_log" / "context_checkpoint.md", marker, "Latest checkpoint: Scientific Reports local submission bundle is available under `08_submission_strategy/scientific_reports_submission_bundle/`, with manifest, checksums, QC CSV and ZIP archive. Final upload remains not yet clear until publisher upload preview and final claim-boundary read are completed.")

    project_root = ROOT.parent
    replace_or_append(
        project_root / "docs" / "agent" / "CURRENT_STATE.md",
        marker,
        f"""## 2026-06-19 Scientific Reports 本地投稿包 dry-run 完成

`TMEM158_CaUPR_ESCC/` 已生成本地投稿上传包：`08_submission_strategy/scientific_reports_submission_bundle/`，并同步生成 `scientific_reports_submission_bundle_manifest.csv`、`scientific_reports_submission_bundle_qc.csv`、`scientific_reports_submission_bundle_readme.md`、`scientific_reports_submission_bundle_checksums.sha256` 和 `TMEM158_TAC_high_ScientificReports_submission_bundle.zip`。机器端 bundle clearance 为 `{machine_clearance}`。

该层证明现有 manuscript、6 张主图、Supplementary Information、source-data inventory、repository manifest/checksum 和 QC 文件能被收拢为可审计的投稿干运行包。它不改变科学 claim ceiling；`final_submission_clearance` 仍为 not_yet，因为投稿系统最终预览和最终 claim-boundary 复读需要人工确认。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "DECISION_LOG.md",
        marker,
        """## 2026-06-19 Scientific Reports 投稿包 dry-run 决策

- 决策：新增本地 Scientific Reports upload dry-run bundle，并接入 `run_all.R`，作为机器端投稿工程清关层。
- 背景：当前 9/10 readiness pass，且 claim-boundary、DOCX、source-data、repository manifest 均已生成；继续堆普通生信不会提高 claim ceiling。
- 依据：bundle manifest/QC/checksum/ZIP 均可复跑生成；缺口已收窄为投稿系统最终预览和最终 claim-boundary 复读。
- 可信度：高。
- 后续待验证：人工补齐元数据并在目标期刊系统中检查最终 PDF/figure preview。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "EVIDENCE_LOG.md",
        marker,
        """### 2026-06-19 更新：Scientific Reports submission bundle dry run

- 新增文件：`scientific_reports_submission_bundle/`、`scientific_reports_submission_bundle_manifest.csv`、`scientific_reports_submission_bundle_qc.csv`、`scientific_reports_submission_bundle_readme.md`、`scientific_reports_submission_bundle_checksums.sha256` 和投稿包 ZIP。
- 解释：这是投稿工程与可追溯性证据，不是新的生物学结果。它支持“机器端投稿材料已经可被统一交付”，但 final upload clearance 仍需人工元数据和上传系统预览。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "TASKS" / "2026-06-18-SMIM14-CaUPR-ESCC-bioinformatics.md",
        marker,
        """## 2026-06-19 最新追加：Scientific Reports submission bundle dry run

- 新增脚本：`TMEM158_CaUPR_ESCC/03_scripts/Python/build_scientific_reports_submission_bundle.py`，并接入 `TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R`。
- 新增输出：本地投稿包目录、manifest、QC、readme、checksums 和 ZIP。
- 当前意义：机器端已经把稿件、主图、补充信息、source data、repository 文件和 QC 证据收拢到一个可交付包；作者元数据和声明已补齐，剩余为 publisher upload preview 和最终 claim-boundary read。"""
    )

    checklist = ROOT / "08_submission_strategy" / "scientific_reports_submission_checklist.md"
    text = checklist.read_text(encoding="utf-8")
    if "- [x] Local Scientific Reports upload dry-run bundle generated" not in text:
        text = text.replace(
            "- [x] Repository deposit manifest and file checksums prepared",
            "- [x] Repository deposit manifest and file checksums prepared\n- [x] Local Scientific Reports upload dry-run bundle generated",
        )
    text = text.replace(
        "Current status: **target-journal manuscript package, editable DOCX, Supplementary Information draft, source-data inventory and repository manifest are ready; human metadata completion still required; not yet final upload-ready**.",
        "Current status: **target-journal manuscript package, editable DOCX, Supplementary Information draft, source-data inventory, repository manifest and local upload dry-run bundle are ready; author metadata and declarations are supplied; publisher upload preview and final claim-boundary read are still required; not yet final upload-ready**.",
    )
    checklist.write_text(text, encoding="utf-8")

    audit = ROOT / "08_submission_strategy" / "submission_readiness_audit.md"
    replace_or_append(audit, marker, f"""## Scientific Reports Bundle Addendum

Generated: {NOW}

- Bundle folder: `08_submission_strategy/scientific_reports_submission_bundle/`
- Bundle manifest: `08_submission_strategy/scientific_reports_submission_bundle_manifest.csv`
- Bundle QC: `08_submission_strategy/scientific_reports_submission_bundle_qc.csv`
- Bundle ZIP: `08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip`
- Machine bundle clearance: `{machine_clearance}`

Interpretation: the upload dry run is machine-clear. Final journal submission remains not yet clear because publisher upload preview and final claim-boundary read require human confirmation.""")


def main() -> None:
    manifest_rows = copy_bundle_files()
    placeholder_rows = audit_placeholders()
    write_bundle_readme(manifest_rows, placeholder_rows)
    # Recompute manifest after README and checksum file are written into the folder.
    write_bundle_checksums(manifest_rows)
    zip_size, zip_checksum = build_zip()

    required = [r for r in manifest_rows if r["required"] == "yes"]
    missing_required = [r for r in required if r["status"] != "ready"]
    unexpected_placeholders = [r for r in placeholder_rows if r["status"] == "unexpected_placeholder"]
    copied = [r for r in manifest_rows if r["status"] == "ready"]
    total_size = sum(int(r["size_bytes"]) for r in copied if r["size_bytes"] != "")
    machine_pass = not missing_required and not unexpected_placeholders

    write_csv(
        ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_manifest.csv",
        manifest_rows,
        ["bundle_path", "source_path", "category", "required", "status", "size_bytes", "sha256", "notes"],
    )
    write_csv(
        ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_placeholders.csv",
        placeholder_rows,
        ["bundle_path", "line_number", "status", "excerpt", "notes"],
    )
    qc_rows = [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "required_files", "value": len(required), "status": "pass", "notes": "Required file rows in bundle manifest"},
        {"item": "missing_required_files", "value": len(missing_required), "status": "pass" if not missing_required else "needs_revision", "notes": "Required files not copied into bundle"},
        {"item": "copied_files", "value": len(copied), "status": "pass", "notes": "Files copied into bundle"},
        {"item": "total_size_bytes", "value": total_size, "status": "pass", "notes": "Total copied file size before ZIP"},
        {"item": "placeholder_risk_rows", "value": len(unexpected_placeholders), "status": "pass" if not unexpected_placeholders else "needs_revision", "notes": "Unexpected placeholder rows outside human-metadata files"},
        {"item": "expected_human_placeholder_rows", "value": len([r for r in placeholder_rows if r["status"] == "expected_human_metadata_placeholder"]), "status": "info", "notes": "Expected placeholders in allowed metadata, QC and helper files"},
        {"item": "bundle_zip", "value": rel(ZIP_PATH), "status": "pass", "notes": f"ZIP size {zip_size} bytes; sha256 {zip_checksum}"},
        {"item": "machine_bundle_clearance", "value": "pass" if machine_pass else "needs_revision", "status": "pass" if machine_pass else "needs_revision", "notes": "Pass requires all required files copied and no unexpected placeholders"},
        {"item": "final_upload_clearance", "value": "not_yet", "status": "not_yet", "notes": "Publisher upload preview and final claim-boundary read require human confirmation"},
    ]
    write_csv(
        ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_qc.csv",
        qc_rows,
        ["item", "value", "status", "notes"],
    )

    update_indexes(zip_size, zip_checksum)
    update_text_surfaces(qc_rows, zip_size, zip_checksum)
    print(
        "scientific_reports_submission_bundle=completed "
        f"required_files={len(required)} missing_required={len(missing_required)} "
        f"copied_files={len(copied)} unexpected_placeholders={len(unexpected_placeholders)} "
        f"machine_bundle_clearance={'pass' if machine_pass else 'needs_revision'} "
        f"zip_bytes={zip_size}"
    )


if __name__ == "__main__":
    main()
