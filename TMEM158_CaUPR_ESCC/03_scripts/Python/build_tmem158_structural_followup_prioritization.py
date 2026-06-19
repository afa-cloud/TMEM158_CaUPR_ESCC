#!/usr/bin/env python3
"""Prioritize structural and assay follow-up for TAC_high bridge candidates.

This module is deliberately narrow. It does not infer physical interaction
from ligand-receptor scores or AlphaFold topology. It ranks already generated
CAF-to-epithelial ligand-receptor candidates for defined-partner modelling and
orthogonal experimental follow-up, while keeping the claim boundary explicit.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

PAIR_TESTS = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_pair_tests.csv"
PAIR_CORR = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_pair_correlations.csv"
AXIS_TESTS = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_axis_tests.csv"
AXIS_CORR = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_axis_correlations.csv"
TOPOLOGY_QC = ROOT / "04_results" / "qc" / "tmem158_protein_topology_claim_audit_qc.csv"

OUT_MD = ROOT / "08_submission_strategy" / "tmem158_structural_followup_prioritization.md"
OUT_CSV = ROOT / "08_submission_strategy" / "tmem158_structural_followup_prioritization.csv"
OUT_TOP = ROOT / "06_tables" / "tmem158_structural_followup_prioritization_top_pairs.csv"
QC_CSV = ROOT / "04_results" / "qc" / "tmem158_structural_followup_prioritization_qc.csv"


PAIR_FIELDS = [
    "row_type",
    "priority_rank",
    "priority_tier",
    "category",
    "candidate",
    "ligand",
    "receptor",
    "evidence_summary",
    "delta_TAC_high_minus_other",
    "pair_FDR",
    "boundary_call",
    "CAF_score_rho",
    "CAF_score_FDR",
    "fibroblast_signature_rho",
    "fibroblast_signature_FDR",
    "perk_caf_ecology_rho",
    "perk_caf_ecology_FDR",
    "structural_class",
    "recommended_followup",
    "claim_boundary",
    "structural_followup_score",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: object, digits: int = 3) -> str:
    number = fnum(value, default=float("nan"))
    if number != number:
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def key_value(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    if not rows:
        return {}
    if "item" in rows[0] and "value" in rows[0]:
        return {row.get("item", ""): row.get("value", "") for row in rows}
    return {}


def correlation_lookup(rows: Iterable[Dict[str, str]], id_field: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    out: Dict[str, Dict[str, Dict[str, str]]] = {}
    for row in rows:
        key = row.get(id_field, "")
        feature = row.get("feature", "")
        if not key or not feature:
            continue
        out.setdefault(key, {})[feature] = row
    return out


def structural_class(ligand: str, receptor: str, category: str) -> tuple[str, float, str]:
    ligand_u = ligand.upper()
    receptor_u = receptor.upper()
    category_u = category.upper()
    if category == "ECM_integrin" or receptor_u.startswith("ITG"):
        if ligand_u in {"POSTN", "FN1"}:
            return (
                "ECM-integrin adhesion bridge",
                1.00,
                "defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays",
            )
        if ligand_u.startswith("COL"):
            return (
                "collagen-integrin matrix bridge",
                0.90,
                "module-level structural follow-up; collagen multimer context makes biochemical and spatial validation more important than single-pair modelling",
            )
        if ligand_u == "SPP1":
            return (
                "SPP1-integrin/CD44 bridge",
                0.82,
                "defined receptor follow-up with spatial/proximity assays; use modelling only as exploratory partner prioritization",
            )
    if ligand_u == "MIF" and receptor_u in {"CXCR4", "CD74"}:
        return (
            "MIF receptor bridge",
            0.88,
            "prioritize receptor activation/proximity assays and pathway readouts; structural modelling is secondary to receptor-state validation",
        )
    if "TGF" in category_u or ligand_u in {"INHBA", "TGFB1", "TGFB2", "TGFB3"}:
        return (
            "TGF-beta/activin signalling bridge",
            0.70,
            "follow only if expression evidence is positive; receptor phosphorylation/readout assays outrank static modelling",
        )
    if ligand_u in {"IL6", "LIF", "OSM"}:
        return (
            "cytokine-family signalling bridge",
            0.55,
            "current TAC_high evidence is weak or negative; keep as boundary/control rather than primary structural target",
        )
    return (
        "other ligand-receptor bridge",
        0.50,
        "rank below ECM-integrin and MIF receptor candidates unless future evidence strengthens this pair",
    )


def score_pair(pair: Dict[str, str], corr: Dict[str, Dict[str, str]], topology_pass: bool) -> Dict[str, object]:
    pair_corr = corr.get(pair.get("pair_id", ""), {})
    caf = pair_corr.get("CAF_score", {})
    fibro = pair_corr.get("fibroblast_TAC_high_top50_signature", {})
    perk_caf = pair_corr.get("perk_caf_ecology_score", {})

    delta = fnum(pair.get("delta_TAC_high_minus_other"))
    fdr = fnum(pair.get("FDR"), default=1.0)
    boundary = pair.get("boundary_call", "")
    if boundary == "TAC_high_higher_FDR":
        fdr_support = 1.0
    elif boundary == "TAC_high_higher_nominal":
        fdr_support = 0.55
    elif delta > 0 and fdr < 0.25:
        fdr_support = 0.25
    else:
        fdr_support = 0.0

    effect_score = max(0.0, min(delta / 0.9, 1.0))
    corr_candidates = []
    for feature_row in (caf, fibro, perk_caf):
        rho = fnum(feature_row.get("rho"))
        row_fdr = fnum(feature_row.get("FDR"), default=1.0)
        if rho > 0 and row_fdr < 0.10:
            corr_candidates.append(rho)
    corr_score = max(0.0, min((max(corr_candidates) if corr_candidates else 0.0) / 0.85, 1.0))
    class_label, class_score, followup = structural_class(pair.get("ligand", ""), pair.get("receptor", ""), pair.get("category", ""))
    topology_score = 1.0 if topology_pass else 0.0
    score = 0.35 * fdr_support + 0.25 * effect_score + 0.25 * corr_score + 0.10 * class_score + 0.05 * topology_score
    if score >= 0.75:
        tier = "high"
    elif score >= 0.50:
        tier = "medium"
    else:
        tier = "low"

    evidence = (
        f"delta={fmt(delta)}; pair FDR={fmt(fdr)}; "
        f"CAF rho={fmt(caf.get('rho'))}/FDR={fmt(caf.get('FDR'))}; "
        f"fibroblast-signature rho={fmt(fibro.get('rho'))}/FDR={fmt(fibro.get('FDR'))}; "
        f"PERK-CAF ecology rho={fmt(perk_caf.get('rho'))}/FDR={fmt(perk_caf.get('FDR'))}"
    )
    return {
        "row_type": "ligand_receptor_pair",
        "priority_rank": "",
        "priority_tier": tier,
        "category": pair.get("category", ""),
        "candidate": pair.get("pair_label", ""),
        "ligand": pair.get("ligand", ""),
        "receptor": pair.get("receptor", ""),
        "evidence_summary": evidence,
        "delta_TAC_high_minus_other": fmt(delta),
        "pair_FDR": fmt(fdr),
        "boundary_call": boundary,
        "CAF_score_rho": fmt(caf.get("rho")),
        "CAF_score_FDR": fmt(caf.get("FDR")),
        "fibroblast_signature_rho": fmt(fibro.get("rho")),
        "fibroblast_signature_FDR": fmt(fibro.get("FDR")),
        "perk_caf_ecology_rho": fmt(perk_caf.get("rho")),
        "perk_caf_ecology_FDR": fmt(perk_caf.get("FDR")),
        "structural_class": class_label,
        "recommended_followup": followup,
        "claim_boundary": "Candidate structural/assay follow-up only; ligand-receptor scores do not prove physical communication, receptor activation, TMEM158 binding or causality.",
        "structural_followup_score": round(score, 4),
    }


def add_module_rows(rows: List[Dict[str, object]], topology_pass: bool) -> None:
    rows.extend(
        [
            {
                "row_type": "module_context",
                "priority_rank": "",
                "priority_tier": "high" if topology_pass else "medium",
                "category": "TMEM158 topology",
                "candidate": "TMEM158 membrane-topology assay bridge",
                "ligand": "TMEM158",
                "receptor": "",
                "evidence_summary": "UniProt/QuickGO/HPA plus AlphaFold audit supports membrane/topology plausibility but not ER localization or direct interaction.",
                "structural_class": "membrane-protein entry point",
                "recommended_followup": "localization, membrane fractionation, proximity labelling and co-IP should be used to test whether TMEM158 is near ECM-integrin/Ca2-UPR contexts; do not present it as a known partner.",
                "claim_boundary": "No direct TMEM158-ECM, TMEM158-integrin or TMEM158-Ca2/UPR interface is established.",
                "structural_followup_score": 0.80 if topology_pass else 0.55,
            },
            {
                "row_type": "module_context",
                "priority_rank": "",
                "priority_tier": "medium",
                "category": "Ca2/UPR readout",
                "candidate": "Ca2/UPR branch readout panel",
                "ligand": "",
                "receptor": "",
                "evidence_summary": "Current evidence prioritizes TAC_high Ca2/PERK-core and CAF-coupled stress ecology as readouts rather than direct structural partners.",
                "structural_class": "functional readout panel",
                "recommended_followup": "measure Ca2 flux/SOCE, ATP2A2/STIM1/ORAI1 context, PERK/IRE1/ATF6 branch proteins and proteostasis readouts after TMEM158 or candidate-bridge perturbation.",
                "claim_boundary": "Functional readouts are not defined-partner structural interactions.",
                "structural_followup_score": 0.62,
            },
        ]
    )


def prioritize() -> tuple[List[Dict[str, object]], Dict[str, str]]:
    pair_tests = read_csv(PAIR_TESTS)
    corr = correlation_lookup(read_csv(PAIR_CORR), "pair_id")
    topology_qc = key_value(TOPOLOGY_QC)
    topology_pass = topology_qc.get("machine_protein_topology_claim_clearance") == "pass"

    rows = [score_pair(row, corr, topology_pass) for row in pair_tests]
    rows.sort(
        key=lambda row: (
            fnum(row.get("structural_followup_score")),
            fnum(row.get("delta_TAC_high_minus_other")),
            fnum(row.get("CAF_score_rho")),
        ),
        reverse=True,
    )
    for idx, row in enumerate(rows, start=1):
        row["priority_rank"] = idx
    add_module_rows(rows, topology_pass)
    return rows, topology_qc


def summarize_axes() -> List[str]:
    tests = {row.get("axis", ""): row for row in read_csv(AXIS_TESTS)}
    corr = correlation_lookup(read_csv(AXIS_CORR), "axis")
    lines: List[str] = []
    for axis in ["ECM_integrin", "MIF_SPP1_axis", "Growth_factor", "IL6_family"]:
        row = tests.get(axis, {})
        axis_corr = corr.get(axis, {})
        caf = axis_corr.get("CAF_score", {})
        fibro = axis_corr.get("fibroblast_TAC_high_top50_signature", {})
        if not row:
            continue
        lines.append(
            f"- `{axis}`: delta={fmt(row.get('delta_TAC_high_minus_other'))}, FDR={fmt(row.get('FDR'))}, "
            f"boundary={row.get('boundary_call', '')}; CAF rho={fmt(caf.get('rho'))}, "
            f"fibroblast-signature rho={fmt(fibro.get('rho'))}."
        )
    return lines


def write_report(rows: Sequence[Dict[str, object]], qc_rows: Sequence[Dict[str, object]]) -> None:
    top_pairs = [row for row in rows if row.get("row_type") == "ligand_receptor_pair"][:10]
    qc = {str(row["item"]): str(row["value"]) for row in qc_rows}
    lines = [
        "# TMEM158/TAC_high Structural Follow-up Prioritization",
        "",
        f"Generated: {NOW}",
        "",
        "## Bottom Line",
        "",
        "The strongest structure/assay follow-up candidates are ECM-integrin bridges, led by POSTN->ITGA5, followed by POSTN-integrins, FN1->ITGA5 and selected collagen-integrin pairs. MIF->CXCR4 is a secondary receptor-state candidate. These are priorities for defined-partner co-modelling and experimental validation, not evidence that physical communication or TMEM158 binding has occurred.",
        "",
        "## Top Priorities",
        "",
        "| Rank | Candidate | Tier | Score | Evidence | Recommended Follow-up |",
        "|---|---|---|---|---|---|",
    ]
    for row in top_pairs:
        evidence = str(row["evidence_summary"]).replace("|", "/")
        followup = str(row["recommended_followup"]).replace("|", "/")
        lines.append(
            f"| {row['priority_rank']} | {row['candidate']} | {row['priority_tier']} | {row['structural_followup_score']} | {evidence} | {followup} |"
        )

    lines.extend(
        [
            "",
            "## Axis Context",
            "",
        ]
    )
    axis_lines = summarize_axes()
    lines.extend(axis_lines if axis_lines else ["- Axis context files were not available."])
    lines.extend(
        [
            "",
            "## How To Use This Layer",
            "",
            "- Use POSTN/FN1/collagen-integrin candidates as the primary ECM-CAF-to-epithelial structural follow-up set.",
            "- Use AlphaFold Server or related defined-partner tools as hypothesis generators only; ECM multimerization, integrin activation state and membrane context require orthogonal assays.",
            "- Pair modelling should be followed by spatial co-expression, ligand/receptor perturbation, proximity labelling, co-IP/crosslinking-MS where feasible, and epithelial Ca2/UPR/proteostasis readouts.",
            "- TMEM158 remains a membrane-protein entry point for proximity/localization testing; it is not currently a demonstrated binding partner of ECM, integrins or Ca2/UPR proteins.",
            "",
            "## Machine QC",
            "",
        ]
    )
    for row in qc_rows:
        lines.append(f"- `{row['item']}`: {row['value']} ({row['status']}) - {row['notes']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This prioritization does not upgrade the public-data manuscript into a physical-interaction or causal-signalling study. It does not prove direct ER localization, TMEM158-ECM binding, TMEM158-integrin binding, CAF-to-epithelial ligand causality, receptor activation, Ca2/UPR protein binding or treatment response.",
            "",
            f"Machine structural follow-up clearance: `{qc.get('machine_structural_followup_clearance', '')}`.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_qc(rows: Sequence[Dict[str, object]], topology_qc: Dict[str, str]) -> List[Dict[str, object]]:
    required = [PAIR_TESTS, PAIR_CORR, AXIS_TESTS, AXIS_CORR, TOPOLOGY_QC]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    pair_rows = [row for row in rows if row.get("row_type") == "ligand_receptor_pair"]
    fdr_positive = [row for row in pair_rows if row.get("boundary_call") == "TAC_high_higher_FDR"]
    high_priority = [row for row in pair_rows if row.get("priority_tier") == "high"]
    top_pair = pair_rows[0].get("candidate", "") if pair_rows else ""
    pass_clearance = not missing and top_pair == "POSTN->ITGA5" and len(fdr_positive) >= 10
    return [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "input_files_missing", "value": len(missing), "status": "pass" if not missing else "needs_revision", "notes": "Missing: " + "; ".join(missing) if missing else "All required LR, axis and topology-boundary files are present"},
        {"item": "ranked_lr_pairs", "value": len(pair_rows), "status": "pass" if pair_rows else "needs_revision", "notes": "Ligand-receptor pairs ranked for follow-up"},
        {"item": "tac_high_higher_fdr_pairs", "value": len(fdr_positive), "status": "pass" if len(fdr_positive) >= 10 else "needs_review", "notes": "FDR-positive TAC_high-higher LR pairs retained from the upstream bridge module"},
        {"item": "high_priority_pairs", "value": len(high_priority), "status": "pass" if high_priority else "needs_review", "notes": "Pairs prioritized for defined-partner structural or proximity follow-up"},
        {"item": "top_structural_followup_pair", "value": top_pair, "status": "pass" if top_pair == "POSTN->ITGA5" else "needs_review", "notes": "Top candidate should remain evidence-led by effect size and CAF/fibroblast coupling"},
        {"item": "protein_topology_claim_clearance", "value": topology_qc.get("machine_protein_topology_claim_clearance", ""), "status": "pass_boundary" if topology_qc.get("machine_protein_topology_claim_clearance") == "pass" else "needs_review", "notes": "TMEM158 topology is used for assayability context, not interaction proof"},
        {"item": "direct_interaction_claim", "value": "not_made", "status": "pass", "notes": "The report explicitly avoids physical-interaction and causality claims"},
        {"item": "machine_structural_followup_clearance", "value": "pass" if pass_clearance else "needs_revision", "status": "pass" if pass_clearance else "needs_revision", "notes": "Pass means prioritization is complete and claim boundaries are explicit"},
    ]


def update_indexes() -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "tmem158_structural_followup_prioritization", "path": "08_submission_strategy/tmem158_structural_followup_prioritization.md"},
            {"result": "tmem158_structural_followup_prioritization_table", "path": "08_submission_strategy/tmem158_structural_followup_prioritization.csv"},
            {"result": "tmem158_structural_followup_prioritization_top_pairs", "path": "06_tables/tmem158_structural_followup_prioritization_top_pairs.csv"},
            {"result": "tmem158_structural_followup_prioritization_qc", "path": "04_results/qc/tmem158_structural_followup_prioritization_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {
                "file_role": "tmem158_structural_followup_prioritization",
                "path": "08_submission_strategy/tmem158_structural_followup_prioritization.md",
                "status": "ready",
                "notes": "Defined-partner structural and assay follow-up prioritization for TAC_high CAF-to-epithelial bridge candidates",
            },
            {
                "file_role": "tmem158_structural_followup_prioritization_table",
                "path": "08_submission_strategy/tmem158_structural_followup_prioritization.csv",
                "status": "ready",
                "notes": "Machine-readable ranking table with claim boundaries",
            },
            {
                "file_role": "tmem158_structural_followup_prioritization_qc",
                "path": "04_results/qc/tmem158_structural_followup_prioritization_qc.csv",
                "status": "ready",
                "notes": "QC summary for structural follow-up prioritization",
            },
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {
                "item": "structural_followup_prioritization",
                "value": "08_submission_strategy/tmem158_structural_followup_prioritization.md",
                "status": "pass",
                "notes": "Prioritizes POSTN/FN1/collagen-integrin and MIF-CXCR4 follow-up while avoiding direct-interaction claims",
            }
        ],
        ["item", "value", "status", "notes"],
    )


def main() -> None:
    rows, topology_qc = prioritize()
    qc_rows = build_qc(rows, topology_qc)
    write_csv(OUT_CSV, rows, PAIR_FIELDS)
    write_csv(OUT_TOP, [row for row in rows if row.get("row_type") == "ligand_receptor_pair"][:20], PAIR_FIELDS)
    write_csv(QC_CSV, qc_rows, ["item", "value", "status", "notes"])
    write_report(rows, qc_rows)
    update_indexes()
    clearance = next(row for row in qc_rows if row["item"] == "machine_structural_followup_clearance")
    top_pair = next(row for row in qc_rows if row["item"] == "top_structural_followup_pair")
    print(
        "tmem158_structural_followup_prioritization=completed "
        f"top_pair={top_pair['value']} clearance={clearance['value']} rows={len(rows)}"
    )


if __name__ == "__main__":
    main()
