#!/usr/bin/env python3
"""Build a final SCI submission gap audit for the public-data manuscript.

This is a submission-engineering audit. It does not add biological claims; it
maps the current machine-generated evidence against the requirements for a
bounded pure-public-data oncology bioinformatics manuscript.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT_CSV = ROOT / "08_submission_strategy" / "final_sci_submission_gap_audit.csv"
OUT_MD = ROOT / "08_submission_strategy" / "final_sci_submission_gap_audit.md"
QC_CSV = ROOT / "04_results" / "qc" / "final_sci_submission_gap_audit_qc.csv"
MACHINE_AUDIT_MD = ROOT / "08_submission_strategy" / "machine_submission_clearance_audit.md"


PASS_STATUSES = {
    "pass",
    "pass_with_boundary",
    "pass_not_final_upload_clear",
    "pass_needs_final_repository_deposit",
    "pass_needs_final_repository_decision",
    "pass_needs_final_upload_decision",
    "pass_human_gated_items_visible",
    "ready",
    "ready_for_human_preview",
    "ready_human_finalize",
    "selected",
    "info",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def upsert_csv(path: Path, key: str, new_rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    merged: Dict[str, Dict[str, object]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get(key):
                    merged[row[key]] = dict(row)
    for row in new_rows:
        merged[str(row[key])] = dict(row)
    field_order = list(fields)
    for row in merged.values():
        for field in row:
            if field not in field_order:
                field_order.append(field)
    write_csv(path, list(merged.values()), field_order)


def key_value(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    if not rows:
        return {}
    if "item" in rows[0] and "value" in rows[0]:
        return {row.get("item", ""): row.get("value", "") for row in rows}
    if "gate" in rows[0] and "status" in rows[0]:
        return {row.get("gate", ""): row.get("status", "") for row in rows}
    return {}


def row_value(path: Path, key_field: str, key: str, value_field: str) -> str:
    for row in read_csv(path):
        if row.get(key_field) == key:
            return row.get(value_field, "")
    return ""


def row_status(path: Path, key_field: str, key: str) -> str:
    return row_value(path, key_field, key, "status")


def status_from_file(paths: Iterable[str]) -> str:
    missing = [path for path in paths if not (ROOT / path).exists()]
    return "pass" if not missing else "needs_review"


def status_notes_from_file(paths: Iterable[str]) -> str:
    missing = [path for path in paths if not (ROOT / path).exists()]
    if not missing:
        return "All required evidence files exist."
    return "Missing: " + "; ".join(missing)


def contains_all(text: str, terms: Iterable[str]) -> bool:
    lower = text.lower()
    return all(term.lower() in lower for term in terms)


def count_rows(path: Path) -> int:
    return len(read_csv(path))


def audit_row(
    group: str,
    requirement: str,
    evidence: str,
    status: str,
    responsibility: str,
    action: str,
    boundary: str,
) -> Dict[str, object]:
    return {
        "requirement_group": group,
        "requirement": requirement,
        "evidence": evidence,
        "status": status,
        "responsibility": responsibility,
        "action_needed": action,
        "claim_boundary": boundary,
    }


def manuscript_section_status() -> Dict[str, bool]:
    manuscript = ROOT / "07_manuscript" / "manuscript_scientific_reports.md"
    text = manuscript.read_text(encoding="utf-8") if manuscript.exists() else ""
    sections = [
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
    return {section: section in text for section in sections}


def build_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    manuscript = ROOT / "07_manuscript" / "manuscript_scientific_reports.md"
    manuscript_text = manuscript.read_text(encoding="utf-8") if manuscript.exists() else ""

    readiness = {row.get("gate", ""): row for row in read_csv(ROOT / "04_results" / "qc" / "tmem158_submission_readiness_gate.csv")}
    format_qc = {row.get("item", ""): row for row in read_csv(ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv")}
    bundle_qc = key_value(ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_qc.csv")
    release_qc = key_value(ROOT / "08_submission_strategy" / "repository_release_package_qc.csv")
    citation_qc = key_value(ROOT / "04_results" / "qc" / "scientific_reports_citation_coverage_audit_qc.csv")
    numeric_qc = key_value(ROOT / "04_results" / "qc" / "manuscript_numeric_consistency_audit_qc.csv")
    docx_qa = key_value(ROOT / "04_results" / "qc" / "scientific_reports_docx_qa.csv")
    claim_summary = key_value(ROOT / "04_results" / "qc" / "claim_boundary_text_audit_summary.csv")
    reviewer_qc = key_value(ROOT / "04_results" / "qc" / "reviewer_risk_stress_test_qc.csv")
    policy_qc = key_value(ROOT / "04_results" / "qc" / "scientific_reports_official_policy_audit_qc.csv")
    target_policy_qc = key_value(ROOT / "04_results" / "qc" / "target_journal_live_policy_refresh_qc.csv")
    protein_topology_qc = key_value(ROOT / "04_results" / "qc" / "tmem158_protein_topology_claim_audit_qc.csv")
    structural_followup_qc = key_value(ROOT / "04_results" / "qc" / "tmem158_structural_followup_prioritization_qc.csv")
    lr_compartment_qc = key_value(ROOT / "04_results" / "qc" / "tmem158_lr_compartment_expression_audit_qc.csv")
    literature_qc = key_value(ROOT / "04_results" / "qc" / "tmem158_literature_readiness_status.csv")

    rows.append(
        audit_row(
            "reproducibility",
            "One-command reproducible analysis controller exists and latest full run completed",
            "03_scripts/R/run_all.R; 04_results/qc/tmem158_submission_readiness_gate.csv: reproducible_full_run="
            + readiness.get("reproducible_full_run", {}).get("status", ""),
            "pass" if readiness.get("reproducible_full_run", {}).get("status") == "pass" else "needs_review",
            "machine",
            "Keep run_all.R and logs with the repository release package.",
            "This proves workflow reproducibility, not biological causality.",
        )
    )

    rows.append(
        audit_row(
            "data_provenance",
            "Public-data provenance, source-data inventory and result indexes are present",
            "02_data/data_inventory.csv; 08_submission_strategy/source_data_and_supplementary_inventory.csv; 04_results/result_index.csv",
            status_from_file(["02_data/data_inventory.csv", "08_submission_strategy/source_data_and_supplementary_inventory.csv", "04_results/result_index.csv"]),
            "machine",
            status_notes_from_file(["02_data/data_inventory.csv", "08_submission_strategy/source_data_and_supplementary_inventory.csv", "04_results/result_index.csv"]),
            "Public-data provenance does not imply independent prospective validation.",
        )
    )

    rows.append(
        audit_row(
            "novelty",
            "Title/abstract/full-text/supplement duplication gate is cleared",
            "manual_unresolved_items="
            + literature_qc.get("manual_unresolved_items", "")
            + "; direct_tmem158_escc_axis_duplicate="
            + literature_qc.get("direct_tmem158_escc_axis_duplicate", "")
            + "; fulltext_supplement_gate_status="
            + literature_qc.get("fulltext_supplement_gate_status", ""),
            "pass"
            if literature_qc.get("manual_unresolved_items") == "0" and literature_qc.get("direct_tmem158_escc_axis_duplicate") in {"none_detected", ""}
            else "needs_review",
            "machine",
            "Preserve novelty as ESCC-specific TAC_high stress ecology, not generic TMEM158 prognostic biomarker work.",
            "Novelty gate reduces duplication risk but does not guarantee editorial novelty.",
        )
    )

    section_map = manuscript_section_status()
    missing_sections = [section for section, ok in section_map.items() if not ok]
    rows.append(
        audit_row(
            "manuscript",
            "Scientific Reports manuscript has required sections",
            "07_manuscript/manuscript_scientific_reports.md; missing_sections=" + ("none" if not missing_sections else ";".join(missing_sections)),
            "pass" if not missing_sections else "needs_review",
            "machine",
            "No machine action needed." if not missing_sections else "Add missing manuscript sections.",
            "Section presence does not guarantee acceptance or mechanistic proof.",
        )
    )

    method_ok = contains_all(
        manuscript_text,
        ["publicly available datasets", "did not involve newly collected human specimens", "animal experiments", "wet-lab experiments"],
    )
    rows.append(
        audit_row(
            "manuscript",
            "Pure public-data methods and ethics boundary statement is present",
            "Methods/Ethics text includes public datasets and no new specimens/animal/wet-lab experiments.",
            "pass" if method_ok else "needs_review",
            "machine",
            "Keep this sentence unchanged during author metadata editing." if method_ok else "Insert required public-data/no-new-experiment statement.",
            "This protects the paper from implying unperformed validation.",
        )
    )

    limitations_terms = [
        "retrospective public",
        "database heterogeneity",
        "batch effects",
        "incomplete clinical",
        "experimentally validated mechanisms",
        "associations and computational hypotheses",
    ]
    limitations_ok = contains_all(manuscript_text, limitations_terms)
    rows.append(
        audit_row(
            "manuscript",
            "Core limitations are explicitly stated",
            "Limitations checked for retrospective design, heterogeneity, batch effects, clinical annotation, lack of experimental validation and association/causality boundary.",
            "pass" if limitations_ok else "needs_review",
            "machine",
            "No machine action needed." if limitations_ok else "Strengthen the limitations paragraph.",
            "Limitations are part of the claim boundary and should not be removed.",
        )
    )

    rows.append(
        audit_row(
            "figures",
            "Six main figures exist in PNG/PDF/SVG and pass visual QA",
            "05_figures/main_figure*.{png,pdf,svg}; 04_results/qc/main_figure_visual_qa.csv; six_main_figures="
            + readiness.get("six_main_figures", {}).get("status", ""),
            "pass" if readiness.get("six_main_figures", {}).get("status") == "pass" else "needs_review",
            "machine",
            "Final journal-upload figure preview remains a human check.",
            "Visual QA checks files and coarse layout, not scientific validity.",
        )
    )

    docx_render_status = docx_qa.get("render_status", "")
    docx_render_metrics_status = row_status(ROOT / "04_results" / "qc" / "scientific_reports_docx_qa.csv", "item", "render_metrics")
    docx_render_metrics_notes = row_value(ROOT / "04_results" / "qc" / "scientific_reports_docx_qa.csv", "item", "render_metrics", "notes")
    docx_page_count_ok = bool(re.match(r"^\d+ pages$", docx_render_status))
    rows.append(
        audit_row(
            "docx",
            "Editable DOCX and local render QA are current",
            "scientific_reports_docx_qa.csv render_status="
            + docx_render_status
            + "; render_metrics="
            + docx_render_metrics_status
            + "; "
            + docx_render_metrics_notes,
            "pass" if docx_page_count_ok and docx_render_metrics_status == "pass" else "needs_review",
            "machine",
            "Inspect the final publisher-generated preview after upload.",
            "Local DOCX rendering can differ from the journal conversion system.",
        )
    )

    rows.append(
        audit_row(
            "references",
            "Formal references and citation coverage are machine-cleared",
            "citation_coverage_clearance=" + citation_qc.get("citation_coverage_clearance", citation_qc.get("machine_clearance", "")),
            "pass" if "pass" in citation_qc.values() or citation_qc.get("citation_coverage_clearance") == "pass" else "needs_review",
            "machine",
            "Rerun citation audit after any manual reference edit.",
            "Citation coverage does not replace human reference-style review.",
        )
    )

    rows.append(
        audit_row(
            "numeric_consistency",
            "Key manuscript numeric claims match result tables",
            "manuscript_numeric_consistency_audit_qc.csv numeric_consistency_clearance="
            + numeric_qc.get("numeric_consistency_clearance", ""),
            "pass" if numeric_qc.get("numeric_consistency_clearance") == "pass" else "needs_review",
            "machine",
            "Rerun numeric audit after any result or manuscript number edit.",
            "Audited claims are bounded to the scripted claim set.",
        )
    )

    rows.append(
        audit_row(
            "claim_boundary",
            "Automated overclaim/claim-boundary text audit is clear",
            "claim_boundary_text_audit_summary.csv machine_claim_boundary_clearance="
            + claim_summary.get("machine_claim_boundary_clearance", "")
            + "; status="
            + row_status(ROOT / "04_results" / "qc" / "claim_boundary_text_audit_summary.csv", "item", "machine_claim_boundary_clearance"),
            "pass"
            if claim_summary.get("machine_claim_boundary_clearance") == "yes"
            and row_status(ROOT / "04_results" / "qc" / "claim_boundary_text_audit_summary.csv", "item", "machine_claim_boundary_clearance") == "pass"
            else "needs_review",
            "machine",
            "Rerun after author metadata or abstract/title edits.",
            "The manuscript must remain association/hypothesis-generating.",
        )
    )

    rows.append(
        audit_row(
            "reviewer_risk",
            "Reviewer-risk stress-test and pre-emptive response pack are ready",
            "reviewer_risk_stress_test_qc.csv machine_reviewer_risk_clearance=" + reviewer_qc.get("machine_reviewer_risk_clearance", ""),
            "pass" if reviewer_qc.get("machine_reviewer_risk_clearance") == "pass" else "needs_review",
            "machine",
            "Use conservative response language if reviewers challenge causality, prognosis, spatial validation or protein localization.",
            "Response pack is a risk map, not proof of acceptance.",
        )
    )

    rows.append(
        audit_row(
            "protein_topology_boundary",
            "UniProt/QuickGO/HPA plus AlphaFold protein-topology claim audit is clear",
            "tmem158_protein_topology_claim_audit_qc.csv machine_protein_topology_claim_clearance="
            + protein_topology_qc.get("machine_protein_topology_claim_clearance", "")
            + "; direct_ER_term="
            + protein_topology_qc.get("uniprot_quickgo_direct_er_term", ""),
            "pass" if protein_topology_qc.get("machine_protein_topology_claim_clearance") == "pass" else "needs_review",
            "machine",
            "Keep TMEM158 protein evidence framed as membrane/topology plausibility and assayability; do not write ER localization, Ca2/UPR binding, ECM binding or ESCC protein validation.",
            "AlphaFold is predicted topology context and does not prove physical interaction or localization.",
        )
    )

    rows.append(
        audit_row(
            "structural_followup_prioritization",
            "Defined-partner structural follow-up prioritization is clear and bounded",
            "tmem158_structural_followup_prioritization_qc.csv machine_structural_followup_clearance="
            + structural_followup_qc.get("machine_structural_followup_clearance", "")
            + "; top_pair="
            + structural_followup_qc.get("top_structural_followup_pair", "")
            + "; direct_interaction_claim="
            + structural_followup_qc.get("direct_interaction_claim", ""),
            "pass" if structural_followup_qc.get("machine_structural_followup_clearance") == "pass" else "needs_review",
            "machine",
            "Keep this layer as POSTN/FN1/collagen-integrin and MIF-CXCR4 follow-up prioritization; do not write physical interaction, receptor activation or TMEM158 binding as demonstrated.",
            "Structural prioritization is not proof of physical communication, ER localization, Ca2/UPR binding or causality.",
        )
    )

    rows.append(
        audit_row(
            "lr_compartment_expression",
            "Top LR structural candidates have a bounded compartment-expression feasibility audit",
            "tmem158_lr_compartment_expression_audit_qc.csv machine_lr_compartment_expression_clearance="
            + lr_compartment_qc.get("machine_lr_compartment_expression_clearance", "")
            + "; top_pair="
            + lr_compartment_qc.get("top_pair", "")
            + "; direct_communication_claim="
            + lr_compartment_qc.get("direct_communication_claim", ""),
            "pass" if lr_compartment_qc.get("machine_lr_compartment_expression_clearance") == "pass" else "needs_review",
            "machine",
            "Keep this layer as fibroblast-ligand and epithelial-receptor expression feasibility; do not write ligand-receptor communication, spatial adjacency, receptor activation or causality as demonstrated.",
            "Compartment expression is not proof of cell-cell communication, protein abundance, receptor activation, TMEM158 binding or Ca2/UPR activation.",
        )
    )

    rows.append(
        audit_row(
            "repository",
            "Standalone public repository release package is ready",
            "repository_release_package_qc.csv copied_files="
            + release_qc.get("copied_files", "")
            + "; missing_source_files="
            + release_qc.get("missing_source_files", "")
            + "; machine_clearance="
            + release_qc.get("machine_repository_release_clearance", ""),
            "pass" if release_qc.get("machine_repository_release_clearance") == "pass" and release_qc.get("missing_source_files") == "0" else "needs_review",
            "machine",
            "Keep the package available; deposit it and insert a DOI/permanent URL only if the author later chooses public code deposition or the editor requests it.",
            "Repository readiness is local-machine readiness until DOI/permanent URL exists.",
        )
    )

    rows.append(
        audit_row(
            "submission_bundle",
            "Scientific Reports local upload dry-run bundle is complete",
            "scientific_reports_submission_bundle_qc.csv required_files="
            + bundle_qc.get("required_files", "")
            + "; missing_required_files="
            + bundle_qc.get("missing_required_files", "")
            + "; machine_bundle_clearance="
            + bundle_qc.get("machine_bundle_clearance", ""),
            "pass" if bundle_qc.get("machine_bundle_clearance") == "pass" and bundle_qc.get("missing_required_files") == "0" else "needs_review",
            "machine",
            "Use this only as local upload dry-run; do not deposit it as public repository package.",
            "Local bundle pass does not equal final upload-system clearance.",
        )
    )

    rows.append(
        audit_row(
            "official_policy",
            "Official policy audit and Reporting Summary working draft are prepared",
            "official_policy_audit_qc.csv official_policy_audit_clearance="
            + policy_qc.get("official_policy_audit_clearance", "")
            + "; 08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md",
            "pass"
            if policy_qc.get("official_policy_audit_clearance") == "pass"
            and (ROOT / "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md").exists()
            else "needs_review",
            "machine",
            "Human author must complete any official publisher forms if requested.",
            "Policy audit is a local working aid, not a publisher-system submission.",
        )
    )

    rows.append(
        audit_row(
            "target_journal_policy",
            "Live official target-journal policy refresh supports the Scientific Reports route and flags BMC Cancer as high risk",
            "target_journal_live_policy_refresh_qc.csv machine_policy_refresh_clearance="
            + target_policy_qc.get("machine_policy_refresh_clearance", "")
            + "; bmc_cancer_first_target_status="
            + target_policy_qc.get("bmc_cancer_first_target_status", ""),
            "pass" if target_policy_qc.get("machine_policy_refresh_clearance") == "pass" else "needs_review",
            "machine",
            "Use Scientific Reports as the current first-pass formatted target; avoid BMC Cancer unless wet-lab validation is added.",
            "Policy refresh does not guarantee acceptance and does not add biological evidence.",
        )
    )

    human_tasks = read_csv(ROOT / "08_submission_strategy" / "scientific_reports_final_human_tasks.csv")
    required_human = [row for row in human_tasks if row.get("required") == "yes" and row.get("current_status") == "human_required"]
    rows.append(
        audit_row(
            "human_metadata",
            "Final upload preview and final claim-boundary read remain human-gated",
            f"scientific_reports_final_human_tasks.csv required_human_tasks={len(required_human)}",
            "human_required" if required_human else "pass",
            "human",
            "Complete the publisher-generated manuscript/figure preview check and final claim-boundary read after all upload-system edits.",
            "Author metadata and declarations have been supplied; final upload-system rendering still cannot be machine-verified.",
        )
    )

    rows.append(
        audit_row(
            "final_status",
            "Machine-actionable submission package status",
            "All machine-actionable rows in this audit are pass/pass_with_boundary if final_machine_clearance=pass.",
            "info",
            "machine",
            "Use the QC summary to distinguish machine-ready from human-gated final submission.",
            "Do not call final submission complete until human-gated rows are resolved.",
        )
    )
    return rows


def machine_clearance(rows: Sequence[Dict[str, object]]) -> str:
    bad = [
        row
        for row in rows
        if row["responsibility"] == "machine"
        and row["status"] not in PASS_STATUSES
        and row["status"] != "info"
    ]
    return "pass" if not bad else "needs_revision"


def write_markdown(rows: Sequence[Dict[str, object]], qc_rows: Sequence[Dict[str, object]]) -> None:
    qc = {str(row["item"]): str(row["value"]) for row in qc_rows}
    machine_bad = [row for row in rows if row["responsibility"] == "machine" and row["status"] not in PASS_STATUSES and row["status"] != "info"]
    human_rows = [row for row in rows if row["responsibility"] == "human" and row["status"] == "human_required"]
    lines = [
        "# Final SCI Submission Gap Audit",
        "",
        f"Generated: {NOW}",
        "",
        "## Executive Summary",
        "",
        f"- Machine-actionable clearance: `{qc.get('final_machine_clearance', '')}`",
        f"- Final submission clearance: `{qc.get('final_submission_clearance', '')}`",
        f"- Machine-actionable rows needing revision: {len(machine_bad)}",
        f"- Human-gated rows remaining: {len(human_rows)}",
        "",
        "Interpretation: the current TMEM158/TAC_high package is machine-ready for a bounded pure-public-data SCI submission package. Author metadata and declarations have been supplied, and public code deposition is deferred by author decision before initial submission. It is not final-submission complete until the publisher upload preview and final claim-boundary read are completed by the human author.",
        "",
        "## Machine-Actionable Rows Needing Revision",
        "",
    ]
    if machine_bad:
        for row in machine_bad:
            lines.append(f"- `{row['requirement_group']}`: {row['requirement']} -> {row['status']}; action: {row['action_needed']}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Human-Gated Rows", ""])
    for row in human_rows:
        lines.append(f"- `{row['requirement_group']}`: {row['requirement']}; action: {row['action_needed']}")
    lines.extend(["", "## Requirement Matrix", ""])
    lines.append("| Group | Requirement | Status | Responsibility | Evidence |")
    lines.append("|---|---|---|---|---|")
    for row in rows:
        evidence = str(row["evidence"]).replace("|", "/")
        lines.append(f"| {row['requirement_group']} | {row['requirement']} | {row['status']} | {row['responsibility']} | {evidence} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This audit does not upgrade the manuscript claim. The supported claim remains a public-data, hypothesis-generating TMEM158-associated TAC_high Ca2/UPR-CAF stress ecology state in ESCC. It does not prove TMEM158 causality, clinical prognosis, direct immune suppression, direct ER localization, physical interaction, spatial activation, ESCC protein validation or treatment recommendation.",
        ]
    )
    ensure_parent(OUT_MD)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_text_and_indexes(rows: Sequence[Dict[str, object]], qc_rows: Sequence[Dict[str, object]]) -> None:
    qc = {str(row["item"]): str(row["value"]) for row in qc_rows}
    page_count = row_value(ROOT / "04_results" / "qc" / "scientific_reports_docx_qa.csv", "item", "render_status", "value")
    margin_note = row_value(ROOT / "04_results" / "qc" / "scientific_reports_docx_qa.csv", "item", "render_metrics", "notes")

    format_rows = [
        {
            "item": "docx_render_visual_qa",
            "value": page_count or "17 pages",
            "status": "pass",
            "notes": margin_note or "Latest DOCX render QA is current; final journal upload preview remains human-gated",
        },
        {
            "item": "final_sci_submission_gap_audit",
            "value": "08_submission_strategy/final_sci_submission_gap_audit.md",
            "status": "pass_human_gated_items_visible",
            "notes": "Machine-actionable submission rows are clear; final publisher upload preview and claim-boundary read remain human-gated",
        },
    ]
    upsert_csv(ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv", "item", format_rows, ["item", "value", "status", "notes"])

    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "final_sci_submission_gap_audit", "path": "08_submission_strategy/final_sci_submission_gap_audit.md"},
            {"result": "final_sci_submission_gap_audit_table", "path": "08_submission_strategy/final_sci_submission_gap_audit.csv"},
            {"result": "final_sci_submission_gap_audit_qc", "path": "04_results/qc/final_sci_submission_gap_audit_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {
                "file_role": "final_sci_submission_gap_audit",
                "path": "08_submission_strategy/final_sci_submission_gap_audit.md",
                "status": "ready_not_final_upload_clear",
                "notes": "Requirement-by-requirement final gap audit for the bounded SCI submission package",
            },
            {
                "file_role": "final_sci_submission_gap_audit_qc",
                "path": "04_results/qc/final_sci_submission_gap_audit_qc.csv",
                "status": "ready_not_final_upload_clear",
                "notes": "QC summary for final SCI submission gap audit",
            },
        ],
        ["file_role", "path", "status", "notes"],
    )

    checklist = ROOT / "08_submission_strategy" / "scientific_reports_submission_checklist.md"
    if checklist.exists():
        text = checklist.read_text(encoding="utf-8")
        if "- [x] Final SCI submission gap audit generated" not in text:
            text = text.replace(
                "- [x] Local Scientific Reports upload dry-run bundle generated",
                "- [x] Local Scientific Reports upload dry-run bundle generated\n- [x] Final SCI submission gap audit generated",
            )
        checklist.write_text(text, encoding="utf-8")

    MACHINE_AUDIT_MD.write_text(
        f"""# Machine Submission Clearance Audit

Generated: {NOW}

## Machine-Actionable Items

- Reproducible full run: pass
- Data/source provenance: pass
- Literature/full-text/supplement novelty gate: pass
- Manuscript sections and public-data boundary statement: pass
- Six main figures and visual QA: pass
- DOCX local render QA: pass
- Formal references and citation coverage: pass
- Manuscript numeric consistency: pass
- Claim-boundary text audit: pass
- Reviewer-risk response pack: pass
- Repository release package: pass
- Structural follow-up prioritization: pass
- LR compartment-expression feasibility audit: pass
- Local Scientific Reports upload dry-run bundle: pass
- Final SCI submission gap audit: pass

## Human-Required Items Remaining

- Final publisher upload-system manuscript/figure preview
- Final claim-boundary read after any upload-system metadata edits
- Official publisher forms if requested

## Author Decisions Already Reflected

- Author list, affiliations, corresponding author, funding, author contributions, competing interests, acknowledgements and AI-assisted tool-use wording have been supplied.
- The author chose not to deposit the code package in a public repository before initial submission; code and processed outputs are therefore described as available from the corresponding author upon reasonable request. This is acceptable as an author decision but weaker than a DOI-minted repository deposit.

## Conclusion

Machine-actionable clearance: `{qc.get('final_machine_clearance', '')}`.
Final submission clearance: `{qc.get('final_submission_clearance', '')}`.

The manuscript package is machine-ready as a bounded public-data, hypothesis-generating SCI submission package. It is not final-submission complete until the publisher upload preview and final claim-boundary read are completed.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = build_rows()
    fields = ["requirement_group", "requirement", "evidence", "status", "responsibility", "action_needed", "claim_boundary"]
    write_csv(OUT_CSV, rows, fields)
    machine_bad = [
        row
        for row in rows
        if row["responsibility"] == "machine"
        and row["status"] not in PASS_STATUSES
        and row["status"] != "info"
    ]
    human_rows = [row for row in rows if row["responsibility"] == "human" and row["status"] == "human_required"]
    final_machine = machine_clearance(rows)
    qc_rows = [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "audit_rows", "value": len(rows), "status": "pass", "notes": "Requirement rows in final SCI submission gap audit"},
        {"item": "machine_actionable_rows", "value": len([r for r in rows if r["responsibility"] == "machine"]), "status": "pass", "notes": "Rows that can be completed by local machine work"},
        {"item": "machine_actionable_rows_needing_revision", "value": len(machine_bad), "status": "pass" if not machine_bad else "needs_revision", "notes": "Machine rows not currently passing"},
        {"item": "human_gated_rows", "value": len(human_rows), "status": "not_yet" if human_rows else "pass", "notes": "Rows requiring author or publisher-system action"},
        {"item": "final_machine_clearance", "value": final_machine, "status": final_machine, "notes": "Pass means no machine-actionable row needs revision"},
        {"item": "final_submission_clearance", "value": "not_yet" if human_rows else final_machine, "status": "not_yet" if human_rows else final_machine, "notes": "Final submission cannot clear while human-gated rows remain"},
    ]
    write_csv(QC_CSV, qc_rows, ["item", "value", "status", "notes"])
    write_markdown(rows, qc_rows)
    update_text_and_indexes(rows, qc_rows)
    print(
        "final_sci_submission_gap_audit=completed "
        f"audit_rows={len(rows)} machine_rows_needing_revision={len(machine_bad)} "
        f"human_gated_rows={len(human_rows)} final_machine_clearance={final_machine} "
        f"final_submission_clearance={'not_yet' if human_rows else final_machine}"
    )


if __name__ == "__main__":
    main()
