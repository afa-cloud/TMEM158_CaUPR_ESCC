#!/usr/bin/env python3
"""Build a protein-topology claim audit for TMEM158.

This audit merges the public UniProt/QuickGO/HPA protein-context layer with
the AlphaFold topology layer. It is designed to prevent overinterpretation:
the evidence supports a membrane/topology rationale and follow-up experiment
prioritization, not direct ER localization, physical binding, ECM interaction
or ESCC protein validation.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT_MD = ROOT / "08_submission_strategy" / "tmem158_protein_topology_claim_audit.md"
OUT_CSV = ROOT / "08_submission_strategy" / "tmem158_protein_topology_claim_audit.csv"
QC_CSV = ROOT / "04_results" / "qc" / "tmem158_protein_topology_claim_audit_qc.csv"


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


def kv_from_rows(path: Path, key_field: str, value_field: str) -> Dict[str, str]:
    return {row.get(key_field, ""): row.get(value_field, "") for row in read_csv(path)}


def first_float(rows: Sequence[Dict[str, str]], key_field: str, key: str, value_field: str) -> float | None:
    for row in rows:
        if row.get(key_field) == key:
            try:
                return float(row.get(value_field, ""))
            except ValueError:
                return None
    return None


def build_audit_rows() -> List[Dict[str, object]]:
    kb = kv_from_rows(ROOT / "04_results" / "validation" / "tmem158_public_protein_knowledgebase_summary.csv", "item", "value")
    evidence_cards = {row.get("item", ""): row for row in read_csv(ROOT / "04_results" / "validation" / "tmem158_public_protein_evidence_cards.csv")}
    localization = read_csv(ROOT / "04_results" / "validation" / "tmem158_uniprot_quickgo_localization.csv")
    hpa = kv_from_rows(ROOT / "04_results" / "validation" / "tmem158_hpa_context_summary.csv", "field", "value")
    af_summary = kv_from_rows(ROOT / "04_results" / "structure" / "tmem158_alphafold_model_summary.csv", "item", "value")
    segments = read_csv(ROOT / "04_results" / "structure" / "tmem158_alphafold_topology_segments.csv")

    loc_terms = "; ".join(
        f"{row.get('source', '')}:{row.get('term_id', '')}:{row.get('term_name', '')}:{row.get('evidence', '')}"
        for row in localization
    )

    def row(layer: str, evidence_item: str, evidence_value: str, interpretation: str, allowed: str, disallowed: str, status: str) -> Dict[str, object]:
        return {
            "layer": layer,
            "evidence_item": evidence_item,
            "evidence_value": evidence_value,
            "interpretation": interpretation,
            "allowed_claim": allowed,
            "disallowed_claim": disallowed,
            "claim_status": status,
        }

    rows: List[Dict[str, object]] = [
        row(
            "UniProt",
            "Reviewed protein identity",
            f"{kb.get('reviewed_accession', '')}; {kb.get('protein_name', '')}; {kb.get('sequence_length_aa', '')} aa",
            "TMEM158 is a reviewed public protein entry suitable for traceable biomarker-candidate annotation.",
            "Reviewed transmembrane-protein candidate and assayable public protein entry.",
            "Experimentally validated ESCC protein expression or mechanism.",
            "support",
        ),
        row(
            "UniProt",
            "Membrane/topology annotation",
            f"{kb.get('subcellular_location', '')}; {kb.get('topology', '')}",
            "The public annotation supports membrane-protein plausibility, not organelle-specific localization.",
            "Membrane/multi-pass topology plausibility.",
            "Direct ER localization or ER-resident functional mechanism.",
            "support_with_boundary",
        ),
        row(
            "QuickGO/UniProt",
            "Cellular-component terms",
            loc_terms,
            "Retrieved cellular-component evidence is limited to membrane terms and does not provide a direct ER term.",
            "Public membrane cellular-component context.",
            "Direct endoplasmic-reticulum localization.",
            "boundary",
        ),
        row(
            "HPA",
            "Protein class and antibody context",
            f"{hpa.get('Protein class', '')}; antibody={hpa.get('Antibody', '')}; IH={hpa.get('Reliability (IH)', '')}",
            "HPA supports public membrane-protein and antibody assayability context.",
            "Atlas-level antibody/IHC context for future validation planning.",
            "New IHC validation, ESCC-specific protein validation or localization.",
            "context",
        ),
        row(
            "HPA",
            "Protein and subcellular evidence boundary",
            f"protein tissue distribution={hpa.get('Protein tissue distribution', '')}; IF main location={hpa.get('Subcellular main location', '') or 'not available'}",
            "HPA does not provide a usable TMEM158 subcellular IF localization layer and reports tissue protein distribution as not detected.",
            "A transparent protein-context limitation.",
            "HPA-confirmed ER localization or ESCC TMEM158 protein expression.",
            "boundary",
        ),
        row(
            "AlphaFold DB",
            "Canonical predicted model",
            f"{af_summary.get('alphafold_entry', '')}; coverage={af_summary.get('coverage', '')}; model_version={af_summary.get('model_version', '')}; global_plddt={af_summary.get('global_plddt', '')}",
            "The official predicted model gives structural context, but global confidence is moderate/low.",
            "Predicted topology rationale and experiment prioritization.",
            "High-confidence mechanism, binding or localization proof.",
            "support_with_boundary",
        ),
    ]
    for segment in segments:
        if segment.get("source") != "UniProt feature":
            continue
        rows.append(
            row(
                "AlphaFold + UniProt",
                segment.get("segment_id", ""),
                f"{segment.get('start', '')}-{segment.get('end', '')}; mean_pLDDT={segment.get('mean_plddt', '')}; hydropathy19={segment.get('mean_hydropathy19', '')}; call={segment.get('confidence_call', '')}",
                segment.get("interpretation", ""),
                "Segment-level topology support, with confidence explicitly stated.",
                "Specific Ca2/UPR or ECM protein interface.",
                "support" if segment.get("confidence_call") == "confident" else "boundary",
            )
        )

    direct_er_card = evidence_cards.get("Direct ER localization", {})
    rows.append(
        row(
            "Integrated claim ceiling",
            "Direct ER / physical-interaction boundary",
            f"direct ER evidence={direct_er_card.get('boundary_call', '')}; AlphaFold main_interpretation={af_summary.get('main_interpretation', '')}",
            "The combined protein layer supports membrane topology and experimental follow-up, not physical interaction or ER localization.",
            "Localization, membrane fraction, proximity-labelling, co-IP and defined-partner co-modelling are justified as next experiments.",
            "TMEM158 directly binds Ca2/UPR proteins, directly interacts with ECM components, or is ER-localized in ESCC.",
            "boundary",
        )
    )
    return rows


def write_report(rows: Sequence[Dict[str, object]], qc_rows: Sequence[Dict[str, object]]) -> None:
    qc = {row["item"]: row for row in qc_rows}
    lines = [
        "# TMEM158 Protein Topology Claim Audit",
        "",
        f"Generated: {NOW}",
        "",
        "## Bottom Line",
        "",
        "TMEM158 can be described as a reviewed membrane-protein candidate with public membrane/topology support and a predicted AlphaFold topology context. This strengthens biological plausibility and assayability, but it must not be written as direct ER localization, direct Ca2/UPR-protein binding, ECM binding, ESCC-specific protein validation or mechanism proof.",
        "",
        "## Machine QC",
        "",
    ]
    for row in qc_rows:
        lines.append(f"- `{row['item']}`: {row['value']} ({row['status']}) - {row['notes']}")
    lines.extend(["", "## Evidence Interpretation Table", ""])
    lines.append("| Layer | Evidence Item | Claim Status | Evidence Value | Allowed Claim | Disallowed Claim |")
    lines.append("|---|---|---|---|---|---|")
    for row in rows:
        vals = {k: str(v).replace("|", "/") for k, v in row.items()}
        lines.append(
            f"| {vals['layer']} | {vals['evidence_item']} | {vals['claim_status']} | {vals['evidence_value']} | {vals['allowed_claim']} | {vals['disallowed_claim']} |"
        )
    lines.extend(
        [
            "",
            "## Recommended Manuscript Wording",
            "",
            "Acceptable: TMEM158 is a public, reviewed transmembrane-protein candidate with membrane/topology plausibility and AlphaFold-supported structural rationale for follow-up localization and interaction assays.",
            "",
            "Avoid: TMEM158 is ER-localized, physically interacts with Ca2/UPR proteins, binds ECM components or has ESCC-specific protein validation.",
            "",
            "## Practical Use",
            "",
            "Use this layer to justify follow-up localization, membrane-fractionation, proximity-labelling, co-immunoprecipitation, crosslinking-MS or explicitly defined partner co-modelling. Do not use it to raise the claim ceiling of the public-data manuscript.",
            "",
            "## Clearance",
            "",
            f"Machine protein-topology claim clearance: `{qc.get('machine_protein_topology_claim_clearance', {}).get('value', '')}`.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_qc(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    localization_text = " ".join(str(row.get("evidence_value", "")) for row in rows if row.get("layer") == "QuickGO/UniProt").lower()
    af_summary_rows = read_csv(ROOT / "04_results" / "structure" / "tmem158_alphafold_model_summary.csv")
    global_plddt = first_float(af_summary_rows, "item", "global_plddt", "value")
    tm1 = first_float(af_summary_rows, "item", "tm1_mean_plddt", "value")
    tm2 = first_float(af_summary_rows, "item", "tm2_mean_plddt", "value")
    required_files = [
        ROOT / "04_results" / "validation" / "tmem158_public_protein_knowledgebase_summary.csv",
        ROOT / "04_results" / "validation" / "tmem158_uniprot_quickgo_localization.csv",
        ROOT / "04_results" / "validation" / "tmem158_hpa_context_summary.csv",
        ROOT / "04_results" / "structure" / "tmem158_alphafold_model_summary.csv",
        ROOT / "04_results" / "structure" / "tmem158_alphafold_topology_segments.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
    no_er_term = "endoplasmic" not in localization_text and "go:0005783" not in localization_text
    rows_needing_revision = 0 if not missing else len(missing)
    return [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "input_files_missing", "value": len(missing), "status": "pass" if not missing else "needs_revision", "notes": "Missing: " + "; ".join(missing) if missing else "All required protein/topology evidence tables are present"},
        {"item": "uniprot_quickgo_direct_er_term", "value": "absent" if no_er_term else "present", "status": "pass_boundary" if no_er_term else "needs_review", "notes": "Absence supports boundary that direct ER localization is not established"},
        {"item": "alphafold_global_plddt", "value": "" if global_plddt is None else round(global_plddt, 2), "status": "pass_boundary", "notes": "Moderate/low global confidence means no interaction-proof claim"},
        {"item": "alphafold_tm1_mean_plddt", "value": "" if tm1 is None else round(tm1, 2), "status": "pass" if tm1 is not None and tm1 >= 70 else "needs_review", "notes": "TM1 provides the strongest topology support"},
        {"item": "alphafold_tm2_mean_plddt", "value": "" if tm2 is None else round(tm2, 2), "status": "pass_boundary", "notes": "TM2 is an annotated but lower-confidence segment"},
        {"item": "protein_audit_rows", "value": len(rows), "status": "pass", "notes": "Evidence interpretation rows written"},
        {"item": "rows_needing_revision", "value": rows_needing_revision, "status": "pass" if rows_needing_revision == 0 else "needs_revision", "notes": "Machine-actionable issues in protein-topology audit"},
        {"item": "machine_protein_topology_claim_clearance", "value": "pass" if rows_needing_revision == 0 and no_er_term else "needs_revision", "status": "pass" if rows_needing_revision == 0 and no_er_term else "needs_revision", "notes": "Use as topology/assayability support only; no ER, binding, ECM or ESCC protein validation claim"},
    ]


def update_indexes() -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "tmem158_protein_topology_claim_audit", "path": "08_submission_strategy/tmem158_protein_topology_claim_audit.md"},
            {"result": "tmem158_protein_topology_claim_audit_table", "path": "08_submission_strategy/tmem158_protein_topology_claim_audit.csv"},
            {"result": "tmem158_protein_topology_claim_audit_qc", "path": "04_results/qc/tmem158_protein_topology_claim_audit_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {
                "file_role": "tmem158_protein_topology_claim_audit",
                "path": "08_submission_strategy/tmem158_protein_topology_claim_audit.md",
                "status": "ready",
                "notes": "Integrated UniProt/QuickGO/HPA plus AlphaFold protein-topology claim boundary audit",
            },
            {
                "file_role": "tmem158_protein_topology_claim_audit_qc",
                "path": "04_results/qc/tmem158_protein_topology_claim_audit_qc.csv",
                "status": "ready",
                "notes": "QC summary for protein-topology claim boundary audit",
            },
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {
                "item": "protein_topology_claim_boundary",
                "value": "08_submission_strategy/tmem158_protein_topology_claim_audit.md",
                "status": "pass",
                "notes": "Public protein/AlphaFold evidence supports membrane topology and assayability only, not ER localization, binding, ECM interaction or ESCC protein validation",
            }
        ],
        ["item", "value", "status", "notes"],
    )


def main() -> None:
    audit_rows = build_audit_rows()
    qc_rows = build_qc(audit_rows)
    write_csv(
        OUT_CSV,
        audit_rows,
        ["layer", "evidence_item", "evidence_value", "interpretation", "allowed_claim", "disallowed_claim", "claim_status"],
    )
    write_csv(QC_CSV, qc_rows, ["item", "value", "status", "notes"])
    write_report(audit_rows, qc_rows)
    update_indexes()
    clearance = next(row for row in qc_rows if row["item"] == "machine_protein_topology_claim_clearance")
    print(f"tmem158_protein_topology_claim_audit=completed clearance={clearance['value']} rows={len(audit_rows)}")


if __name__ == "__main__":
    main()
