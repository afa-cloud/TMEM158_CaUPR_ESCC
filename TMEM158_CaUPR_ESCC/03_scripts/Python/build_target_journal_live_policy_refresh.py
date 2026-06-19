#!/usr/bin/env python3
"""Write a dated live target-journal policy refresh report.

This script records the official-policy conclusions checked online during the
2026-06-19 Codex run. It does not fetch web pages itself; the URLs and source
line notes are retained so the author can manually re-check them before final
submission.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
REPORT = ROOT / "08_submission_strategy" / "target_journal_live_policy_refresh.md"
TABLE = ROOT / "08_submission_strategy" / "target_journal_live_policy_refresh.csv"
QC = ROOT / "04_results" / "qc" / "target_journal_live_policy_refresh_qc.csv"
PUBLIC_REPOSITORY_URL = "https://github.com/afa-cloud/TMEM158_CaUPR_ESCC"


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


def policy_rows() -> List[Dict[str, object]]:
    return [
        {
            "journal_or_policy": "Scientific Reports",
            "official_source": "https://www.nature.com/srep/author-instructions/submission-guidelines",
            "source_note": "Article format recommends <=11 typeset pages, main text <=4500 words, title <=20 words, abstract <=200 words; abstract should not contain references; up to 6 keywords are allowed.",
            "project_status": "pass",
            "project_evidence": "scientific_reports_format_qc.csv: title_words=15, abstract_words=172, keywords=6, main_text_words=3019, citation audit confirms abstract_reference_pattern=none.",
            "action_needed": "Keep current Scientific Reports first-pass target and retain concise abstract/title language.",
        },
        {
            "journal_or_policy": "Scientific Reports",
            "official_source": "https://www.nature.com/srep/author-instructions/submission-guidelines",
            "source_note": "Manuscript should include author affiliations/contact information; LLM use should be documented; author contribution and competing-interest statements are required.",
            "project_status": "ready_author_confirmed",
            "project_evidence": "human_submission_metadata_template.md, manuscript_scientific_reports.md and scientific_reports_submission_system_fields.csv contain author metadata, author contributions, competing interests, funding, acknowledgements and AI-tool disclosure.",
            "action_needed": "Keep these declarations unchanged unless the authors revise them before upload.",
        },
        {
            "journal_or_policy": "Scientific Reports",
            "official_source": "https://www.nature.com/srep/author-instructions/submission-guidelines",
            "source_note": "Data Availability Statement is mandatory and should be located at the end of the main text before References.",
            "project_status": "pass_public_repository",
            "project_evidence": f"manuscript_scientific_reports.md contains Data availability and Code availability sections; public GitHub repository is available at {PUBLIC_REPOSITORY_URL}.",
            "action_needed": "Use the GitHub repository URL in submission fields; mint DOI only if later requested.",
        },
        {
            "journal_or_policy": "Scientific Reports / Springer Nature data policy",
            "official_source": "https://www.nature.com/srep/journal-policies/editorial-policies",
            "source_note": "Data statements should include accession codes, identifiers, links and conditions for access; data and associated protocols should be available to readers and reviewers.",
            "project_status": "pass_public_repository",
            "project_evidence": f"source_data_and_supplementary_inventory.csv, repository_release_package_manifest.csv and repository checksums are present; code/output deposition is public at {PUBLIC_REPOSITORY_URL}.",
            "action_needed": "Keep repository release package available for later DOI-minted archival release if requested.",
        },
        {
            "journal_or_policy": "Springer Nature data availability statements",
            "official_source": "https://www.springernature.com/gp/authors/research-data-policy/data-availability-statements",
            "source_note": "Data availability statements should tell readers how to access supporting data; repository data should include hyperlinks and persistent identifiers; secondary data sources should be included.",
            "project_status": "pass_public_repository",
            "project_evidence": f"Repository release package and source-data inventory are prepared; TCGA/GEO/cBioPortal/UniProt/QuickGO/HPA/AlphaFold sources are cited in manuscript and inventories; public GitHub repository is available at {PUBLIC_REPOSITORY_URL}.",
            "action_needed": "Use the GitHub repository URL unless a DOI-minted archival release is later required.",
        },
        {
            "journal_or_policy": "BMC Cancer",
            "official_source": "https://link.springer.com/journal/12885/submission-guidelines/research-article",
            "source_note": "BMC Cancer research-article guidance states that manuscripts consisting solely of bioinformatics/computational analysis/public-database prediction without validation will not be considered.",
            "project_status": "high_risk_not_first_target",
            "project_evidence": "This project is deliberately pure public-data and lacks wet-lab biological validation.",
            "action_needed": "Do not use BMC Cancer as first target unless wet-lab validation is added.",
        },
        {
            "journal_or_policy": "BMC Cancer",
            "official_source": "https://link.springer.com/journal/12885/aims-and-scope",
            "source_note": "BMC Cancer scope includes computational biology/systems biology, but diagnostic/prognostic biomarker submissions should include independent validation and biological validation in vitro or in vivo.",
            "project_status": "high_risk_not_first_target",
            "project_evidence": "Current manuscript is not framed as a clinically validated biomarker and has no in vitro/in vivo validation.",
            "action_needed": "Preserve Scientific Reports route; keep BMC Cancer as no-go unless validation is added.",
        },
    ]


def write_report(rows: Sequence[Dict[str, object]]) -> None:
    lines = [
        "# Target Journal Live Policy Refresh",
        "",
        f"Generated: {NOW}",
        "",
        "## Decision",
        "",
        "Scientific Reports remains the more suitable first-pass target for the current pure-public-data, hypothesis-generating TMEM158/TAC_high manuscript. BMC Cancer remains high risk and should not be the first target without wet-lab biological validation.",
        "",
        "## Evidence Table",
        "",
        "| Journal/Policy | Project Status | Official Source | Source Note | Action Needed |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['journal_or_policy']} | {row['project_status']} | {row['official_source']} | {row['source_note']} | {row['action_needed']} |"
        )
    lines.extend(
        [
            "",
            "## Project Implication",
            "",
            "- Keep the manuscript framed as a public-data biological discovery candidate, not a validated prognostic/diagnostic biomarker.",
            "- Keep Scientific Reports as the first-pass formatted target.",
            "- Do not switch to BMC Cancer unless wet-lab biological validation is added.",
            f"- Author metadata and declarations are supplied; public GitHub repository deposition is complete at {PUBLIC_REPOSITORY_URL}.",
            "- The remaining non-machine upload items are publisher upload preview and final claim-boundary read.",
            "",
            "## Boundary",
            "",
            "This policy refresh does not add biological evidence and does not guarantee acceptance. It only checks whether the current submission route remains defensible against official target-journal policy.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_indexes() -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "target_journal_live_policy_refresh", "path": "08_submission_strategy/target_journal_live_policy_refresh.md"},
            {"result": "target_journal_live_policy_refresh_table", "path": "08_submission_strategy/target_journal_live_policy_refresh.csv"},
            {"result": "target_journal_live_policy_refresh_qc", "path": "04_results/qc/target_journal_live_policy_refresh_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {
                "file_role": "target_journal_live_policy_refresh",
                "path": "08_submission_strategy/target_journal_live_policy_refresh.md",
                "status": "ready_not_final_upload_clear",
                "notes": "Dated live official-policy refresh for Scientific Reports and BMC Cancer target decision",
            },
            {
                "file_role": "target_journal_live_policy_refresh_qc",
                "path": "04_results/qc/target_journal_live_policy_refresh_qc.csv",
                "status": "ready_not_final_upload_clear",
                "notes": "QC summary for target-journal policy refresh",
            },
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {
                "item": "target_journal_live_policy_refresh",
                "value": "08_submission_strategy/target_journal_live_policy_refresh.md",
                "status": "pass_human_gated_items_visible",
                "notes": "Scientific Reports remains defensible as first target; BMC Cancer remains high risk without wet-lab validation",
            }
        ],
        ["item", "value", "status", "notes"],
    )


def main() -> None:
    rows = policy_rows()
    write_csv(
        TABLE,
        rows,
        ["journal_or_policy", "official_source", "source_note", "project_status", "project_evidence", "action_needed"],
    )
    write_report(rows)
    qc_rows = [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "official_sources_checked", "value": 5, "status": "pass", "notes": "Scientific Reports, Springer Nature data policy and BMC Cancer official pages"},
        {"item": "scientific_reports_first_target_status", "value": "defensible", "status": "pass", "notes": "Article format and declaration/data requirements match current package; final preview remains human-gated"},
        {"item": "bmc_cancer_first_target_status", "value": "not_recommended_without_wet_lab_validation", "status": "pass", "notes": "Official pages reject public-database-only bioinformatics without validation"},
        {"item": "machine_policy_refresh_clearance", "value": "pass", "status": "pass", "notes": "No machine-side change to target journal strategy required"},
        {"item": "final_target_journal_clearance", "value": "not_yet", "status": "not_yet", "notes": "Final submission still requires publisher upload preview and final claim-boundary read"},
    ]
    write_csv(QC, qc_rows, ["item", "value", "status", "notes"])
    update_indexes()
    print("target_journal_live_policy_refresh=completed official_sources_checked=5 machine_policy_refresh_clearance=pass")


if __name__ == "__main__":
    main()
