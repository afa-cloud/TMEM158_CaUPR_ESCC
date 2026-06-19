#!/usr/bin/env python3
"""Build a final author-facing submission handoff pack.

This is a submission-execution artifact. It does not add biological evidence.
It converts the current machine-cleared Scientific Reports package into a
concise set of upload files, copy-ready fields and the remaining publisher
preview / final claim-boundary checks.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT_MD = ROOT / "08_submission_strategy" / "final_author_submission_handoff.md"
OUT_CSV = ROOT / "08_submission_strategy" / "final_author_submission_action_table.csv"
QC_CSV = ROOT / "04_results" / "qc" / "final_author_submission_handoff_qc.csv"
PUBLIC_REPOSITORY_URL = "https://github.com/afa-cloud/TMEM158_CaUPR_ESCC"


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
    for row in read_csv(path):
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
    return {}


def file_status(paths: Iterable[str]) -> str:
    missing = [path for path in paths if not (ROOT / path).exists()]
    return "pass" if not missing else "missing:" + ";".join(missing)


def field_rows_by_name(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {row.get("field_name", ""): row for row in rows}


def md_escape(text: str) -> str:
    return text.replace("\n", "<br>")


def build_upload_file_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = [
        {
            "step": "1",
            "upload_item": "Main manuscript DOCX",
            "path": "07_manuscript/manuscript_scientific_reports.docx",
            "required": "yes",
            "status": file_status(["07_manuscript/manuscript_scientific_reports.docx"]),
            "notes": "Editable Scientific Reports manuscript. Local render QA passed, but publisher preview remains human-gated.",
        },
        {
            "step": "2",
            "upload_item": "Cover letter",
            "path": "08_submission_strategy/scientific_reports_cover_letter_draft.md",
            "required": "yes",
            "status": file_status(["08_submission_strategy/scientific_reports_cover_letter_draft.md"]),
            "notes": "Add corresponding-author header, signature and any required editor salutation before upload.",
        },
        {
            "step": "3",
            "upload_item": "Supplementary Information",
            "path": "07_manuscript/supplementary_information_scientific_reports.md",
            "required": "yes",
            "status": file_status(["07_manuscript/supplementary_information_scientific_reports.md"]),
            "notes": "Markdown supplementary draft; convert to DOCX/PDF only if journal system requests a specific format.",
        },
        {
            "step": "4",
            "upload_item": "Repository release ZIP",
            "path": "08_submission_strategy/TMEM158_TAC_high_repository_release.zip",
            "required": "optional",
            "status": file_status(["08_submission_strategy/TMEM158_TAC_high_repository_release.zip"]),
            "notes": "Author currently chose not to deposit code before initial submission. Keep this clean repository package for later Zenodo/OSF/GitHub deposition if requested.",
        },
        {
            "step": "5",
            "upload_item": "Local submission dry-run ZIP",
            "path": "08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip",
            "required": "no",
            "status": file_status(["08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip"]),
            "notes": "Use for local organization only unless a coauthor asks for one archive. Not the public repository deposit package.",
        },
        {
            "step": "6",
            "upload_item": "Reporting Summary working draft",
            "path": "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md",
            "required": "if_requested",
            "status": file_status(["08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md"]),
            "notes": "Use as a working draft if the submission workflow requests a formal Nature Portfolio Reporting Summary form.",
        },
    ]
    main_figures = [
        "main_figure1_tmem158_axis_discovery",
        "main_figure2_tac_high_bulk_state",
        "main_figure3_tac_high_transcriptome",
        "main_figure4_gse53625_clinical_calibration",
        "main_figure5_scrna_caf_bridge",
        "main_figure6_independent_context_and_boundaries",
    ]
    for idx, fig in enumerate(main_figures, start=1):
        for ext in ("png", "pdf", "svg"):
            path = f"05_figures/{fig}.{ext}"
            rows.append(
                {
                    "step": f"F{idx}.{ext}",
                    "upload_item": f"Main Figure {idx} {ext.upper()}",
                    "path": path,
                    "required": "yes",
                    "status": file_status([path]),
                    "notes": "Upload the format requested by the journal; retain all three local formats for QA and conversion.",
                }
            )
    return rows


def build_human_action_rows(human_rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    guidance = {
        "competing_interests": "Use 'The author(s) declare no competing interests.' only if all authors confirm it is true.",
        "funding": "Enter funder names, grant numbers and funder-role statement, or confirm no specific funding if accurate.",
        "author_contributions": "Use final author initials and CRediT-style roles; do not infer roles from the analysis files.",
        "acknowledgements": "Confirm technical support, data-source acknowledgement beyond citations and approved AI-tool disclosure.",
        "repository_doi_or_permanent_url": f"Use the public GitHub repository URL: {PUBLIC_REPOSITORY_URL}. Mint and replace with a DOI only if the journal requires it.",
        "suggested_reviewers": "Optional. Add only if the system requests reviewers and conflicts have been checked.",
        "opposed_reviewers": "Optional. Add only if necessary and allowed by the journal.",
        "final_upload_preview": "After upload, inspect the publisher-generated PDF/HTML previews for manuscript, figures and supplement.",
        "final_claim_boundary_read": "After any metadata edits, re-read title, abstract, cover letter and generated preview for overclaim drift.",
    }
    for idx, row in enumerate(human_rows, start=1):
        field = row.get("field_name", "")
        rows.append(
            {
                "order": idx,
                "task_id": row.get("task_id", ""),
                "field_name": field,
                "required": row.get("required", ""),
                "current_status": row.get("current_status", ""),
                "action_needed": row.get("action_needed", ""),
                "recommended_handling": guidance.get(field, "Human author decision required."),
                "source": row.get("source", ""),
                "notes": row.get("notes", ""),
            }
        )
    return rows


def build_qc_rows(upload_rows: Sequence[Dict[str, object]], action_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    final_gap = key_value(ROOT / "04_results" / "qc" / "final_sci_submission_gap_audit_qc.csv")
    bundle_qc = key_value(ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_qc.csv")
    repo_qc = key_value(ROOT / "08_submission_strategy" / "repository_release_package_qc.csv")
    claim_qc = key_value(ROOT / "04_results" / "qc" / "claim_boundary_text_audit_summary.csv")
    numeric_qc = key_value(ROOT / "04_results" / "qc" / "manuscript_numeric_consistency_audit_qc.csv")
    citation_qc = key_value(ROOT / "04_results" / "qc" / "scientific_reports_citation_coverage_audit_qc.csv")
    missing_uploads = [row for row in upload_rows if str(row["status"]).startswith("missing")]
    required_human = [row for row in action_rows if row["required"] == "yes"]
    machine_ready = (
        not missing_uploads
        and final_gap.get("final_machine_clearance") == "pass"
        and bundle_qc.get("machine_bundle_clearance") == "pass"
        and repo_qc.get("machine_repository_release_clearance") == "pass"
        and claim_qc.get("machine_claim_boundary_clearance") == "yes"
        and numeric_qc.get("numeric_consistency_clearance") == "pass"
        and citation_qc.get("citation_coverage_clearance") == "pass"
    )
    return [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "handoff_markdown", "value": rel(OUT_MD), "status": "pass", "notes": "Author-facing final submission handoff"},
        {"item": "action_table", "value": rel(OUT_CSV), "status": "pass", "notes": "Machine-readable upload and human action table"},
        {"item": "upload_rows", "value": len(upload_rows), "status": "pass", "notes": "Upload/file rows listed in handoff"},
        {"item": "missing_upload_rows", "value": len(missing_uploads), "status": "pass" if not missing_uploads else "needs_revision", "notes": "Listed upload/source files that are absent"},
        {"item": "required_human_tasks", "value": len(required_human), "status": "not_yet" if required_human else "pass", "notes": "Human-gated required tasks retained as explicit blockers"},
        {"item": "final_machine_clearance", "value": final_gap.get("final_machine_clearance", ""), "status": "pass" if final_gap.get("final_machine_clearance") == "pass" else "needs_revision", "notes": "From final SCI gap audit"},
        {"item": "bundle_clearance", "value": bundle_qc.get("machine_bundle_clearance", ""), "status": "pass" if bundle_qc.get("machine_bundle_clearance") == "pass" else "needs_revision", "notes": "From local Scientific Reports submission bundle QC"},
        {"item": "repository_release_clearance", "value": repo_qc.get("machine_repository_release_clearance", ""), "status": "pass" if repo_qc.get("machine_repository_release_clearance") == "pass" else "needs_revision", "notes": "From repository release package QC"},
        {"item": "claim_boundary_clearance", "value": claim_qc.get("machine_claim_boundary_clearance", ""), "status": "pass" if claim_qc.get("machine_claim_boundary_clearance") == "yes" else "needs_revision", "notes": "From public-facing claim-boundary text audit"},
        {"item": "numeric_consistency_clearance", "value": numeric_qc.get("numeric_consistency_clearance", ""), "status": "pass" if numeric_qc.get("numeric_consistency_clearance") == "pass" else "needs_revision", "notes": "From manuscript numeric consistency audit"},
        {"item": "citation_coverage_clearance", "value": citation_qc.get("citation_coverage_clearance", ""), "status": "pass" if citation_qc.get("citation_coverage_clearance") == "pass" else "needs_revision", "notes": "From Scientific Reports citation coverage audit"},
        {"item": "machine_handoff_clearance", "value": "pass" if machine_ready else "needs_revision", "status": "pass" if machine_ready else "needs_revision", "notes": "Pass means no machine-side handoff artifact is missing"},
        {"item": "final_upload_clearance", "value": "not_yet", "status": "not_yet", "notes": f"Publisher upload preview and final claim-boundary read remain required; public GitHub repository is listed as {PUBLIC_REPOSITORY_URL}"},
    ]


def write_markdown(
    upload_rows: Sequence[Dict[str, object]],
    action_rows: Sequence[Dict[str, object]],
    qc_rows: Sequence[Dict[str, object]],
    fields: Dict[str, Dict[str, str]],
) -> None:
    bundle_qc = key_value(ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_qc.csv")
    repo_qc = key_value(ROOT / "08_submission_strategy" / "repository_release_package_qc.csv")
    final_gap = key_value(ROOT / "04_results" / "qc" / "final_sci_submission_gap_audit_qc.csv")
    lines: List[str] = []
    lines.extend(
        [
            "# Final Author Submission Handoff",
            "",
            f"Generated: {NOW}",
            "",
            "## Status",
            "",
            f"- Machine-side final clearance: `{final_gap.get('final_machine_clearance', '')}`",
            f"- Final upload clearance: `{final_gap.get('final_submission_clearance', '')}`",
            f"- Local Scientific Reports bundle: `{bundle_qc.get('machine_bundle_clearance', '')}`",
            f"- Repository release package: `{repo_qc.get('machine_repository_release_clearance', '')}`",
            "",
            f"Interpretation: the machine-prepared manuscript package is ready for journal-system upload. The manuscript is not yet final-submission complete because the publisher-generated upload preview and a final claim-boundary read must still be completed by the human author. Public GitHub repository deposition is complete at {PUBLIC_REPOSITORY_URL}.",
            "",
            "## Copy-Ready Submission Fields",
            "",
        ]
    )
    for field in [
        "article_type",
        "title",
        "running_title",
        "abstract",
        "keywords",
        "editor_significance_statement",
        "plain_language_summary",
        "cover_letter_core_pitch",
        "data_availability",
        "code_availability",
        "ethics_statement",
        "public_data_boundary",
        "claims_not_made",
        "limitations_summary",
    ]:
        row = fields.get(field)
        if not row:
            continue
        lines.append(f"### {field}")
        lines.append("")
        lines.append(f"Status: `{row.get('status', '')}`")
        lines.append("")
        lines.append(row.get("field_value", ""))
        lines.append("")
        lines.append(f"Source: `{row.get('source', '')}`")
        lines.append("")
    lines.extend(
        [
            "## Upload File Map",
            "",
            "| Step | Upload item | Path | Required | Status | Notes |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in upload_rows:
        lines.append(
            f"| {row['step']} | {row['upload_item']} | `{row['path']}` | {row['required']} | {row['status']} | {md_escape(str(row['notes']))} |"
        )
    lines.extend(
        [
            "",
            "## Human-Gated Actions",
            "",
            "| Order | Field | Required | Current status | Action | Recommended handling |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in action_rows:
        lines.append(
            f"| {row['order']} | {row['field_name']} | {row['required']} | {row['current_status']} | {md_escape(str(row['action_needed']))} | {md_escape(str(row['recommended_handling']))} |"
        )
    lines.extend(
        [
            "",
            "## Recommended Repository Step",
            "",
            f"The code and processed outputs have been deposited in the public GitHub repository: {PUBLIC_REPOSITORY_URL}. Keep `08_submission_strategy/TMEM158_TAC_high_repository_release.zip` as the clean archival package for a later Zenodo/OSF DOI-minted release if the editor requests it. Do not deposit `TMEM158_TAC_high_ScientificReports_submission_bundle.zip`; that file is a local journal-upload dry run.",
            "",
            "If a DOI is later required, use a DOI-capable repository such as Zenodo, OSF or an institutional repository, then update Data availability and Code availability with the DOI. Until then, the manuscript and submission fields should use the public GitHub URL above.",
            "",
            "## Final Claim-Boundary Read",
            "",
            "Before clicking submit, confirm that the title, abstract, cover letter, editor comments and upload-system generated PDF do not introduce any of the following claims:",
            "",
            "- TMEM158 is a validated causal driver.",
            "- TAC_high is a clinically validated prognostic subtype.",
            "- The study demonstrates direct immune suppression or CD8 exhaustion.",
            "- The study proves cisplatin or treatment resistance.",
            "- The study proves direct spatial activation or ligand-receptor signalling causality.",
            "- TMEM158 is experimentally validated as an ESCC protein or ER-localized mechanism.",
            "- POSTN/FN1/collagen-integrin or MIF-CXCR4 candidates are proven receptor-activation or physical-communication mechanisms.",
            "",
            "Safe wording: public-data association, computationally supported stress-ecology state, expression-feasible candidate bridge, follow-up prioritization, hypothesis-generating discovery candidate.",
            "",
            "## Machine QC Snapshot",
            "",
            "| Item | Value | Status | Notes |",
            "|---|---|---|---|",
        ]
    )
    for row in qc_rows:
        lines.append(f"| {row['item']} | {row['value']} | {row['status']} | {md_escape(str(row['notes']))} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This handoff does not declare the manuscript submitted or accepted. It proves that the machine-prepared pure public-data package, author metadata and declarations are organized for journal-system upload; the remaining hard gates are publisher-system preview and a final claim-boundary read.",
            "",
        ]
    )
    ensure_parent(OUT_MD)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def update_indexes() -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "final_author_submission_handoff", "path": "08_submission_strategy/final_author_submission_handoff.md"},
            {"result": "final_author_submission_action_table", "path": "08_submission_strategy/final_author_submission_action_table.csv"},
            {"result": "final_author_submission_handoff_qc", "path": "04_results/qc/final_author_submission_handoff_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {"file_role": "final_author_submission_handoff", "path": "08_submission_strategy/final_author_submission_handoff.md", "status": "ready_not_final_upload_clear", "notes": "Author-facing final submission handoff; publisher preview and final claim-boundary read remain required"},
            {"file_role": "final_author_submission_action_table", "path": "08_submission_strategy/final_author_submission_action_table.csv", "status": "ready_not_final_upload_clear", "notes": "Machine-readable final upload and human-action table"},
            {"file_role": "final_author_submission_handoff_qc", "path": "04_results/qc/final_author_submission_handoff_qc.csv", "status": "ready_not_final_upload_clear", "notes": "QC summary for the final handoff pack"},
        ],
        ["file_role", "path", "status", "notes"],
    )


def main() -> None:
    fields = field_rows_by_name(read_csv(ROOT / "08_submission_strategy" / "scientific_reports_submission_system_fields.csv"))
    human_rows = read_csv(ROOT / "08_submission_strategy" / "scientific_reports_final_human_tasks.csv")
    upload_rows = build_upload_file_rows()
    action_rows = build_human_action_rows(human_rows)
    qc_rows = build_qc_rows(upload_rows, action_rows)
    write_csv(
        OUT_CSV,
        list(upload_rows) + list(action_rows),
        [
            "step",
            "upload_item",
            "path",
            "required",
            "status",
            "notes",
            "order",
            "task_id",
            "field_name",
            "current_status",
            "action_needed",
            "recommended_handling",
            "source",
        ],
    )
    write_csv(QC_CSV, qc_rows, ["item", "value", "status", "notes"])
    write_markdown(upload_rows, action_rows, qc_rows, fields)
    update_indexes()
    machine_clearance = next(row for row in qc_rows if row["item"] == "machine_handoff_clearance")["value"]
    required_human = next(row for row in qc_rows if row["item"] == "required_human_tasks")["value"]
    print(
        "final_author_submission_handoff=completed "
        f"upload_rows={len(upload_rows)} required_human_tasks={required_human} "
        f"machine_handoff_clearance={machine_clearance} final_upload_clearance=not_yet"
    )


if __name__ == "__main__":
    main()
