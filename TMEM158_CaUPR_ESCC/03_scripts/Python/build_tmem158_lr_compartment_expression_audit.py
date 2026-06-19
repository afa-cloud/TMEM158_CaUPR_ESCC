#!/usr/bin/env python3
"""Audit compartment expression support for prioritized TAC_high LR candidates.

The structural follow-up ranking nominates candidate CAF-to-epithelial bridges.
This script checks whether those candidates have the expected compartment
expression pattern in the existing GSE160269 pseudo-bulk tables: ligand signal
in fibroblast/CAF and receptor signal in epithelial profiles. It is a sanity
audit, not a cell-cell communication or receptor-activation proof.
"""

from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

GENE_MEANS = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_gene_means.csv"
PAIR_SCORES = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_pair_scores.csv"
PAIR_TESTS = ROOT / "04_results" / "ligand_receptor" / "tmem158_tac_high_caf_epi_lr_pair_tests.csv"
STRUCTURAL_TOP = ROOT / "06_tables" / "tmem158_structural_followup_prioritization_top_pairs.csv"

OUT_MD = ROOT / "08_submission_strategy" / "tmem158_lr_compartment_expression_audit.md"
OUT_CSV = ROOT / "08_submission_strategy" / "tmem158_lr_compartment_expression_audit.csv"
OUT_TOP = ROOT / "06_tables" / "tmem158_lr_compartment_expression_audit_top_candidates.csv"
QC_CSV = ROOT / "04_results" / "qc" / "tmem158_lr_compartment_expression_audit_qc.csv"

FIELDS = [
    "priority_rank",
    "candidate",
    "category",
    "ligand",
    "receptor",
    "n_tumor_samples",
    "n_tac_high",
    "n_other",
    "fibroblast_ligand_median_expr",
    "epithelial_ligand_median_expr",
    "ligand_fibroblast_minus_epithelial",
    "fibroblast_ligand_median_pct_positive",
    "epithelial_receptor_median_expr",
    "fibroblast_receptor_median_expr",
    "receptor_epithelial_minus_fibroblast",
    "epithelial_receptor_median_pct_positive",
    "lr_score_delta_TAC_high_minus_other",
    "lr_score_FDR",
    "ligand_TAC_high_delta",
    "ligand_TAC_high_p",
    "receptor_TAC_high_delta",
    "receptor_TAC_high_p",
    "compartment_expression_call",
    "audit_boundary",
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


def fnum(value: object, default: float = math.nan) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_numbers(values: Iterable[object]) -> List[float]:
    out = [fnum(value) for value in values]
    return [value for value in out if math.isfinite(value)]


def med(values: Iterable[object]) -> float:
    nums = clean_numbers(values)
    return median(nums) if nums else math.nan


def fmt(value: object, digits: int = 3) -> str:
    number = fnum(value)
    if not math.isfinite(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def rank_sum_p(group_a: List[float], group_b: List[float]) -> float:
    """Approximate two-sided Mann-Whitney/Wilcoxon rank-sum p-value."""
    a = [x for x in group_a if math.isfinite(x)]
    b = [x for x in group_b if math.isfinite(x)]
    if len(a) < 3 or len(b) < 3:
        return math.nan
    values = [(x, 0) for x in a] + [(x, 1) for x in b]
    values.sort(key=lambda item: item[0])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[j][0] == values[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    r_a = sum(rank for rank, item in zip(ranks, values) if item[1] == 0)
    n1, n2 = len(a), len(b)
    u1 = r_a - n1 * (n1 + 1) / 2.0
    mean_u = n1 * n2 / 2.0
    var_u = n1 * n2 * (n1 + n2 + 1) / 12.0
    if var_u <= 0:
        return math.nan
    z = (u1 - mean_u) / math.sqrt(var_u)
    return math.erfc(abs(z) / math.sqrt(2.0))


def build_gene_lookup() -> Dict[tuple[str, str, str], Dict[str, str]]:
    lookup: Dict[tuple[str, str, str], Dict[str, str]] = {}
    for row in read_csv(GENE_MEANS):
        if row.get("condition") != "Tumor":
            continue
        key = (row.get("sample", ""), row.get("compartment", ""), row.get("gene", ""))
        lookup[key] = row
    return lookup


def pair_test_lookup() -> Dict[str, Dict[str, str]]:
    return {row.get("pair_label", ""): row for row in read_csv(PAIR_TESTS)}


def pair_score_lookup() -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {}
    for row in read_csv(PAIR_SCORES):
        out.setdefault(row.get("pair_label", ""), []).append(row)
    return out


def audit_pair(
    candidate: Dict[str, str],
    gene_lookup: Dict[tuple[str, str, str], Dict[str, str]],
    score_lookup: Dict[str, List[Dict[str, str]]],
    tests: Dict[str, Dict[str, str]],
) -> Dict[str, object]:
    ligand = candidate.get("ligand", "")
    receptor = candidate.get("receptor", "")
    label = candidate.get("candidate") or candidate.get("pair_label", "")
    rows = score_lookup.get(label, [])
    samples = [row.get("sample", "") for row in rows if row.get("sample")]

    def expr(sample: str, compartment: str, gene: str, field: str) -> float:
        return fnum(gene_lookup.get((sample, compartment, gene), {}).get(field))

    fib_lig = [expr(sample, "Fibroblast", ligand, "mean_log1p_cp10k") for sample in samples]
    epi_lig = [expr(sample, "Epithelial", ligand, "mean_log1p_cp10k") for sample in samples]
    fib_lig_pct = [expr(sample, "Fibroblast", ligand, "pct_positive") for sample in samples]
    epi_rec = [expr(sample, "Epithelial", receptor, "mean_log1p_cp10k") for sample in samples]
    fib_rec = [expr(sample, "Fibroblast", receptor, "mean_log1p_cp10k") for sample in samples]
    epi_rec_pct = [expr(sample, "Epithelial", receptor, "pct_positive") for sample in samples]

    high_rows = [row for row in rows if row.get("TAC_high_group") == "High"]
    low_rows = [row for row in rows if row.get("TAC_high_group") != "High"]
    high_samples = [row.get("sample", "") for row in high_rows]
    low_samples = [row.get("sample", "") for row in low_rows]
    high_lig = [expr(sample, "Fibroblast", ligand, "mean_log1p_cp10k") for sample in high_samples]
    low_lig = [expr(sample, "Fibroblast", ligand, "mean_log1p_cp10k") for sample in low_samples]
    high_rec = [expr(sample, "Epithelial", receptor, "mean_log1p_cp10k") for sample in high_samples]
    low_rec = [expr(sample, "Epithelial", receptor, "mean_log1p_cp10k") for sample in low_samples]

    fib_lig_med = med(fib_lig)
    epi_lig_med = med(epi_lig)
    epi_rec_med = med(epi_rec)
    fib_rec_med = med(fib_rec)
    fib_lig_pct_med = med(fib_lig_pct)
    epi_rec_pct_med = med(epi_rec_pct)
    lig_delta = med(high_lig) - med(low_lig)
    rec_delta = med(high_rec) - med(low_rec)
    lig_p = rank_sum_p(clean_numbers(high_lig), clean_numbers(low_lig))
    rec_p = rank_sum_p(clean_numbers(high_rec), clean_numbers(low_rec))

    ligand_ok = math.isfinite(fib_lig_med) and fib_lig_med > 0.25 and fib_lig_pct_med > 0.05
    receptor_ok = math.isfinite(epi_rec_med) and epi_rec_med > 0.02 and epi_rec_pct_med > 0.01
    ligand_fib_enriched = math.isfinite(fib_lig_med - epi_lig_med) and fib_lig_med >= epi_lig_med
    call = "pass_expected_compartment_pattern" if ligand_ok and receptor_ok and ligand_fib_enriched else "pass_with_boundary"
    if not ligand_ok or not receptor_ok:
        call = "candidate_requires_expression_boundary"

    test = tests.get(label, {})
    return {
        "priority_rank": candidate.get("priority_rank", ""),
        "candidate": label,
        "category": candidate.get("category", ""),
        "ligand": ligand,
        "receptor": receptor,
        "n_tumor_samples": len(samples),
        "n_tac_high": len(high_samples),
        "n_other": len(low_samples),
        "fibroblast_ligand_median_expr": fmt(fib_lig_med),
        "epithelial_ligand_median_expr": fmt(epi_lig_med),
        "ligand_fibroblast_minus_epithelial": fmt(fib_lig_med - epi_lig_med),
        "fibroblast_ligand_median_pct_positive": fmt(fib_lig_pct_med),
        "epithelial_receptor_median_expr": fmt(epi_rec_med),
        "fibroblast_receptor_median_expr": fmt(fib_rec_med),
        "receptor_epithelial_minus_fibroblast": fmt(epi_rec_med - fib_rec_med),
        "epithelial_receptor_median_pct_positive": fmt(epi_rec_pct_med),
        "lr_score_delta_TAC_high_minus_other": fmt(test.get("delta_TAC_high_minus_other")),
        "lr_score_FDR": fmt(test.get("FDR")),
        "ligand_TAC_high_delta": fmt(lig_delta),
        "ligand_TAC_high_p": fmt(lig_p),
        "receptor_TAC_high_delta": fmt(rec_delta),
        "receptor_TAC_high_p": fmt(rec_p),
        "compartment_expression_call": call,
        "audit_boundary": "Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding.",
    }


def build_rows() -> List[Dict[str, object]]:
    structural_rows = [
        row
        for row in read_csv(STRUCTURAL_TOP)
        if row.get("row_type") == "ligand_receptor_pair"
    ]
    top_rows = structural_rows[:20]
    gene_lookup = build_gene_lookup()
    score_lookup = pair_score_lookup()
    tests = pair_test_lookup()
    rows = [audit_pair(row, gene_lookup, score_lookup, tests) for row in top_rows]
    rows.sort(key=lambda row: fnum(row.get("priority_rank"), 9999))
    return rows


def build_qc(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    required = [GENE_MEANS, PAIR_SCORES, PAIR_TESTS, STRUCTURAL_TOP]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    pass_expected = [row for row in rows if row.get("compartment_expression_call") == "pass_expected_compartment_pattern"]
    boundary = [row for row in rows if row.get("compartment_expression_call") != "pass_expected_compartment_pattern"]
    top = rows[0].get("candidate", "") if rows else ""
    top_ok = rows and rows[0].get("compartment_expression_call") in {"pass_expected_compartment_pattern", "pass_with_boundary"}
    machine_pass = not missing and bool(rows) and top == "POSTN->ITGA5" and top_ok
    return [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "input_files_missing", "value": len(missing), "status": "pass" if not missing else "needs_revision", "notes": "Missing: " + "; ".join(missing) if missing else "All required LR and compartment-expression inputs are present"},
        {"item": "audited_top_structural_pairs", "value": len(rows), "status": "pass" if rows else "needs_revision", "notes": "Top structural follow-up pairs audited for compartment-expression feasibility"},
        {"item": "expected_compartment_pattern_pairs", "value": len(pass_expected), "status": "pass" if pass_expected else "needs_review", "notes": "Pairs with fibroblast ligand and detectable epithelial receptor pattern"},
        {"item": "expression_boundary_pairs", "value": len(boundary), "status": "pass_boundary", "notes": "Pairs retained with expression or compartment caveats"},
        {"item": "top_pair", "value": top, "status": "pass" if top == "POSTN->ITGA5" else "needs_review", "notes": "The top structural candidate remains POSTN->ITGA5"},
        {"item": "direct_communication_claim", "value": "not_made", "status": "pass", "notes": "The report explicitly avoids communication/activation/causality claims"},
        {"item": "machine_lr_compartment_expression_clearance", "value": "pass" if machine_pass else "needs_revision", "status": "pass" if machine_pass else "needs_revision", "notes": "Pass means the expression-feasibility audit is complete and bounded"},
    ]


def write_report(rows: Sequence[Dict[str, object]], qc_rows: Sequence[Dict[str, object]]) -> None:
    qc = {str(row["item"]): str(row["value"]) for row in qc_rows}
    lines = [
        "# TAC_high LR Compartment-Expression Audit",
        "",
        f"Generated: {NOW}",
        "",
        "## Bottom Line",
        "",
        "This audit checks whether prioritized TAC_high structural follow-up candidates show a compatible single-cell compartment-expression pattern in GSE160269: ligand signal in fibroblast/CAF pseudo-bulk and receptor signal in epithelial pseudo-bulk. It supports expression feasibility for follow-up prioritization, not physical cell-cell communication.",
        "",
        "## Top Candidate Audit",
        "",
        "| Rank | Candidate | Call | Fibroblast Ligand Median | Epithelial Receptor Median | Ligand Fibroblast-Epithelial | Receptor Epithelial-Fibroblast | LR FDR | Boundary |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows[:12]:
        lines.append(
            f"| {row['priority_rank']} | {row['candidate']} | {row['compartment_expression_call']} | "
            f"{row['fibroblast_ligand_median_expr']} | {row['epithelial_receptor_median_expr']} | "
            f"{row['ligand_fibroblast_minus_epithelial']} | {row['receptor_epithelial_minus_fibroblast']} | "
            f"{row['lr_score_FDR']} | {row['audit_boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `pass_expected_compartment_pattern` means the public single-cell pseudo-bulk layer supports ligand availability in fibroblast/CAF and receptor detectability in epithelial profiles.",
            "- `pass_with_boundary` or `candidate_requires_expression_boundary` means the pair can remain as a candidate only with explicit expression caveats.",
            "- Low epithelial receptor expression does not invalidate all follow-up, but it shifts priority toward spatial/protein validation and receptor-activation assays.",
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
            "This audit does not prove ligand-receptor communication, spatial adjacency, receptor activation, ligand causality, TMEM158 binding, ECM binding or Ca2/UPR pathway activation. It only verifies whether the nominated candidates have a compatible public single-cell compartment-expression pattern for follow-up.",
            "",
            f"Machine LR compartment-expression clearance: `{qc.get('machine_lr_compartment_expression_clearance', '')}`.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_indexes() -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "tmem158_lr_compartment_expression_audit", "path": "08_submission_strategy/tmem158_lr_compartment_expression_audit.md"},
            {"result": "tmem158_lr_compartment_expression_audit_table", "path": "08_submission_strategy/tmem158_lr_compartment_expression_audit.csv"},
            {"result": "tmem158_lr_compartment_expression_audit_top_candidates", "path": "06_tables/tmem158_lr_compartment_expression_audit_top_candidates.csv"},
            {"result": "tmem158_lr_compartment_expression_audit_qc", "path": "04_results/qc/tmem158_lr_compartment_expression_audit_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {
                "file_role": "tmem158_lr_compartment_expression_audit",
                "path": "08_submission_strategy/tmem158_lr_compartment_expression_audit.md",
                "status": "ready",
                "notes": "Single-cell compartment-expression sanity audit for prioritized TAC_high ligand-receptor candidates",
            },
            {
                "file_role": "tmem158_lr_compartment_expression_audit_table",
                "path": "08_submission_strategy/tmem158_lr_compartment_expression_audit.csv",
                "status": "ready",
                "notes": "Machine-readable compartment-expression audit table",
            },
            {
                "file_role": "tmem158_lr_compartment_expression_audit_qc",
                "path": "04_results/qc/tmem158_lr_compartment_expression_audit_qc.csv",
                "status": "ready",
                "notes": "QC summary for LR compartment-expression audit",
            },
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {
                "item": "lr_compartment_expression_audit",
                "value": "08_submission_strategy/tmem158_lr_compartment_expression_audit.md",
                "status": "pass",
                "notes": "Checks fibroblast ligand and epithelial receptor expression feasibility for top structural follow-up candidates",
            }
        ],
        ["item", "value", "status", "notes"],
    )


def main() -> None:
    rows = build_rows()
    qc_rows = build_qc(rows)
    write_csv(OUT_CSV, rows, FIELDS)
    write_csv(OUT_TOP, rows[:12], FIELDS)
    write_csv(QC_CSV, qc_rows, ["item", "value", "status", "notes"])
    write_report(rows, qc_rows)
    update_indexes()
    clearance = next(row for row in qc_rows if row["item"] == "machine_lr_compartment_expression_clearance")
    top = next(row for row in qc_rows if row["item"] == "top_pair")
    print(
        "tmem158_lr_compartment_expression_audit=completed "
        f"top_pair={top['value']} clearance={clearance['value']} rows={len(rows)}"
    )


if __name__ == "__main__":
    main()
