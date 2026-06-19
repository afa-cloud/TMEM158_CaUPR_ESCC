#!/usr/bin/env python3
"""Build a reviewer-risk stress test and pre-emptive response pack.

This is a submission-readiness artifact, not a new biological analysis. It
maps likely reviewer objections to current result files, safe response wording
and explicit claims to avoid.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


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


def file_status(paths: Sequence[str]) -> str:
    missing = [path for path in paths if not (ROOT / path).exists()]
    return "ready" if not missing else "missing:" + ";".join(missing)


RISK_ITEMS: List[Dict[str, object]] = [
    {
        "risk_id": "R01_novelty_duplication",
        "severity": "high",
        "reviewer_objection": "TMEM158/ESCC or Ca2-UPR-CAF signatures may already be reported.",
        "evidence_files": [
            "04_results/qc/tmem158_literature_readiness_status.csv",
            "01_literature/tmem158_fulltext_supplement_review_summary.csv",
            "08_submission_strategy/reviewer_risk_checklist.md",
        ],
        "defensible_position": "Novelty is framed as an ESCC-specific, rule-defined TAC_high Ca2/UPR-CAF ecology, not generic TMEM158 biomarker biology.",
        "claim_to_avoid": "No claim that TMEM158 is globally novel in cancer or that no related TMEM158 literature exists.",
        "short_response": "We performed a VM-routed title/abstract, PMC full-text, local full-text and supplementary/context gate; no direct TMEM158-ESCC TAC_high/Ca2/UPR/CAF duplicate remains unresolved.",
    },
    {
        "risk_id": "R02_public_data_only",
        "severity": "high",
        "reviewer_objection": "The study lacks wet-lab validation.",
        "evidence_files": [
            "07_manuscript/manuscript_scientific_reports.md",
            "08_submission_strategy/claim_boundary_text_audit.md",
            "04_results/qc/claim_boundary_text_audit_summary.csv",
        ],
        "defensible_position": "The manuscript is submitted as a public-data biological discovery and hypothesis-generating study.",
        "claim_to_avoid": "No wet-lab validation, treatment recommendation, clinical implementation or causal mechanism claim.",
        "short_response": "We explicitly state that only public datasets were used and that all findings are associations requiring experimental validation.",
    },
    {
        "risk_id": "R03_tmem158_causality",
        "severity": "high",
        "reviewer_objection": "The analysis does not prove TMEM158 causally drives Ca2/UPR signalling.",
        "evidence_files": [
            "04_results/qc/claim_boundary_text_audit_summary.csv",
            "04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv",
            "07_manuscript/manuscript_scientific_reports.md",
        ],
        "defensible_position": "TMEM158 is a lead computational entry point into a broader state, not a validated driver.",
        "claim_to_avoid": "Do not write that TMEM158 drives, regulates or causes Ca2/UPR-CAF ecology.",
        "short_response": "The wording deliberately uses entry point, association and state-marker language, and multi-omics data argue against a simple genomic driver explanation.",
    },
    {
        "risk_id": "R04_prognosis_negative",
        "severity": "high",
        "reviewer_objection": "Survival analysis is negative, so the paper is not a prognostic biomarker study.",
        "evidence_files": [
            "04_results/survival/tmem158_ecology_state_survival.csv",
            "04_results/survival/tmem158_gse53625_survival_cox.csv",
            "04_results/qc/tmem158_submission_readiness_gate.csv",
        ],
        "defensible_position": "The manuscript is a stress-ecology discovery study; OS-negative results are retained as boundaries.",
        "claim_to_avoid": "No prognostic biomarker, clinical subtype or survival predictor framing.",
        "short_response": "Both TCGA and GSE53625 OS analyses are reported as negative; they calibrate the claim away from prognosis and toward biology-state discovery.",
    },
    {
        "risk_id": "R05_caf_composition",
        "severity": "high",
        "reviewer_objection": "TAC_high may simply reflect CAF abundance or stromal contamination.",
        "evidence_files": [
            "04_results/validation/tmem158_stromal_adjusted_score_meta.csv",
            "04_results/transcriptome/tmem158_stromal_adjusted_meta_differential_genes.csv",
            "04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv",
            "05_figures/main_figure3_tac_high_transcriptome.png",
        ],
        "defensible_position": "The CAF component is part of the ecological state, and CAF-adjusted models separate stromal localization from residual stress transcription.",
        "claim_to_avoid": "No tumour-cell-intrinsic proof or CAF-independent proteostasis/efflux proof.",
        "short_response": "We added continuous CAF-adjusted score and transcriptome models; they retain residual MYC/OXPHOS/NFE2L2/translation programmes while preventing overclaiming of CAF-independent score effects.",
    },
    {
        "risk_id": "R06_score_defined_state",
        "severity": "medium",
        "reviewer_objection": "TAC_high is manually defined and could be arbitrary.",
        "evidence_files": [
            "04_results/validation/tmem158_rule_ecology_subtype_reproducibility.csv",
            "04_results/validation/tmem158_tac_high_permutation_summary.csv",
            "04_results/validation/tmem158_tac_high_component_specificity_meta.csv",
            "05_figures/main_figure2_tac_high_bulk_state.png",
        ],
        "defensible_position": "TAC_high is transparent, rule-defined, reproducible across cohorts and stress-tested by permutation and component contrasts.",
        "claim_to_avoid": "No claim that TAC_high is a clinically validated molecular subtype.",
        "short_response": "The state appears in all four bulk cohorts and random-label permutation supports specificity for the strongest transport/efflux readout.",
    },
    {
        "risk_id": "R07_gse53625_targeted_reannotation",
        "severity": "medium",
        "reviewer_objection": "GSE53625 is not a full-transcriptome validation because targeted reannotation was required.",
        "evidence_files": [
            "04_results/qc/tmem158_gse53625_probe_mapping_status.csv",
            "04_results/validation/tmem158_gse53625_signature_coverage.csv",
            "04_results/validation/tmem158_gse53625_paired_tumor_normal_tests.csv",
            "04_results/validation/tmem158_gse53625_tac_state_contrasts.csv",
        ],
        "defensible_position": "GSE53625 is an external clinical calibration layer with 179 paired samples and explicit coverage boundaries.",
        "claim_to_avoid": "No full-transcriptome validation or prognostic validation claim.",
        "short_response": "We recovered 64/67 requested genes and report missing ORAI1/PDPN/TALDO1 coverage; the cohort is used only for clinical calibration.",
    },
    {
        "risk_id": "R08_single_cell_causality",
        "severity": "high",
        "reviewer_objection": "Single-cell localization and ligand-receptor scoring do not prove cell-cell signalling.",
        "evidence_files": [
            "04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_tests.csv",
            "04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_tests.csv",
            "04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_tests.csv",
            "08_submission_strategy/tmem158_lr_compartment_expression_audit.csv",
            "04_results/qc/tmem158_lr_compartment_expression_audit_qc.csv",
            "05_figures/main_figure5_scrna_caf_bridge.png",
        ],
        "defensible_position": "Single-cell data support fibroblast/CAF localization and expression-feasible candidate bridges only.",
        "claim_to_avoid": "No CellChat-level proof, spatial adjacency, receptor activation, physical communication or causal signalling claim.",
        "short_response": "The text calls POSTN/FN1-integrin and MIF-CXCR4 expression-feasible candidate bridges and explicitly avoids ligand-receptor causality, receptor activation and physical communication claims.",
    },
    {
        "risk_id": "R09_gse221561_partial_recovery",
        "severity": "medium",
        "reviewer_objection": "Independent single-cell validation is partial and small.",
        "evidence_files": [
            "04_results/gse221561/tmem158_gse221561_tac_context_status.csv",
            "04_results/gse221561/tmem158_gse221561_tac_compartment_paired_tests.csv",
            "04_results/gse221561/tmem158_gse221561_tac_target_gene_coverage.csv",
        ],
        "defensible_position": "GSE221561 is an independent localization support layer, not definitive validation.",
        "claim_to_avoid": "No definitive therapy-response or bridge-causality conclusion from GSE221561.",
        "short_response": "We report 7/11 raw library recovery, 124/124 target-gene coverage and six matched tumour libraries as a bounded independent context layer.",
    },
    {
        "risk_id": "R10_spatial_context_boundary",
        "severity": "high",
        "reviewer_objection": "Public spatial source data do not directly validate TAC_high spatial activation.",
        "evidence_files": [
            "04_results/spatial_progression/tmem158_spatial_progression_context_status.csv",
            "04_results/spatial_progression/tmem158_spatial_progression_stage_tests.csv",
            "05_figures/main_figure6_independent_context_and_boundaries.png",
        ],
        "defensible_position": "Spatial source data provide fibroblast-rich tissue-context calibration only.",
        "claim_to_avoid": "No direct spatial validation of TMEM158, TAC_high, Ca2/UPR or ligand-receptor proximity.",
        "short_response": "The public source workbook lacks complete WTA expression; therefore we use DSP fibroblast and alpha-SMA trends only as tissue-context evidence.",
    },
    {
        "risk_id": "R11_immune_suppression_boundary",
        "severity": "medium",
        "reviewer_objection": "The title/history mentions immune suppression, but single-cell data do not support T-cell exhaustion.",
        "evidence_files": [
            "04_results/immune/tmem158_scrna_rule_state_immune_tests.csv",
            "08_submission_strategy/claim_boundary_text_audit.md",
        ],
        "defensible_position": "The final TMEM158 story is CAF/stress ecology, not direct immune suppression.",
        "claim_to_avoid": "No CD8 exhaustion, Treg or suppressive myeloid mechanism claim.",
        "short_response": "GSE160269 immune pseudo-bulk tests are retained as negative boundaries and the manuscript avoids immune-suppression claims.",
    },
    {
        "risk_id": "R12_drug_resistance_boundary",
        "severity": "high",
        "reviewer_objection": "Drug-efflux or proteostasis signals may be overread as cisplatin resistance.",
        "evidence_files": [
            "04_results/validation/tmem158_tac_high_permutation_summary.csv",
            "04_results/validation/tmem158_gse53625_tac_state_contrasts.csv",
            "08_submission_strategy/claim_boundary_text_audit.md",
        ],
        "defensible_position": "Transport/proteostasis signals are transcriptional readouts and hypothesis-generating.",
        "claim_to_avoid": "No cisplatin resistance, therapy response or treatment recommendation claim.",
        "short_response": "The text restricts drug-efflux to a bounded transcriptional readout and explicitly states that public data do not establish therapy resistance.",
    },
    {
        "risk_id": "R13_batch_and_platform",
        "severity": "medium",
        "reviewer_objection": "Multiple public platforms may introduce batch effects and heterogeneity.",
        "evidence_files": [
            "07_manuscript/manuscript_scientific_reports.md",
            "08_submission_strategy/source_data_and_supplementary_inventory.csv",
            "04_results/qc/submission_archive_qc.csv",
        ],
        "defensible_position": "The study uses within-cohort scoring, cohort-level statistics and explicit cross-platform boundaries.",
        "claim_to_avoid": "No claim of uniform direction across every platform.",
        "short_response": "The manuscript emphasizes cohort-specific scoring, signed meta-analysis and heterogeneous Ca2-direction boundaries.",
    },
    {
        "risk_id": "R14_data_code_availability",
        "severity": "medium",
        "reviewer_objection": "A pure bioinformatics paper must provide reproducible code, source data and traceability.",
        "evidence_files": [
            "03_scripts/R/run_all.R",
            "08_submission_strategy/source_data_and_supplementary_inventory.csv",
            "08_submission_strategy/repository_deposit_manifest.csv",
            "08_submission_strategy/scientific_reports_submission_bundle_qc.csv",
        ],
        "defensible_position": "Code, source-data inventory, repository manifest, checksums and a local upload bundle are prepared.",
        "claim_to_avoid": "Do not say final DOI is available before repository deposition.",
        "short_response": "The project includes run_all.R, source-data inventory, repository manifest/checksums and a machine-clear submission bundle; DOI remains human-gated.",
    },
    {
        "risk_id": "R15_final_upload_preview",
        "severity": "medium",
        "reviewer_objection": "The submission package is not final until the publisher-generated upload preview and final claim-boundary read are completed.",
        "evidence_files": [
            "08_submission_strategy/human_submission_metadata_template.md",
            "08_submission_strategy/scientific_reports_submission_bundle_qc.csv",
            "04_results/qc/tmem158_submission_readiness_gate.csv",
        ],
        "defensible_position": "Machine-actionable layers are complete; author metadata and declarations are supplied; final upload preview remains human-gated.",
        "claim_to_avoid": "No claim of final journal upload clearance until publisher preview and final claim-boundary read are complete.",
        "short_response": "The readiness gate intentionally remains not-yet-final because publisher upload preview and final claim-boundary read require human confirmation; public code deposition is deferred by author decision before initial submission.",
    },
    {
        "risk_id": "R16_alphafold_topology_boundary",
        "severity": "medium",
        "reviewer_objection": "AlphaFold predicted topology may be overinterpreted as ER localization or physical interaction evidence.",
        "evidence_files": [
            "04_results/structure/tmem158_alphafold_model_summary.csv",
            "04_results/structure/tmem158_alphafold_topology_segments.csv",
            "04_results/qc/tmem158_alphafold_topology_context_status.csv",
            "07_manuscript/tmem158_alphafold_topology_context_update.md",
        ],
        "defensible_position": "AlphaFold/UniProt provide predicted membrane-topology rationale only; the global model confidence is moderate/low and TM2 is lower-confidence.",
        "claim_to_avoid": "No ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC protein validation claim.",
        "short_response": "We report the predicted model as structural plausibility for follow-up localization and interaction experiments, and explicitly state that it does not demonstrate localization, binding, signalling or ESCC protein validation.",
    },
]


def build_matrix() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for item in RISK_ITEMS:
        paths = item["evidence_files"]
        status = file_status(paths)  # type: ignore[arg-type]
        rows.append(
            {
                "risk_id": item["risk_id"],
                "severity": item["severity"],
                "reviewer_objection": item["reviewer_objection"],
                "evidence_files": ";".join(paths),  # type: ignore[arg-type]
                "evidence_status": status,
                "defensible_position": item["defensible_position"],
                "claim_to_avoid": item["claim_to_avoid"],
                "short_response": item["short_response"],
            }
        )
    return rows


def write_response_pack(rows: Sequence[Dict[str, object]]) -> None:
    missing = [row for row in rows if str(row["evidence_status"]).startswith("missing:")]
    high = [row for row in rows if row["severity"] == "high"]
    lines: List[str] = [
        "# Reviewer Pre-emptive Response Pack",
        "",
        f"Generated: {NOW}",
        "",
        "## Purpose",
        "",
        "This document converts the current TMEM158/TAC_high public-data evidence into reviewer-facing response points. It is not a rebuttal to actual reviews and does not add new biological claims.",
        "",
        "## Overall Positioning",
        "",
        "The manuscript should be defended as a pure public-data, hypothesis-generating discovery of a TMEM158-associated TAC_high Ca2/UPR-CAF stress ecology state in ESCC. It should not be defended as a validated TMEM158 causal mechanism, prognostic model, immune-suppression mechanism, spatially validated programme or drug-resistance paper.",
        "",
        "## Machine QC",
        "",
        f"- Reviewer-risk rows: {len(rows)}",
        f"- High-severity rows: {len(high)}",
        f"- Rows with missing evidence files: {len(missing)}",
        "",
        "## Fast Editorial Answer",
        "",
        "This study is suitable as a public-data biological discovery manuscript because it combines axis-first candidate selection, multi-cohort rule-defined state reproducibility, whole-transcriptome validation, CAF-adjusted stress testing, targeted clinical calibration, independent single-cell localization, candidate CAF-to-epithelial bridge analysis, public spatial source-data context, formal literature gating, claim-boundary auditing and a machine-clear submission bundle. The manuscript also keeps negative survival, immune, drug-resistance, spatial and causality boundaries visible.",
        "",
        "## High-Risk Reviewer Questions",
        "",
    ]
    for row in high:
        lines.extend(
            [
                f"### {row['risk_id']}",
                "",
                f"**Likely objection:** {row['reviewer_objection']}",
                "",
                f"**Defensible position:** {row['defensible_position']}",
                "",
                f"**Short response:** {row['short_response']}",
                "",
                f"**Evidence files:** `{row['evidence_files']}`",
                "",
                f"**Claim to avoid:** {row['claim_to_avoid']}",
                "",
            ]
        )
    lines.extend(["## Full Risk Matrix", ""])
    for row in rows:
        lines.extend(
            [
                f"- **{row['risk_id']}** ({row['severity']}; {row['evidence_status']}): {row['short_response']} Avoid: {row['claim_to_avoid']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Remaining Human-Gated Items",
            "",
            "- Author names and affiliations.",
            "- Corresponding author contact information.",
            "- Author contributions.",
            "- Funding, acknowledgements and competing interests.",
            "- Repository DOI or permanent URL.",
            "- Final manuscript and figure preview inside the journal upload system.",
            "",
        ]
    )
    out = ROOT / "08_submission_strategy" / "reviewer_preemptive_response_pack.md"
    ensure_parent(out)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_editorial_triage(rows: Sequence[Dict[str, object]]) -> None:
    missing = [row for row in rows if str(row["evidence_status"]).startswith("missing:")]
    high_missing = [row for row in missing if row["severity"] == "high"]
    machine_clearance = "pass" if not high_missing and not missing else "pass_with_missing_optional_context" if not high_missing else "needs_revision"
    lines = [
        "# Editorial Triage Risk Audit",
        "",
        f"Generated: {NOW}",
        "",
        "## Machine Triage",
        "",
        f"- Risk rows: {len(rows)}",
        f"- Missing evidence rows: {len(missing)}",
        f"- High-severity missing evidence rows: {len(high_missing)}",
        f"- Machine reviewer-risk clearance: `{machine_clearance}`",
        "",
        "## Recommended Submission Position",
        "",
        "Submit as a public-data, association-based ESCC stress-ecology discovery manuscript. The strongest line is the reproducible TAC_high Ca2/UPR-CAF ecology with CAF-adjusted residual stress-state transcription and independent single-cell fibroblast localization. The weakest lines are prognosis, causal direction, direct immune suppression, drug resistance and direct spatial validation; these should remain boundaries rather than claims.",
        "",
    ]
    if missing:
        lines.append("## Missing Evidence Rows")
        lines.append("")
        for row in missing:
            lines.append(f"- `{row['risk_id']}`: {row['evidence_status']}")
        lines.append("")
    out = ROOT / "08_submission_strategy" / "editorial_triage_risk_audit.md"
    out.write_text("\n".join(lines), encoding="utf-8")


def write_qc(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    missing = [row for row in rows if str(row["evidence_status"]).startswith("missing:")]
    high_missing = [row for row in missing if row["severity"] == "high"]
    qc_rows = [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "reviewer_risk_rows", "value": len(rows), "status": "pass", "notes": "Total pre-emptive reviewer-risk rows"},
        {"item": "high_severity_rows", "value": len([row for row in rows if row["severity"] == "high"]), "status": "pass", "notes": "High-severity objections mapped"},
        {"item": "missing_evidence_rows", "value": len(missing), "status": "pass" if not missing else "needs_review", "notes": "Rows with missing evidence files"},
        {"item": "high_severity_missing_evidence_rows", "value": len(high_missing), "status": "pass" if not high_missing else "needs_revision", "notes": "High-severity rows lacking evidence"},
        {"item": "machine_reviewer_risk_clearance", "value": "pass" if not high_missing else "needs_revision", "status": "pass" if not high_missing else "needs_revision", "notes": "Pass requires no high-severity objection without evidence"},
        {"item": "final_upload_clearance", "value": "not_yet", "status": "not_yet", "notes": "Publisher upload preview and final claim-boundary read remain human-gated"},
    ]
    write_csv(ROOT / "04_results" / "qc" / "reviewer_risk_stress_test_qc.csv", qc_rows, ["item", "value", "status", "notes"])
    return qc_rows


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


def update_indexes(qc_rows: Sequence[Dict[str, object]]) -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "reviewer_risk_stress_test_matrix", "path": "08_submission_strategy/reviewer_risk_stress_test_matrix.csv"},
            {"result": "reviewer_preemptive_response_pack", "path": "08_submission_strategy/reviewer_preemptive_response_pack.md"},
            {"result": "editorial_triage_risk_audit", "path": "08_submission_strategy/editorial_triage_risk_audit.md"},
            {"result": "reviewer_risk_stress_test_qc", "path": "04_results/qc/reviewer_risk_stress_test_qc.csv"},
            {"result": "reviewer_response_evidence_map", "path": "06_tables/reviewer_response_evidence_map.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {"file_role": "reviewer_risk_stress_test_matrix", "path": "08_submission_strategy/reviewer_risk_stress_test_matrix.csv", "status": "ready", "notes": "Pre-emptive reviewer objection-to-evidence matrix"},
            {"file_role": "reviewer_preemptive_response_pack", "path": "08_submission_strategy/reviewer_preemptive_response_pack.md", "status": "ready", "notes": "Reviewer-facing response wording and claim boundaries"},
            {"file_role": "editorial_triage_risk_audit", "path": "08_submission_strategy/editorial_triage_risk_audit.md", "status": "ready", "notes": "Desk-reject and reviewer-risk summary"},
            {"file_role": "reviewer_risk_stress_test_qc", "path": "04_results/qc/reviewer_risk_stress_test_qc.csv", "status": "ready_not_final_upload_clear", "notes": "Reviewer-risk QC; final upload still human-gated"},
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {"item": "reviewer_risk_response_pack", "value": "08_submission_strategy/reviewer_preemptive_response_pack.md", "status": "pass", "notes": "Pre-emptive reviewer-risk response pack generated"},
            {"item": "editorial_triage_risk_audit", "value": "08_submission_strategy/editorial_triage_risk_audit.md", "status": "pass", "notes": "Editorial triage risk audit generated"},
        ],
        ["item", "value", "status", "notes"],
    )


def update_text_surfaces(qc_rows: Sequence[Dict[str, object]]) -> None:
    marker = "2026-06-19 reviewer risk response pack"
    clearance = next(row for row in qc_rows if row["item"] == "machine_reviewer_risk_clearance")["value"]
    text = f"""
Reviewer-risk response pack:

- `08_submission_strategy/reviewer_risk_stress_test_matrix.csv`
- `08_submission_strategy/reviewer_preemptive_response_pack.md`
- `08_submission_strategy/editorial_triage_risk_audit.md`
- `04_results/qc/reviewer_risk_stress_test_qc.csv`
- `06_tables/reviewer_response_evidence_map.csv`

Machine reviewer-risk clearance: `{clearance}`. This layer maps likely reviewer objections to evidence files and safe response wording. It does not change the biological claim ceiling; final upload remains human-gated.
"""
    replace_or_append(ROOT / "README.md", marker, text)
    replace_or_append(ROOT / "00_project_log" / "master_log.md", marker, f"- 2026-06-19 latest: Generated reviewer-risk stress-test matrix, pre-emptive response pack and editorial triage audit. Machine reviewer-risk clearance: `{clearance}`.")
    replace_or_append(ROOT / "00_project_log" / "stage_summary.md", marker, f"- Reviewer-risk response pack complete: likely objections around novelty, public-data-only design, CAF confounding, prognosis, causality, single-cell LR bridges, spatial context and drug-resistance boundaries are mapped to current evidence files.")
    replace_or_append(ROOT / "00_project_log" / "decision_record.md", marker, "Decision: add reviewer-risk stress testing after machine bundle clearance.\n\nReason: for a pure public-data SCI submission, the strongest remaining machine-side need is not another weak data layer but a defensible, evidence-linked answer to predictable reviewer objections.")
    replace_or_append(ROOT / "00_project_log" / "context_checkpoint.md", marker, "Latest checkpoint: reviewer-risk response package generated. Use `08_submission_strategy/reviewer_preemptive_response_pack.md` and `reviewer_risk_stress_test_matrix.csv` when drafting cover letter, response-to-reviewers or deciding whether another analysis is truly needed.")
    checklist = ROOT / "08_submission_strategy" / "scientific_reports_submission_checklist.md"
    checklist_text = checklist.read_text(encoding="utf-8")
    if "- [x] Reviewer-risk response pack generated" not in checklist_text:
        checklist_text = checklist_text.replace("- [x] Reviewer-risk checklist present", "- [x] Reviewer-risk checklist present\n- [x] Reviewer-risk response pack generated")
    checklist.write_text(checklist_text, encoding="utf-8")

    project_root = ROOT.parent
    replace_or_append(
        project_root / "docs" / "agent" / "CURRENT_STATE.md",
        marker,
        f"""## 2026-06-19 reviewer-risk 预答辩包完成

`TMEM158_CaUPR_ESCC/` 已生成审稿风险压力测试与预答辩包：`08_submission_strategy/reviewer_risk_stress_test_matrix.csv`、`08_submission_strategy/reviewer_preemptive_response_pack.md`、`08_submission_strategy/editorial_triage_risk_audit.md`、`04_results/qc/reviewer_risk_stress_test_qc.csv` 和 `06_tables/reviewer_response_evidence_map.csv`。机器端 reviewer-risk clearance 为 `{clearance}`。

该层把最可能的审稿质疑，包括创新性、纯公共数据、TMEM158 因果、预后阴性、CAF 混杂、TAC_high 人工定义、GSE53625 targeted reannotation、单细胞 LR 因果、GSE221561 小样本、空间 source-data 边界、免疫抑制、drug resistance、batch effects、data/code availability 和最终人工元数据，逐条映射到证据文件和安全答辩措辞。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "DECISION_LOG.md",
        marker,
        """## 2026-06-19 reviewer-risk 预答辩包决策

- 决策：在投稿包机器端清关后，新增 reviewer-risk stress-test 和 pre-emptive response pack。
- 背景：当前普通生信证据继续增加的边际收益低；更关键的是提前防守纯公共数据稿常见审稿质疑。
- 依据：现有 9/10 readiness、bundle clearance pass、claim-boundary pass；新矩阵逐条绑定证据文件，避免凭空答辩。
- 可信度：高。
- 后续待验证：最终 cover letter 和 response-to-reviewers 应沿用该包中的保守话术，不得升级为因果或临床结论。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "EVIDENCE_LOG.md",
        marker,
        """### 2026-06-19 更新：reviewer-risk response pack

- 新增文件：`reviewer_risk_stress_test_matrix.csv`、`reviewer_preemptive_response_pack.md`、`editorial_triage_risk_audit.md`、`reviewer_risk_stress_test_qc.csv`、`reviewer_response_evidence_map.csv`。
- 解释：这是审稿防御和投稿风险证据层，不是新的生物学结果。它强化当前稿件适合按 public-data stress-ecology discovery 投稿，同时把预后、因果、药物耐受、免疫抑制和空间验证保留为边界。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "TASKS" / "2026-06-18-SMIM14-CaUPR-ESCC-bioinformatics.md",
        marker,
        """## 2026-06-19 最新追加：reviewer-risk 预答辩包

- 新增脚本：`TMEM158_CaUPR_ESCC/03_scripts/Python/build_reviewer_risk_response_pack.py`，并接入 `run_all.R`。
- 新增输出：reviewer-risk matrix、pre-emptive response pack、editorial triage audit、QC 和 evidence map。
- 当前意义：机器端已经把可能审稿质疑逐条绑定到证据文件和保守回应，减少纯生信稿因过度主张、CAF 混杂或缺湿实验被动挨打的风险。"""
    )


def main() -> None:
    rows = build_matrix()
    write_csv(
        ROOT / "08_submission_strategy" / "reviewer_risk_stress_test_matrix.csv",
        rows,
        [
            "risk_id",
            "severity",
            "reviewer_objection",
            "evidence_files",
            "evidence_status",
            "defensible_position",
            "claim_to_avoid",
            "short_response",
        ],
    )
    write_csv(
        ROOT / "06_tables" / "reviewer_response_evidence_map.csv",
        rows,
        [
            "risk_id",
            "severity",
            "reviewer_objection",
            "evidence_files",
            "evidence_status",
            "defensible_position",
            "claim_to_avoid",
            "short_response",
        ],
    )
    write_response_pack(rows)
    write_editorial_triage(rows)
    qc_rows = write_qc(rows)
    update_indexes(qc_rows)
    update_text_surfaces(qc_rows)
    missing = [row for row in rows if str(row["evidence_status"]).startswith("missing:")]
    high_missing = [row for row in missing if row["severity"] == "high"]
    clearance = "pass" if not high_missing else "needs_revision"
    print(
        "reviewer_risk_response_pack=completed "
        f"risk_rows={len(rows)} missing_evidence={len(missing)} "
        f"high_missing={len(high_missing)} machine_reviewer_risk_clearance={clearance}"
    )


if __name__ == "__main__":
    main()
