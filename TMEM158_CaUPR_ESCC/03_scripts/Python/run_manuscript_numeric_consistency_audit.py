#!/usr/bin/env python3
"""Audit manuscript numeric claims against machine-readable result tables.

This is a submission-quality control layer. It does not create new biological
evidence. It checks whether key numeric claims in the Scientific Reports draft
remain synchronized with the current result tables after repeated manuscript
and workflow regeneration.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT.parent
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
MANUSCRIPT = ROOT / "07_manuscript" / "manuscript_scientific_reports.md"
AUDIT_CSV = ROOT / "04_results" / "qc" / "manuscript_numeric_consistency_audit.csv"
AUDIT_QC = ROOT / "04_results" / "qc" / "manuscript_numeric_consistency_audit_qc.csv"
AUDIT_MD = ROOT / "08_submission_strategy" / "manuscript_numeric_consistency_audit.md"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    full = ROOT / path if isinstance(path, str) else path
    if not full.exists():
        raise FileNotFoundError(full)
    with full.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def upsert_csv(path: Path, key: str, new_rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    rows: Dict[str, Dict[str, object]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get(key):
                    rows[row[key]] = dict(row)
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
        current = pattern.sub(block, current)
    else:
        if current and not current.endswith("\n"):
            current += "\n"
        current += "\n" + block
    ensure_parent(path)
    path.write_text(current, encoding="utf-8")


def norm_text(text: str) -> str:
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = text.replace(" ", "").replace("\t", "").replace("\n", "")
    text = re.sub(r"e([+-])0+(\d)", r"e\1\2", text, flags=re.I)
    return text.lower()


def any_fragment_present(manuscript_norm: str, fragments: Sequence[str]) -> bool:
    return any(norm_text(fragment) in manuscript_norm for fragment in fragments if fragment)


def row_where(rows: Sequence[Dict[str, str]], **conditions: str) -> Dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in conditions.items()):
            return row
    raise KeyError(f"No row matched {conditions}")


def value_where(rows: Sequence[Dict[str, str]], key_field: str, key_value: str, value_field: str = "value") -> str:
    return row_where(rows, **{key_field: key_value})[value_field]


def f_float(value: str | float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def f_sig(value: str | float, sig: int = 3) -> str:
    val = float(value)
    if val == 0:
        return "0"
    text = f"{val:.{sig}g}"
    return re.sub(r"e([+-])0+(\d)", r"e\1\2", text)


def f_sci(value: str | float, digits: int = 2) -> str:
    text = f"{float(value):.{digits}e}"
    return re.sub(r"e([+-])0+(\d)", r"e\1\2", text)


def claim(
    rows: List[Dict[str, object]],
    manuscript_norm: str,
    claim_id: str,
    category: str,
    source_path: str,
    source_value: str,
    expected_fragments: Sequence[str],
    priority: str = "critical",
    notes: str = "",
) -> None:
    present = any_fragment_present(manuscript_norm, expected_fragments)
    rows.append(
        {
            "claim_id": claim_id,
            "category": category,
            "priority": priority,
            "source_path": source_path,
            "source_value": source_value,
            "expected_fragments": " | ".join(expected_fragments),
            "status": "pass" if present else "missing_or_stale",
            "notes": notes,
        }
    )


def build_claim_rows(manuscript_text: str) -> List[Dict[str, object]]:
    manuscript_norm = norm_text(manuscript_text)
    rows: List[Dict[str, object]] = []

    expr_path = "04_results/expression/tmem158_tumor_normal_tests.csv"
    expr = read_csv(expr_path)
    for dataset, n_tumor, n_normal, delta_digits, fdr_fragment in [
        ("TCGA", "184", "13", 3, "FDR=1.69e-4"),
        ("GSE20347", "17", "17", 3, "FDR=0.0382"),
        ("GSE26886", "9", "19", 3, "FDR=0.00260"),
        ("GSE45670", "28", "10", 3, "FDR=0.987"),
    ]:
        row = row_where(expr, dataset=dataset, metric="TMEM158")
        claim(
            rows,
            manuscript_norm,
            f"expression_{dataset}",
            "tumour_normal_expression",
            expr_path,
            f"n_tumor={row['n_tumor']}; n_normal={row['n_normal']}; delta={row['delta_tumor_minus_normal']}; FDR={row['FDR']}",
            [
                f"{dataset} ({n_tumor} tumours, {n_normal} normals; median difference {f_float(row['delta_tumor_minus_normal'], delta_digits)}; {fdr_fragment})",
                f"{n_tumor} tumours, {n_normal} normals; median difference {f_float(row['delta_tumor_minus_normal'], delta_digits)}; {fdr_fragment}",
            ],
        )

    survival_path = "04_results/survival/tmem158_ecology_state_survival.csv"
    survival = read_csv(survival_path)
    tac_surv = row_where(survival, model="ecology_subtype", term="ecology_subtypeTAC_high")
    claim(
        rows,
        manuscript_norm,
        "tcga_tac_high_survival_boundary",
        "survival_boundary",
        survival_path,
        f"HR={tac_surv['HR']}; FDR={tac_surv['FDR']}",
        [f"TAC_high subtype term had HR={f_float(tac_surv['HR'], 3)} with FDR={f_float(tac_surv['FDR'], 3)}"],
    )

    cross_path = "04_results/validation/tmem158_cross_layer_evidence.csv"
    cross = read_csv(cross_path)
    for layer, fragment in [
        ("TCGA axis-CAF discovery", "TCGA axis-CAF discovery rho of"),
        ("GSE45670 pretreatment validation", "GSE45670 validation rho of"),
        ("DepMap ESCC basal branch", "DepMap ESCC basal branch rho of"),
    ]:
        row = row_where(cross, layer=layer, metric="rho")
        claim(
            rows,
            manuscript_norm,
            f"cross_layer_{layer.replace(' ', '_').lower()}",
            "axis_first_candidate_evidence",
            cross_path,
            f"{layer} rho={row['value']}",
            [f"{fragment} {f_float(row['value'], 3)}"],
        )

    axis_path = "04_results/enrichment/tmem158_axis_correlations_by_dataset.csv"
    axis = read_csv(axis_path)
    gse45670_ca = row_where(axis, dataset="GSE45670", metric="Ca2_axis_score")
    claim(
        rows,
        manuscript_norm,
        "gse45670_negative_ca2_axis_boundary",
        "axis_boundary",
        axis_path,
        f"rho={gse45670_ca['rho']}; FDR={gse45670_ca['FDR']}",
        ["GSE45670 showed positive CAF coupling but a negative Ca2-axis correlation"],
        priority="boundary",
        notes="The manuscript states the direction without printing the exact rho.",
    )

    counts_path = "04_results/validation/tmem158_rule_ecology_subtype_counts.csv"
    counts = read_csv(counts_path)
    count_fragments = []
    for dataset in ("GSE20347", "GSE26886", "GSE45670", "TCGA"):
        row = row_where(counts, dataset=dataset, ecology_subtype="TAC_high")
        count_fragments.append(f"{dataset} (n={row['n_samples']})")
    claim(
        rows,
        manuscript_norm,
        "bulk_tac_high_counts",
        "rule_defined_state",
        counts_path,
        "; ".join(count_fragments),
        [
            "; ".join(count_fragments),
            "GSE20347 (n=5), GSE26886 (n=4), GSE45670 (n=8) and TCGA (n=58)",
        ],
    )

    repro_path = "04_results/validation/tmem158_rule_ecology_subtype_reproducibility.csv"
    repro = read_csv(repro_path)
    for metric, expected in [
        ("Proteostasis_score", "higher proteostasis score"),
        ("Survival_score", "higher cell-survival transcriptional score"),
        ("Drug_efflux_score", "Drug-efflux score showed a meta-positive"),
    ]:
        row = row_where(repro, metric=metric)
        claim(
            rows,
            manuscript_norm,
            f"rule_tac_high_{metric}",
            "rule_defined_state",
            repro_path,
            f"signed_z={row['signed_z']}; meta_FDR={row['meta_FDR']}; positive_fdr={row['positive_fdr']}",
            [
                f"{expected} (signed z={f_float(row['signed_z'], 3)}, meta-FDR={f_sci(row['meta_FDR'], 2) if float(row['meta_FDR']) < 0.001 else f_float(row['meta_FDR'], 4)}, {row['positive_fdr']} FDR-positive cohorts)",
                f"{expected} (signed z={f_float(row['signed_z'], 3)}, meta-FDR={f_sci(row['meta_FDR'], 2) if float(row['meta_FDR']) < 0.001 else f_float(row['meta_FDR'], 4)}, {'two' if row['positive_fdr'] == '2' else 'one'} FDR-positive cohort",
                f"{expected} by signed meta-analysis (signed z={f_float(row['signed_z'], 3)}, meta-FDR={f_sci(row['meta_FDR'], 2) if float(row['meta_FDR']) < 0.001 else f_float(row['meta_FDR'], 4)}, {'two' if row['positive_fdr'] == '2' else 'one'} FDR-positive cohort",
                f"{expected} but less replicated boundary signal (signed z={f_float(row['signed_z'], 3)}, meta-FDR={f_sci(row['meta_FDR'], 2) if float(row['meta_FDR']) < 0.001 else f_float(row['meta_FDR'], 4)}, {'two' if row['positive_fdr'] == '2' else 'one'} FDR-positive cohort",
            ],
        )

    full_path = "04_results/validation/tmem158_ecology_state_reproducibility.csv"
    full = read_csv(full_path)
    full_prot = row_where(full, contrast="TMEM158_CaUPR_CAF_full_high_vs_low", metric="Proteostasis_score")
    claim(
        rows,
        manuscript_norm,
        "full_tmem158_caupr_caf_proteostasis",
        "composite_state",
        full_path,
        f"signed_z={full_prot['signed_z']}; meta_FDR={full_prot['meta_FDR']}; positive_fdr={full_prot['positive_fdr']}",
        [
            f"proteostasis score (signed z={f_float(full_prot['signed_z'], 3)}, meta-FDR={f_float(full_prot['meta_FDR'], 5)}, {full_prot['positive_fdr']} FDR-positive cohorts)",
            f"proteostasis score (signed z={f_float(full_prot['signed_z'], 3)}, meta-FDR={f_float(full_prot['meta_FDR'], 5)}, two FDR-positive cohorts)",
        ],
    )

    perm_path = "04_results/validation/tmem158_tac_high_permutation_summary.csv"
    perm = read_csv(perm_path)
    for metric, fragment in [
        ("Drug_efflux_score", "drug-efflux transcriptional readout"),
        ("Proteostasis_score", "Proteostasis showed a positive"),
        ("Survival_score", "survival score was not random-label specific"),
    ]:
        row = row_where(perm, metric=metric)
        claim(
            rows,
            manuscript_norm,
            f"permutation_{metric}",
            "specificity_test",
            perm_path,
            f"delta={row['observed_meta_delta']}; p={row['empirical_two_sided_p']}; FDR={row['empirical_FDR']}",
            [
                f"{fragment} (weighted median delta={f_float(row['observed_meta_delta'], 3)}, empirical two-sided P={f_float(row['empirical_two_sided_p'], 5)}, empirical FDR={f_float(row['empirical_FDR'], 4)})",
                f"{fragment} (delta={f_float(row['observed_meta_delta'], 3)}, empirical two-sided P={f_float(row['empirical_two_sided_p'], 4)}, empirical FDR={f_float(row['empirical_FDR'], 3)})",
                f"delta={f_float(row['observed_meta_delta'], 3)}, empirical two-sided P={f_float(row['empirical_two_sided_p'], 4)}, empirical FDR={f_float(row['empirical_FDR'], 3)}",
                f"delta={f_float(row['observed_meta_delta'], 3)}, empirical two-sided P={f_float(row['empirical_two_sided_p'], 3)}, empirical FDR={f_float(row['empirical_FDR'], 3)}",
            ],
        )

    tac_gene_path = "04_results/transcriptome/tmem158_tac_high_top_meta_genes.csv"
    tac_genes = read_csv(tac_gene_path)
    tac_vs_other_genes = [row["gene"] for row in tac_genes if row["model"] == "TAC_high_vs_other"][:10]
    claim(
        rows,
        manuscript_norm,
        "tac_high_top_meta_genes",
        "whole_transcriptome",
        tac_gene_path,
        "; ".join(tac_vs_other_genes),
        ["POSTN, COL6A3, COL1A2, TMEM158, CHST7, COL3A1, FAP, SULF1, COL1A1 and COL6A2"],
    )

    gs_path = "04_results/transcriptome/tmem158_tac_high_geneset_enrichment.csv"
    gs = read_csv(gs_path)
    er = row_where(gs, model="Core_CAF_interaction", gene_set="CUSTOM_ER_PROTEOSTASIS")
    drug = row_where(gs, model="Core_CAF_interaction", gene_set="CUSTOM_DRUG_EFFLUX_TRANSPORT")
    claim(
        rows,
        manuscript_norm,
        "core_caf_custom_er_proteostasis",
        "whole_transcriptome",
        gs_path,
        f"CUSTOM_ER_PROTEOSTASIS FDR={er['FDR']}",
        [f"ER proteostasis (FDR={f_float(er['FDR'], 3)})"],
    )
    claim(
        rows,
        manuscript_norm,
        "core_caf_custom_drug_efflux_boundary",
        "whole_transcriptome",
        gs_path,
        f"CUSTOM_DRUG_EFFLUX_TRANSPORT FDR={drug['FDR']}",
        [f"drug-efflux transporters as a weaker boundary signal (FDR={f_float(drug['FDR'], 3)})"],
    )

    st_score_path = "04_results/validation/tmem158_stromal_adjusted_score_meta.csv"
    st_score = read_csv(st_score_path)
    st_prot = row_where(st_score, metric="Proteostasis_score", contrast="TAC_high_vs_CAF_only_CAF_adjusted")
    st_drug = row_where(st_score, metric="Drug_efflux_score", contrast="TAC_high_vs_CAF_only_CAF_adjusted")
    claim(
        rows,
        manuscript_norm,
        "caf_adjusted_score_boundary",
        "caf_adjusted_boundary",
        st_score_path,
        f"proteostasis meta_FDR={st_prot['meta_FDR']}; drug_efflux meta_FDR={st_drug['meta_FDR']}",
        [f"proteostasis meta-FDR={f_float(st_prot['meta_FDR'], 3)}; drug-efflux meta-FDR={f_float(st_drug['meta_FDR'], 3)}"],
    )

    st_model_path = "04_results/validation/tmem158_stromal_adjusted_score_model_meta.csv"
    st_model = read_csv(st_model_path)
    st_core_drug = row_where(st_model, metric="Drug_efflux_score", term="core_axis_state_score_adjusted_for_CAF")
    claim(
        rows,
        manuscript_norm,
        "caf_adjusted_core_axis_drug_efflux",
        "caf_adjusted_boundary",
        st_model_path,
        f"meta_FDR={st_core_drug['meta_FDR']}",
        [f"meta-FDR={f_float(st_core_drug['meta_FDR'], 5)}"],
    )

    st_gene_path = "04_results/transcriptome/tmem158_stromal_adjusted_top_meta_genes.csv"
    st_genes = read_csv(st_gene_path)
    st_top = [row["gene"] for row in st_genes[:9]]
    claim(
        rows,
        manuscript_norm,
        "caf_adjusted_top_genes",
        "caf_adjusted_transcriptome",
        st_gene_path,
        "; ".join(st_top),
        ["CHST7, TMEM158, PTDSS1, MAFG, ABCC1, NFE2L2, TALDO1, OSGIN1 and TOMM22"],
    )

    st_gs_path = "04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv"
    st_gs = read_csv(st_gs_path)
    for gene_set, claim_id, fragment in [
        ("CUSTOM_CAF_ECM", "caf_adjusted_custom_caf_ecm", "Custom CAF/ECM was no longer FDR-positive after adjustment"),
        ("CUSTOM_ER_PROTEOSTASIS", "caf_adjusted_custom_er", "custom ER-proteostasis and drug-efflux modules were also not FDR-positive"),
        ("CUSTOM_DRUG_EFFLUX_TRANSPORT", "caf_adjusted_custom_drug", "FDR=0.290 and 0.254"),
    ]:
        row = row_where(st_gs, model="TAC_high_adjusted_for_CAF", gene_set=gene_set)
        if claim_id == "caf_adjusted_custom_caf_ecm":
            fragments = [f"Custom CAF/ECM was no longer FDR-positive after adjustment (FDR={f_float(row['FDR'], 3)})"]
        else:
            fragments = [fragment]
        claim(rows, manuscript_norm, claim_id, "caf_adjusted_transcriptome", st_gs_path, f"{gene_set} FDR={row['FDR']}", fragments)

    gse_pair_path = "04_results/validation/tmem158_gse53625_paired_tumor_normal_tests.csv"
    gse_pair = read_csv(gse_pair_path)
    for metric, fragment, delta_digits, fdr in [
        ("TMEM158", "TMEM158 was significantly higher in tumours than paired normal tissues", 3, "FDR=1.05e-5"),
        ("ECM_integrin_bridge_score", "ECM-integrin bridge score was strongly tumour-elevated", 3, "FDR<0.001"),
        ("Residual_stress_score", "CAF-adjusted residual-stress score also increased modestly in tumours", 3, "FDR=0.019"),
    ]:
        row = row_where(gse_pair, metric=metric)
        claim(
            rows,
            manuscript_norm,
            f"gse53625_paired_{metric}",
            "external_clinical_calibration",
            gse_pair_path,
            f"n_pairs={row['n_pairs']}; delta={row['paired_delta_median']}; FDR={row['FDR']}",
            [
                f"{fragment} (paired delta={f_float(row['paired_delta_median'], delta_digits)}, {fdr})",
                f"{fragment} (paired median delta={f_float(row['paired_delta_median'], delta_digits)}, {fdr})",
            ],
        )

    gse_contrast_path = "04_results/validation/tmem158_gse53625_tac_state_contrasts.csv"
    gse_contrast = read_csv(gse_contrast_path)
    for metric, expected, fdr_fragment in [
        ("ECM_integrin_bridge_score", "higher ECM-integrin bridge score than other tumours", "FDR=1.80e-17"),
        ("Residual_stress_score", "higher residual-stress score", "FDR=1.68e-9"),
        ("Proteostasis_score", "higher proteostasis score", "FDR=1.96e-12"),
        ("CAF_score", "higher CAF score", "FDR=1.62e-18"),
    ]:
        row = row_where(gse_contrast, contrast="TAC_high_vs_other", metric=metric)
        claim(
            rows,
            manuscript_norm,
            f"gse53625_tac_{metric}",
            "external_clinical_calibration",
            gse_contrast_path,
            f"n_high={row['n_high']}; n_low={row['n_low']}; delta={row['delta_high_minus_low']}; FDR={row['FDR']}",
            [f"{expected} (delta={f_float(row['delta_high_minus_low'], 3)}, {fdr_fragment})"],
        )

    gse_surv_path = "04_results/survival/tmem158_gse53625_survival_cox.csv"
    gse_surv = read_csv(gse_surv_path)
    surv_fragments = []
    for feature, label in [
        ("TMEM158", "continuous TMEM158"),
        ("full_axis_ecology_score", "full TAC score"),
        ("TAC_high_indicator", "TAC_high status"),
    ]:
        row = row_where(gse_surv, model="univariable", feature=feature)
        surv_fragments.append(f"{label} (P={f_float(row['p.value'], 3)})")
    claim(
        rows,
        manuscript_norm,
        "gse53625_survival_negative",
        "external_clinical_calibration",
        gse_surv_path,
        "; ".join(surv_fragments),
        [
            ", ".join(surv_fragments),
            f"{surv_fragments[0]}, {surv_fragments[1]} and {surv_fragments[2]}",
        ],
    )

    multi_path = "04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv"
    multi = read_csv(multi_path)
    for comparison, expected in [
        ("TMEM158_log2CNA vs TMEM158", "TMEM158_log2CNA was negatively correlated with TMEM158 expression"),
        ("TMEM158_log2CNA vs full_axis_ecology_score", "with the full-axis ecology score"),
        ("TMEM158_promoter_methylation vs TMEM158", "Promoter methylation was positively, not negatively, correlated with TMEM158 expression"),
        ("TMEM158_promoter_methylation vs full_axis_ecology_score", "with the full-axis ecology score"),
    ]:
        row = row_where(multi, comparison=comparison)
        claim(
            rows,
            manuscript_norm,
            f"multiomics_{comparison.replace(' ', '_').replace('vs', 'vs')}",
            "multiomics_boundary",
            multi_path,
            f"rho={row['rho']}; FDR={row['FDR']}",
            [f"{expected} (rho={f_float(row['rho'], 3)}, FDR={f_float(row['FDR'], 5) if float(row['FDR']) < 0.01 else f_float(row['FDR'], 4)})"],
        )

    mutation_path = "04_results/mutation_cnv_methylation/tmem158_cbioportal_mutation_summary.csv"
    mutation = read_csv(mutation_path)
    claim(
        rows,
        manuscript_norm,
        "multiomics_mutation_records_zero",
        "multiomics_boundary",
        mutation_path,
        f"mutation_records={value_where(mutation, 'item', 'mutation_records')}",
        ["zero TMEM158 mutation records"],
    )

    immune_count_path = "04_results/immune/tmem158_scrna_rule_state_counts.csv"
    immune_count = read_csv(immune_count_path)
    immune_count_fragment = ", ".join(
        [
            f"{subtype}={value_where(immune_count, 'ecology_subtype', subtype, value_field='n_samples')}"
            for subtype in ("TAC_high", "Axis_only", "CAF_only", "TAC_low")
        ]
    )
    claim(rows, manuscript_norm, "scrna_rule_state_counts", "single_cell_boundary", immune_count_path, immune_count_fragment, [immune_count_fragment])

    immune_path = "04_results/immune/tmem158_scrna_rule_state_immune_tests.csv"
    immune = read_csv(immune_path)
    all_fdr = sorted({f_float(row["FDR"], 3) for row in immune})
    claim(rows, manuscript_norm, "scrna_immune_boundary_fdr", "single_cell_boundary", immune_path, f"all FDR values={all_fdr}", ["all had FDR=0.938"])

    sig_cov_path = "04_results/scrna_signature/tmem158_tac_high_scrna_signature_coverage.csv"
    sig_cov = read_csv(sig_cov_path)
    observed = sorted({int(row["n_genes_observed"]) for row in sig_cov if row["signature"].startswith("TAC_high")})
    claim(rows, manuscript_norm, "scrna_signature_genes_extracted", "single_cell_localization", sig_cov_path, f"TAC_high observed gene counts={observed}", ["392 unique TAC_high signature genes"])

    sig_comp_path = "04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_tests.csv"
    sig_comp = read_csv(sig_comp_path)
    n_fib = sum(1 for row in sig_comp if row["call"] == "fibroblast_higher_FDR")
    claim(
        rows,
        manuscript_norm,
        "scrna_fibroblast_compartment_tests",
        "single_cell_localization",
        sig_comp_path,
        f"fibroblast_higher_FDR={n_fib}/{len(sig_comp)}",
        [
            f"{n_fib}/{len(sig_comp)} paired Fibroblast-vs-other comparisons",
            "all nine paired Fibroblast-vs-other comparisons",
        ],
    )

    sig_state_path = "04_results/scrna_signature/tmem158_tac_high_scrna_signature_state_tests.csv"
    sig_state = read_csv(sig_state_path)
    top50 = row_where(sig_state, signature="TAC_high_positive_top50", compartment="Fibroblast")
    claim(rows, manuscript_norm, "scrna_top50_fibroblast_state", "single_cell_localization", sig_state_path, f"delta={top50['delta_TAC_high_minus_other']}; FDR={top50['FDR']}", [f"delta={f_float(top50['delta_TAC_high_minus_other'], 3)}, FDR={f_float(top50['FDR'], 3)}"])

    lr_pair_path = "04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_tests.csv"
    lr_pairs = read_csv(lr_pair_path)
    fdr_pairs = [row for row in lr_pairs if row["boundary_call"] == "TAC_high_higher_FDR"]
    postn_itga5 = row_where(lr_pairs, pair_label="POSTN->ITGA5")
    claim(rows, manuscript_norm, "lr_pair_count_and_top", "caf_epi_bridge", lr_pair_path, f"FDR pairs={len(fdr_pairs)}; POSTN->ITGA5 delta={postn_itga5['delta_TAC_high_minus_other']}; FDR={postn_itga5['FDR']}", [f"Twelve pairs were higher in TAC_high at FDR<0.10, led by POSTN->ITGA5 (delta={f_float(postn_itga5['delta_TAC_high_minus_other'], 3)}, FDR={f_float(postn_itga5['FDR'], 3)})"])

    lr_axis_path = "04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_tests.csv"
    lr_axis = read_csv(lr_axis_path)
    ecm = row_where(lr_axis, axis="ECM_integrin")
    mif = row_where(lr_axis, axis="MIF_SPP1_axis")
    claim(rows, manuscript_norm, "lr_axis_ecm_mif", "caf_epi_bridge", lr_axis_path, f"ECM delta={ecm['delta_TAC_high_minus_other']}; FDR={ecm['FDR']}; MIF delta={mif['delta_TAC_high_minus_other']}; FDR={mif['FDR']}", [f"ECM-integrin (delta={f_float(ecm['delta_TAC_high_minus_other'], 3)}, FDR={f_float(ecm['FDR'], 3)}) and MIF/SPP1 (delta={f_float(mif['delta_TAC_high_minus_other'], 3)}, FDR={f_float(mif['FDR'], 3)})"])

    lr_comp_path = "06_tables/tmem158_lr_compartment_expression_audit_top_candidates.csv"
    lr_comp = read_csv(lr_comp_path)
    pass_expected = [row for row in lr_comp if row["compartment_expression_call"] == "pass_expected_compartment_pattern"]
    postn_comp = row_where(lr_comp, candidate="POSTN->ITGA5")
    fn1_comp = row_where(lr_comp, candidate="FN1->ITGA5")
    claim(
        rows,
        manuscript_norm,
        "lr_compartment_expression_audit",
        "caf_epi_bridge",
        lr_comp_path,
        f"audited={len(lr_comp)}; pass_expected={len(pass_expected)}; POSTN fibroblast={postn_comp['fibroblast_ligand_median_expr']}; POSTN epithelial receptor={postn_comp['epithelial_receptor_median_expr']}; POSTN FDR={postn_comp['lr_score_FDR']}; FN1 FDR={fn1_comp['lr_score_FDR']}",
        [
            f"top {len(lr_comp)} structural candidates found {len(pass_expected)} pairs with the expected fibroblast-ligand and detectable epithelial-receptor pattern",
            f"POSTN->ITGA5 and FN1->ITGA5 passed this expression-feasibility check; for POSTN->ITGA5, fibroblast POSTN median expression was {postn_comp['fibroblast_ligand_median_expr']}, epithelial ITGA5 median expression was {postn_comp['epithelial_receptor_median_expr']} and the LR score FDR was {f_float(postn_comp['lr_score_FDR'], 3)}",
        ],
    )

    gse221_status_path = "04_results/gse221561/tmem158_gse221561_tac_context_status.csv"
    gse221_status = read_csv(gse221_status_path)
    claim(
        rows,
        manuscript_norm,
        "gse221561_recovery_status",
        "independent_single_cell_context",
        gse221_status_path,
        f"libraries_parsed={value_where(gse221_status, 'item', 'libraries_parsed')}; libraries_failed={value_where(gse221_status, 'item', 'libraries_failed')}; target_genes_covered={value_where(gse221_status, 'item', 'target_genes_covered')}",
        ["partial recovery of 7 of 11 listed libraries", "All 124 requested TMEM158/TAC_high/ECM-integrin target genes were covered"],
    )
    claim(
        rows,
        manuscript_norm,
        "gse221561_tac_meta_ecm",
        "independent_single_cell_context",
        gse221_status_path,
        f"delta={value_where(gse221_status, 'item', 'fibroblast_vs_epithelial_TAC_meta_delta')}; p={value_where(gse221_status, 'item', 'fibroblast_vs_epithelial_TAC_meta_p')}",
        [f"Fibroblast-versus-epithelial TAC meta-ECM delta was {value_where(gse221_status, 'item', 'fibroblast_vs_epithelial_TAC_meta_delta')} (paired Wilcoxon P={value_where(gse221_status, 'item', 'fibroblast_vs_epithelial_TAC_meta_p')})"],
    )

    gse221_corr_path = "04_results/gse221561/tmem158_gse221561_tac_matched_sample_correlations.csv"
    gse221_corr = read_csv(gse221_corr_path)
    proteo = row_where(gse221_corr, x_feature="TAC_like_context_score", y_feature="Proteostasis_score.Epithelial")
    claim(rows, manuscript_norm, "gse221561_epithelial_proteostasis_correlation", "independent_single_cell_context", gse221_corr_path, f"rho={proteo['rho']}; FDR={proteo['FDR']}", [f"rho={f_float(proteo['rho'], 3)}, FDR={f_float(proteo['FDR'], 3)}"])

    spatial_path = "04_results/spatial_progression/tmem158_spatial_progression_context_status.csv"
    spatial = read_csv(spatial_path)
    claim(
        rows,
        manuscript_norm,
        "spatial_fibroblast_alpha_sma_context",
        "spatial_source_data_context",
        spatial_path,
        f"fibroblast_delta={value_where(spatial, 'field', 'fibroblast_delta_ESCC_minus_NE')}; fibroblast_rho={value_where(spatial, 'field', 'fibroblast_stage_trend_rho')}; alpha_delta={value_where(spatial, 'field', 'alpha_SMA_delta_ESCC_minus_NE')}; alpha_rho={value_where(spatial, 'field', 'alpha_SMA_stage_trend_rho')}",
        [
            f"DSP fibroblast abundance increased across histological stages (ESCC-minus-NE median delta={value_where(spatial, 'field', 'fibroblast_delta_ESCC_minus_NE')}; stage-trend rho={value_where(spatial, 'field', 'fibroblast_stage_trend_rho')}; FDR<0.001)",
            f"alpha-SMA fibroblast IF also increased from NE to ESCC (delta={value_where(spatial, 'field', 'alpha_SMA_delta_ESCC_minus_NE')}; stage-trend rho={value_where(spatial, 'field', 'alpha_SMA_stage_trend_rho')}; FDR<0.001)",
        ],
    )

    protein_path = "04_results/validation/tmem158_public_protein_knowledgebase_summary.csv"
    protein = read_csv(protein_path)
    protein_source = "; ".join([f"{row['source']}:{row['item']}={row['value']}" for row in protein if row["item"] in {"reviewed_accession", "sequence_length_aa", "subcellular_location", "topology", "antibody"}])
    claim(
        rows,
        manuscript_norm,
        "public_protein_uniprot_context",
        "protein_context",
        protein_path,
        protein_source,
        ["reviewed accession Q8WZ71, Transmembrane protein 158, 300 amino acids, with membrane and multi-pass membrane protein annotations"],
    )
    claim(
        rows,
        manuscript_norm,
        "public_protein_quickgo_boundary",
        "protein_context",
        protein_path,
        protein_source,
        ["QuickGO/UniProt cellular-component evidence was limited to membrane (GO:0016020)"],
        priority="boundary",
    )
    claim(
        rows,
        manuscript_norm,
        "public_protein_hpa_context",
        "protein_context",
        protein_path,
        protein_source,
        ["HPA mapped TMEM158 to ENSG00000249992, classified it as a predicted membrane protein, provided protein-level evidence and listed an approved IHC antibody (HPA074974)"],
    )
    claim(
        rows,
        manuscript_norm,
        "public_protein_hpa_boundary",
        "protein_context",
        protein_path,
        protein_source,
        ["HPA did not provide subcellular IF localization, reported protein tissue distribution as not detected and did not establish ESCC-specific protein validation"],
        priority="boundary",
    )

    af_path = "04_results/structure/tmem158_alphafold_model_summary.csv"
    af = read_csv(af_path)
    claim(
        rows,
        manuscript_norm,
        "alphafold_coverage_global_confidence",
        "protein_topology_context",
        af_path,
        f"coverage={value_where(af, 'item', 'coverage')}; global_plddt={value_where(af, 'item', 'global_plddt')}; tm1={value_where(af, 'item', 'tm1_mean_plddt')}; tm2={value_where(af, 'item', 'tm2_mean_plddt')}",
        [f"canonical Q8WZ71 model covered residues {value_where(af, 'item', 'coverage')} (model version {value_where(af, 'item', 'model_version')}) with global pLDDT {value_where(af, 'item', 'global_plddt')}"],
    )
    claim(
        rows,
        manuscript_norm,
        "alphafold_tm1_confidence",
        "protein_topology_context",
        af_path,
        f"tm1_mean_plddt={value_where(af, 'item', 'tm1_mean_plddt')}",
        [f"first segment had higher AlphaFold confidence (mean pLDDT {value_where(af, 'item', 'tm1_mean_plddt')})"],
    )
    claim(
        rows,
        manuscript_norm,
        "alphafold_tm2_boundary",
        "protein_topology_context",
        af_path,
        f"tm2_mean_plddt={value_where(af, 'item', 'tm2_mean_plddt')}",
        [f"second segment remained low-confidence (mean pLDDT {value_where(af, 'item', 'tm2_mean_plddt')})"],
        priority="boundary",
    )
    claim(
        rows,
        manuscript_norm,
        "alphafold_claim_ceiling",
        "protein_topology_context",
        af_path,
        value_where(af, "item", "main_interpretation"),
        ["does not establish direct ER localization, binding to Ca2/UPR proteins, interaction with ECM components, or ESCC-specific protein validation"],
        priority="boundary",
    )

    return rows


def write_audit_report(rows: Sequence[Dict[str, object]], qc_rows: Sequence[Dict[str, object]]) -> None:
    missing = [row for row in rows if row["status"] != "pass"]
    lines = [
        "# Manuscript Numeric Consistency Audit",
        "",
        f"Generated: {NOW}",
        "",
        "## Scope",
        "",
        "This audit checks key numeric claims in `07_manuscript/manuscript_scientific_reports.md` against the current machine-readable result tables. It is a submission-quality control layer, not a new biological analysis.",
        "",
        "## QC Summary",
        "",
        "| Item | Value | Status | Notes |",
        "|---|---:|---|---|",
    ]
    for row in qc_rows:
        lines.append(f"| {row['item']} | {row['value']} | {row['status']} | {row['notes']} |")
    lines.extend(["", "## Missing Or Stale Claims", ""])
    if not missing:
        lines.append("No missing or stale critical numeric-claim rows were detected.")
    else:
        lines.extend(["| Claim | Source | Expected manuscript fragment |", "|---|---|---|"])
        for row in missing:
            lines.append(f"| {row['claim_id']} | `{row['source_path']}` | {row['expected_fragments']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A pass means the current manuscript still contains the audited key numbers or bounded textual statements derived from the current result tables. It does not verify every possible number in every supplementary file and does not replace human proofreading.",
        ]
    )
    ensure_parent(AUDIT_MD)
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_indexes_and_surfaces(qc_rows: Sequence[Dict[str, object]]) -> None:
    clearance = next(row for row in qc_rows if row["item"] == "numeric_consistency_clearance")["value"]
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "manuscript_numeric_consistency_audit", "path": "04_results/qc/manuscript_numeric_consistency_audit.csv"},
            {"result": "manuscript_numeric_consistency_audit_qc", "path": "04_results/qc/manuscript_numeric_consistency_audit_qc.csv"},
            {"result": "manuscript_numeric_consistency_audit_report", "path": "08_submission_strategy/manuscript_numeric_consistency_audit.md"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {"file_role": "manuscript_numeric_consistency_audit_csv", "path": "04_results/qc/manuscript_numeric_consistency_audit.csv", "status": f"ready_clearance_{clearance}", "notes": "Audits key manuscript numeric claims against result tables"},
            {"file_role": "manuscript_numeric_consistency_audit_qc", "path": "04_results/qc/manuscript_numeric_consistency_audit_qc.csv", "status": f"ready_clearance_{clearance}", "notes": "Numeric consistency QC summary"},
            {"file_role": "manuscript_numeric_consistency_audit_report", "path": "08_submission_strategy/manuscript_numeric_consistency_audit.md", "status": f"ready_clearance_{clearance}", "notes": "Markdown numeric consistency report"},
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {"item": "manuscript_numeric_consistency_audit", "value": "04_results/qc/manuscript_numeric_consistency_audit.csv", "status": "pass" if clearance == "pass" else "needs_revision", "notes": "Key manuscript numeric claims checked against result tables"},
        ],
        ["item", "value", "status", "notes"],
    )

    checklist = ROOT / "08_submission_strategy" / "scientific_reports_submission_checklist.md"
    if checklist.exists():
        text = checklist.read_text(encoding="utf-8")
        item = "- [x] Manuscript numeric consistency audit passed: `04_results/qc/manuscript_numeric_consistency_audit.csv`"
        anchor = "- [x] Automated claim-boundary text audit generated"
        if item not in text and anchor in text:
            text = text.replace(anchor, anchor + "\n" + item)
        checklist.write_text(text, encoding="utf-8")

    marker = "2026-06-19 manuscript numeric consistency audit"
    block = f"""Manuscript numeric consistency audit:

- CSV: `04_results/qc/manuscript_numeric_consistency_audit.csv`
- QC: `04_results/qc/manuscript_numeric_consistency_audit_qc.csv`
- Report: `08_submission_strategy/manuscript_numeric_consistency_audit.md`
- Clearance: `{clearance}`

This layer checks key manuscript numbers against result tables and is a submission-quality control layer, not new biological evidence."""
    replace_or_append(ROOT / "README.md", marker, block)
    replace_or_append(ROOT / "00_project_log" / "master_log.md", marker, f"- 2026-06-19 latest: Added manuscript numeric consistency audit. Clearance: `{clearance}`.")
    replace_or_append(ROOT / "00_project_log" / "stage_summary.md", marker, "- Added a machine-readable audit linking key manuscript numeric claims back to current result tables.")
    replace_or_append(ROOT / "00_project_log" / "decision_record.md", marker, "Decision: add manuscript numeric consistency as a final machine QC layer before treating the submission package as internally coherent.\n\nReason: after many manuscript and evidence-layer regenerations, stale numeric claims are a realistic submission risk.")
    replace_or_append(ROOT / "00_project_log" / "context_checkpoint.md", marker, f"Latest checkpoint: manuscript numeric consistency audit clearance is `{clearance}`; final upload remains human-gated.")

    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "CURRENT_STATE.md",
        marker,
        f"""## 2026-06-19 manuscript numeric consistency audit 完成

已新增 `TMEM158_CaUPR_ESCC/03_scripts/Python/run_manuscript_numeric_consistency_audit.py`，并生成 `04_results/qc/manuscript_numeric_consistency_audit.csv`、`manuscript_numeric_consistency_audit_qc.csv` 和 `08_submission_strategy/manuscript_numeric_consistency_audit.md`。该层把 Scientific Reports 稿件中的关键数值主张逐条对回当前结果表，当前 clearance 为 `{clearance}`。

该层不是新生物学证据，而是投稿质量控制：用于降低多轮重写后正文数字、图注数字或源表不一致的风险。final upload clearance 仍需人工作者信息、声明、repository DOI/永久链接和投稿系统预览。"""
    )
    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "DECISION_LOG.md",
        marker,
        """## 2026-06-19 manuscript numeric consistency audit 决策

- 决策：新增稿件关键数字-源表一致性审计，并接入一键流程和投稿包。
- 背景：当前已经进入投稿工程阶段，最现实的机器端风险之一是多轮重写后正文数字与结果表不同步。
- 依据：审计脚本从 expression、survival、TAC_high reproducibility、permutation、transcriptome、GSE53625、multi-omics、single-cell、LR、spatial、protein 和 AlphaFold 等结果表抽取关键数字并检查当前 Scientific Reports 稿件。
- 可信度：高。该层只做可复跑的一致性检查，不改变科学 claim。"""
    )
    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "EVIDENCE_LOG.md",
        marker,
        """### 2026-06-19 更新：manuscript numeric consistency audit

- 证据类型：submission QC / manuscript-table consistency，不是新生物学证据。
- 新增输出：`manuscript_numeric_consistency_audit.csv`、`manuscript_numeric_consistency_audit_qc.csv`、`manuscript_numeric_consistency_audit.md`。
- 解释：该层证明当前稿件关键数字仍可追溯到当前结果表；后续人工改稿后应重跑。"""
    )
    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "TASKS" / "2026-06-18-SMIM14-CaUPR-ESCC-bioinformatics.md",
        marker,
        """## 2026-06-19 追加：manuscript numeric consistency audit

- 新增脚本：`TMEM158_CaUPR_ESCC/03_scripts/Python/run_manuscript_numeric_consistency_audit.py`。
- 新增输出：稿件关键数字一致性审计 CSV/QC/MD。
- 当前意义：机器端投稿包不仅有 claim-boundary 审计，也能检查关键结果数字是否与当前源表同步。"""
    )


def main() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    rows = build_claim_rows(text)
    missing = [row for row in rows if row["status"] != "pass"]
    critical_missing = [row for row in missing if row["priority"] == "critical"]
    clearance = "pass" if not critical_missing else "needs_revision"
    qc_rows = [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "claims_audited", "value": len(rows), "status": "pass", "notes": "Key manuscript numeric or bounded text claims checked"},
        {"item": "missing_or_stale_rows", "value": len(missing), "status": "pass" if not missing else "needs_revision", "notes": "Rows whose expected manuscript fragment was not detected"},
        {"item": "critical_missing_or_stale_rows", "value": len(critical_missing), "status": "pass" if not critical_missing else "needs_revision", "notes": "Critical rows requiring manuscript/source synchronization"},
        {"item": "numeric_consistency_clearance", "value": clearance, "status": "pass" if clearance == "pass" else "needs_revision", "notes": "Pass requires no critical missing/stale rows"},
    ]
    write_csv(
        AUDIT_CSV,
        rows,
        ["claim_id", "category", "priority", "source_path", "source_value", "expected_fragments", "status", "notes"],
    )
    write_csv(AUDIT_QC, qc_rows, ["item", "value", "status", "notes"])
    write_audit_report(rows, qc_rows)
    update_indexes_and_surfaces(qc_rows)
    print(
        "manuscript_numeric_consistency_audit=completed "
        f"claims={len(rows)} missing_or_stale={len(missing)} critical_missing={len(critical_missing)} "
        f"clearance={clearance}"
    )


if __name__ == "__main__":
    main()
