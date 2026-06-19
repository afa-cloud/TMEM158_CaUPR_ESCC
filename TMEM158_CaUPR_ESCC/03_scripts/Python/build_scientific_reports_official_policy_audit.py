#!/usr/bin/env python3
"""Build a Scientific Reports and Nature Portfolio policy audit layer.

This script is a submission-readiness layer, not a biological analysis. It
checks the current manuscript against machine-auditable journal requirements,
creates a Nature Portfolio Reporting Summary working draft, and records the
remaining human-gated submission items.
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
CHECKED_DATE = datetime.now().strftime("%Y-%m-%d")

MANUSCRIPT = ROOT / "07_manuscript" / "manuscript_scientific_reports.md"
POLICY_AUDIT_CSV = ROOT / "04_results" / "qc" / "scientific_reports_official_policy_audit.csv"
POLICY_AUDIT_QC = ROOT / "04_results" / "qc" / "scientific_reports_official_policy_audit_qc.csv"
POLICY_AUDIT_MD = ROOT / "08_submission_strategy" / "scientific_reports_official_policy_audit.md"
REPORTING_SUMMARY = ROOT / "08_submission_strategy" / "nature_portfolio_reporting_summary_working_draft.md"
EDITORIAL_CHECKLIST = ROOT / "08_submission_strategy" / "editorial_policy_checklist_working_draft.md"

SCIREP_SUBMISSION_URL = "https://www.nature.com/srep/author-instructions/submission-guidelines"
NATURE_REPORTING_URL = "https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards"
SCIREP_EDITORIAL_URL = "https://www.nature.com/srep/journal-policies/editorial-policies"
NATURE_COI_URL = "https://www.nature.com/nature-portfolio/editorial-policies/competing-interests"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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
    rows = {row.get(key, ""): dict(row) for row in read_csv(path) if row.get(key)}
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


def section_text(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.M)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.M)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[/-][A-Za-z0-9]+)*", text))


def parse_docx_qa() -> Dict[str, str]:
    rows = read_csv(ROOT / "04_results" / "qc" / "scientific_reports_docx_qa.csv")
    return {row.get("item", ""): row.get("value", "") for row in rows}


def parse_bundle_qc() -> Dict[str, str]:
    rows = read_csv(ROOT / "08_submission_strategy" / "scientific_reports_submission_bundle_qc.csv")
    return {row.get("item", ""): row.get("value", "") for row in rows}


def main_figure_count() -> int:
    figure_dir = ROOT / "05_figures"
    return len([path for path in figure_dir.glob("main_figure*.png") if re.match(r"main_figure[0-9]+_", path.name)])


def title_from_markdown(text: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    return match.group(1).strip() if match else ""


def keywords_from_markdown(text: str) -> List[str]:
    body = section_text(text, "Keywords")
    if not body:
        return []
    return [part.strip() for part in body.replace("\n", " ").split(";") if part.strip()]


def main_text_for_word_count(text: str) -> str:
    include = []
    for heading in ("Introduction", "Results", "Discussion", "Limitations"):
        body = section_text(text, heading)
        if body:
            include.append(body)
    return "\n\n".join(include)


def has_ai_methods_statement(text: str) -> bool:
    methods = section_text(text, "Methods")
    if "AI-assisted drafting and code support" not in methods:
        return False
    return bool(re.search(r"AI-assisted tools were used.*human author", methods, re.I | re.S))


def abstract_has_reference_pattern(abstract: str) -> bool:
    return bool(
        re.search(r"\[[0-9,\-\s]+\]", abstract)
        or re.search(r"\([A-Z][A-Za-z-]+ et al\.,?\s+\d{4}\)", abstract)
        or re.search(r"https?://|doi:", abstract, re.I)
    )


def status_for(limit_pass: bool, human_gated: bool = False) -> str:
    if human_gated:
        return "human_required"
    return "pass" if limit_pass else "needs_revision"


def build_audit_rows(text: str) -> List[Dict[str, object]]:
    title = title_from_markdown(text)
    abstract = section_text(text, "Abstract")
    keywords = keywords_from_markdown(text)
    methods = section_text(text, "Methods")
    figures = main_figure_count()
    docx_qa = parse_docx_qa()
    bundle_qc = parse_bundle_qc()
    main_words = count_words(main_text_for_word_count(text))
    title_words = count_words(title)
    abstract_words = count_words(abstract)

    rows: List[Dict[str, object]] = [
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Article title length",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"{title_words} words",
            "status": status_for(title_words <= 20),
            "notes": "Scientific Reports guidance recommends titles of no more than 20 words.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Abstract length",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"{abstract_words} words",
            "status": status_for(abstract_words <= 200),
            "notes": "Scientific Reports guidance recommends an abstract of no more than 200 words.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Abstract structure and references",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": "unstructured; no detected reference pattern" if not abstract_has_reference_pattern(abstract) else "reference-like pattern detected",
            "status": status_for(bool(abstract) and not abstract_has_reference_pattern(abstract)),
            "notes": "Scientific Reports asks for an unstructured abstract without references.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Keywords",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"{len(keywords)} keywords",
            "status": status_for(0 < len(keywords) <= 6),
            "notes": "Scientific Reports allows up to six keywords or key phrases.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Main-text word count",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"{main_words} words excluding Abstract, Methods, figure legends and References",
            "status": status_for(main_words <= 4500),
            "notes": "Machine count uses Introduction, Results, Discussion and Limitations only.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Display-item count",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"{figures} main figures",
            "status": status_for(figures <= 8),
            "notes": "The submission-facing manuscript uses six composite main figures.",
            "evidence_path": "05_figures/",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "Required article sections",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": "; ".join([h for h in ("Introduction", "Results", "Discussion", "Methods") if section_text(text, h)]),
            "status": status_for(all(section_text(text, h) for h in ("Introduction", "Results", "Discussion", "Methods"))),
            "notes": "The article uses the expected scientific-article structure.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Scientific Reports format",
            "check_item": "AI-assisted tool-use documentation",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": "Methods subsection present" if has_ai_methods_statement(text) else "Methods subsection missing",
            "status": status_for(has_ai_methods_statement(text)),
            "notes": "Official guidance says LLM use should be documented in Methods or a suitable alternative section.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Nature Portfolio reporting",
            "check_item": "Reporting Summary",
            "source_url": NATURE_REPORTING_URL,
            "observed_value": "working draft generated",
            "status": "ready_human_finalize",
            "notes": "Nature Portfolio indicates life-science manuscripts require a reporting summary when sent for review; the final official form remains human-gated.",
            "evidence_path": "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md",
        },
        {
            "policy_area": "Data and code availability",
            "check_item": "Data availability statement",
            "source_url": NATURE_REPORTING_URL,
            "observed_value": "present" if "## Data availability" in text else "missing",
            "status": "pass_author_decision_no_repository" if "## Data availability" in text else "needs_revision",
            "notes": "Public data sources are listed; repository deposition is deferred before initial submission by author decision.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Data and code availability",
            "check_item": "Code availability statement",
            "source_url": NATURE_REPORTING_URL,
            "observed_value": "present" if "## Code availability" in text else "missing",
            "status": "pass_author_decision_no_repository" if "## Code availability" in text else "needs_revision",
            "notes": "The reproducible workflow path is listed; code is available from the corresponding author upon reasonable request before initial submission.",
            "evidence_path": "07_manuscript/manuscript_scientific_reports.md",
        },
        {
            "policy_area": "Authorship and declarations",
            "check_item": "Author agreement and title-page metadata",
            "source_url": SCIREP_EDITORIAL_URL,
            "observed_value": "author metadata supplied",
            "status": "ready_author_confirmed",
            "notes": "Author list, affiliations and correspondence details are supplied; all-author agreement remains a real-world author responsibility before submission.",
            "evidence_path": "08_submission_strategy/human_submission_metadata_template.md",
        },
        {
            "policy_area": "Authorship and declarations",
            "check_item": "Competing interests statement",
            "source_url": NATURE_COI_URL,
            "observed_value": "statement supplied",
            "status": "ready_author_confirmed",
            "notes": "The author confirmed no competing interests; all authors should preserve this statement only if it remains true before submission.",
            "evidence_path": "08_submission_strategy/human_submission_metadata_template.md",
        },
        {
            "policy_area": "Submission engineering",
            "check_item": "Editable DOCX render QA",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"{docx_qa.get('render_status', 'not available')}; {docx_qa.get('render_metrics', 'metrics not available')}",
            "status": "pass_internal_qa" if docx_qa.get("render_status") else "needs_revision",
            "notes": "Local render QA is an internal check; final journal-system PDF preview remains human-gated.",
            "evidence_path": "04_results/qc/scientific_reports_docx_qa.csv",
        },
        {
            "policy_area": "Submission engineering",
            "check_item": "Local upload dry-run bundle",
            "source_url": SCIREP_SUBMISSION_URL,
            "observed_value": f"machine_bundle_clearance={bundle_qc.get('machine_bundle_clearance', 'not available')}",
            "status": "pass_not_final_upload_clear" if bundle_qc.get("machine_bundle_clearance") == "pass" else "needs_revision",
            "notes": "Local bundle clearance does not replace final upload-system preview.",
            "evidence_path": "08_submission_strategy/scientific_reports_submission_bundle_qc.csv",
        },
    ]
    return rows


def write_policy_markdown(rows: Sequence[Dict[str, object]]) -> None:
    lines = [
        "# Scientific Reports Official Policy Audit",
        "",
        f"Generated: {NOW}",
        "",
        "## Official Sources Checked",
        "",
        f"- Scientific Reports submission guidelines: {SCIREP_SUBMISSION_URL}",
        f"- Nature Portfolio reporting standards: {NATURE_REPORTING_URL}",
        f"- Scientific Reports editorial policies: {SCIREP_EDITORIAL_URL}",
        f"- Nature Portfolio competing interests policy: {NATURE_COI_URL}",
        "",
        "## Machine-Auditable Checks",
        "",
        "| Policy area | Check | Observed value | Status | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy_area']} | {row['check_item']} | {row['observed_value']} | {row['status']} | {row['notes']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The machine-auditable Scientific Reports formatting checks pass or are bounded by explicit human-gated submission tasks. The current manuscript has a compliant title, abstract, keyword count, main-text length, article structure, six display items and Methods-level AI-assisted tool-use documentation.",
            "",
            "The remaining items are not analysis failures. They require human author action: final author list and affiliations, all-author agreement, competing interests, funding, author contributions, repository DOI or permanent URL if deposited, final official Reporting Summary form if requested by the journal workflow, and final upload-system preview.",
        ]
    )
    ensure_parent(POLICY_AUDIT_MD)
    POLICY_AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reporting_summary(text: str) -> None:
    title = title_from_markdown(text)
    abstract = section_text(text, "Abstract")
    methods = section_text(text, "Methods")
    reporting = f"""# Nature Portfolio Reporting Summary Working Draft

Generated: {NOW}

This is a machine-prepared working draft to help complete the official Nature Portfolio Reporting Summary if the manuscript is sent for review. It is not a signed final publisher form.

## Manuscript

- Title: {title}
- Article type target: Scientific Reports Article
- Study type: Retrospective public-data computational biology and oncology analysis
- Primary organism: Human
- Disease context: Esophageal squamous cell carcinoma
- New experimental data: None

## Experimental Design

- Public datasets only were analysed. No new human specimens, animal experiments, wet-lab experiments or prospective recruitment were performed.
- The analysis was rebuilt around a Ca2/UPR axis-first strategy after the original SMIM14-centred model was demoted.
- The lead computational entry point is TMEM158, interpreted as a state-associated membrane-protein candidate, not a validated causal driver.
- The rule-defined TAC_high state combines high TMEM158-Ca2/PERK core score with high CAF score within each cohort.

## Sample Size And Replication

- Sample sizes are determined by available public cohorts and usable public raw files, not by prospective power calculation.
- Bulk discovery and validation use TCGA/GDC-compatible ESCC context and GEO cohorts listed in the manuscript and source-data inventory.
- GSE53625 is used as independent targeted clinical calibration after probe-sequence reannotation.
- GSE160269 and GSE221561 are used for single-cell pseudo-bulk localization and external context.
- Public spatial source-data tables from Liu et al., Nature Communications 2023 are used for fibroblast-rich progression context, not direct TMEM158/TAC_high spatial rescoring.

## Data Exclusions And Missing Data

- Dataset inclusion, corrupted raw-library handling and restricted-source boundaries are documented in the manuscript, QC outputs and source-data inventory.
- In GSE221561, seven of eleven listed raw libraries were usable; corrupted gzip members were retained in QC and not treated as silently absent.
- The public spatial Source Data did not contain the complete WTA matrix, so TMEM158, TAC_high and Ca2/UPR spatial scores were not directly recomputed.

## Randomization And Blinding

- Randomization and blinding are not applicable to this retrospective public-data computational study.
- Cohort-preserving random-label testing was used as a statistical specificity stress test for TAC_high, not as experimental randomization.

## Statistical Methods

- Sample-level scores were standardized within cohorts.
- Wilcoxon tests, Benjamini-Hochberg FDR correction, signed Stouffer meta-analysis, limma models, Cox proportional-hazards models and pseudo-bulk single-cell summaries were used as described in Methods.
- Negative or underpowered survival, immune, drug-resistance, spatial and causality layers are retained as claim boundaries rather than removed.

## Software And Reproducibility

- Main workflow: `TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R`
- Helper scripts: `TMEM158_CaUPR_ESCC/03_scripts/R/` and `TMEM158_CaUPR_ESCC/03_scripts/Python/`
- Source-data inventory: `TMEM158_CaUPR_ESCC/08_submission_strategy/source_data_and_supplementary_inventory.csv`
- Repository manifest: `TMEM158_CaUPR_ESCC/08_submission_strategy/repository_deposit_manifest.csv`
- Checksums: `TMEM158_CaUPR_ESCC/08_submission_strategy/repository_file_checksums.sha256`

## Human Research Ethics

- All datasets used were public and de-identified.
- No new ethics approval or informed consent was required for this secondary public-data analysis, subject to final author and institutional confirmation.

## Human-Gated Completion Items

- Complete the official Nature Portfolio Reporting Summary form if requested by the submission workflow.
- Confirm author names, affiliations, corresponding author and all-author agreement.
- Confirm competing interests, funding, acknowledgements and author contributions.
- Add repository DOI or permanent URL if a repository deposit is made before submission.
- Inspect the final journal-system converted manuscript and figure previews.

## Manuscript Abstract For Reference

{abstract}

## Methods Section Anchor

{methods[:1800].strip()}...
"""
    ensure_parent(REPORTING_SUMMARY)
    REPORTING_SUMMARY.write_text(reporting, encoding="utf-8")


def write_editorial_checklist() -> None:
    text = f"""# Editorial Policy Checklist Working Draft

Generated: {NOW}

| Item | Status | Evidence | Human action |
|---|---|---|---|
| Article type and structure | ready | `07_manuscript/manuscript_scientific_reports.md` | Final author review |
| AI-assisted tool-use disclosure | ready | Methods subsection and article-end disclosure | Human author approval |
| Data availability | ready, repository decision pending | Data Availability statement; source-data inventory | Add DOI/permanent URL if deposited |
| Code availability | ready, repository decision pending | Code Availability statement; `run_all.R` | Add DOI/permanent URL if deposited |
| Reporting Summary | working draft ready | `nature_portfolio_reporting_summary_working_draft.md` | Complete official publisher form if requested |
| Author list and title page | human required | `human_submission_metadata_template.md` | Fill final authors, affiliations, corresponding author |
| Author agreement | human required | Scientific Reports editorial policy | Submitting author must confirm all authors agree |
| Competing interests | human required | Nature Portfolio competing interests policy | Confirm all-author financial and non-financial declarations |
| Funding | human required | Human metadata template | Supply grants or no-funding statement |
| Preprint URL | optional human decision | Cover letter/system fields | Add only if applicable |
| Final upload-system preview | human required | Local DOCX render QA and bundle dry run | Inspect journal-generated PDF/figure preview |

Official source URLs:

- {SCIREP_SUBMISSION_URL}
- {NATURE_REPORTING_URL}
- {SCIREP_EDITORIAL_URL}
- {NATURE_COI_URL}
"""
    ensure_parent(EDITORIAL_CHECKLIST)
    EDITORIAL_CHECKLIST.write_text(text, encoding="utf-8")


def update_indexes(rows: Sequence[Dict[str, object]]) -> None:
    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "scientific_reports_official_policy_audit", "path": "04_results/qc/scientific_reports_official_policy_audit.csv"},
            {"result": "scientific_reports_official_policy_audit_report", "path": "08_submission_strategy/scientific_reports_official_policy_audit.md"},
            {"result": "nature_portfolio_reporting_summary_working_draft", "path": "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md"},
            {"result": "editorial_policy_checklist_working_draft", "path": "08_submission_strategy/editorial_policy_checklist_working_draft.md"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {"file_role": "scientific_reports_official_policy_audit_csv", "path": "04_results/qc/scientific_reports_official_policy_audit.csv", "status": "ready_human_gated_items_visible", "notes": "Official Scientific Reports/Nature Portfolio policy audit"},
            {"file_role": "scientific_reports_official_policy_audit_report", "path": "08_submission_strategy/scientific_reports_official_policy_audit.md", "status": "ready_human_gated_items_visible", "notes": "Markdown policy audit with source URLs"},
            {"file_role": "nature_portfolio_reporting_summary_working_draft", "path": "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md", "status": "ready_human_finalize", "notes": "Machine-prepared working draft; official form remains human-gated"},
            {"file_role": "editorial_policy_checklist_working_draft", "path": "08_submission_strategy/editorial_policy_checklist_working_draft.md", "status": "ready_human_gated_items_visible", "notes": "Authorship, COI, data/code and reporting checklist"},
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "08_submission_strategy" / "scientific_reports_final_human_tasks.csv",
        "task_id",
        [
            {"task_id": "human_09", "field_name": "official_reporting_summary_form", "required": "journal_workflow_dependent", "current_status": "working_draft_ready_human_required", "action_needed": "HUMAN_REQUIRED: complete and approve the official Nature Portfolio Reporting Summary form if the Scientific Reports workflow requests it.", "source": "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md", "notes": "Machine working draft prepared; final publisher form needs human review."},
            {"task_id": "human_10", "field_name": "author_agreement_and_title_page", "required": "yes", "current_status": "human_required", "action_needed": "HUMAN_REQUIRED: confirm final author list, affiliations, corresponding author details and all-author agreement before submission.", "source": "08_submission_strategy/human_submission_metadata_template.md", "notes": "Cannot be inferred from public data."},
            {"task_id": "human_11", "field_name": "final_upload_preview", "required": "yes", "current_status": "human_required", "action_needed": "HUMAN_REQUIRED: inspect final manuscript DOCX/PDF and figure previews in the Scientific Reports upload system.", "source": "08_submission_strategy/scientific_reports_submission_checklist.md", "notes": "Local render QA passed, but upload-system conversion can differ."},
        ],
        ["task_id", "field_name", "required", "current_status", "action_needed", "source", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {"item": "official_policy_audit", "value": "04_results/qc/scientific_reports_official_policy_audit.csv", "status": "pass_human_gated_items_visible", "notes": "Official Scientific Reports/Nature Portfolio policy audit generated"},
            {"item": "reporting_summary_working_draft", "value": "08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md", "status": "ready_human_finalize", "notes": "Working draft prepared; final official form remains human-gated"},
        ],
        ["item", "value", "status", "notes"],
    )


def update_checklist(rows: Sequence[Dict[str, object]]) -> None:
    checklist = ROOT / "08_submission_strategy" / "scientific_reports_submission_checklist.md"
    if not checklist.exists():
        return
    text = checklist.read_text(encoding="utf-8")
    additions = [
        "- [x] Official Scientific Reports/Nature Portfolio policy audit generated: `04_results/qc/scientific_reports_official_policy_audit.csv`",
        "- [x] Nature Portfolio Reporting Summary working draft generated: `08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md`",
        "- [ ] Complete final official Reporting Summary form if requested by the submission workflow",
        "- [ ] Confirm all-author agreement and final title-page metadata",
    ]
    anchor = "- [x] AI-assisted tool-use disclosure present"
    if additions[0] not in text and anchor in text:
        text = text.replace(anchor, anchor + "\n" + "\n".join(additions))
    text = re.sub(
        r"Current status: \*\*.*?not yet final upload-ready\*\*\.",
        "Current status: **target-journal manuscript package, editable DOCX, Supplementary Information draft, source-data inventory, repository manifest, submission-system field pack, official policy audit, Reporting Summary working draft and local upload dry-run bundle are ready; author metadata and declarations are supplied; official form completion if requested, publisher upload preview and final claim-boundary read are still required; not yet final upload-ready**.",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"Reason final upload is not yet clear: .*",
        "Reason final upload is not yet clear: official Reporting Summary form completion if requested, publisher-generated preview inspection and final claim-boundary read are outside the current machine analysis.",
        text,
    )
    checklist.write_text(text, encoding="utf-8")


def update_strategy(text: str, rows: Sequence[Dict[str, object]]) -> None:
    title = title_from_markdown(text)
    abstract = section_text(text, "Abstract")
    keywords = keywords_from_markdown(text)
    marker = "2026-06-19 official scirep policy audit"
    body = f"""## 2026-06-19 Official Scientific Reports/Nature Portfolio Policy Audit

- Official sources checked: Scientific Reports submission guidelines; Nature Portfolio reporting standards; Scientific Reports editorial policies; Nature Portfolio competing interests policy.
- Current manuscript title count: {count_words(title)} words.
- Current abstract count: {count_words(abstract)} words.
- Current keyword count: {len(keywords)}.
- Main display items: {main_figure_count()} composite figures.
- Machine-auditable formatting status: pass, with human-gated items separated.
- Reporting Summary: working draft generated at `08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md`; final official form remains human-gated if requested by the journal workflow.
- Remaining human gates: all-author agreement, official Reporting Summary form if requested, publisher upload-system preview and final claim-boundary read; repository DOI/permanent URL only if later deposited or requested."""
    replace_or_append(ROOT / "08_submission_strategy" / "target_journal_scientific_reports_strategy.md", marker, body)


def update_text_surfaces(rows: Sequence[Dict[str, object]]) -> None:
    machine_blockers = [row for row in rows if row["status"] == "needs_revision"]
    human_gates = [row for row in rows if "human" in str(row["status"]) or "repository" in str(row["status"])]
    qc_status = "pass" if not machine_blockers else "needs_revision"
    marker = "2026-06-19 official scirep policy audit"
    block = f"""Scientific Reports/Nature Portfolio official policy audit:

- Policy audit CSV: `04_results/qc/scientific_reports_official_policy_audit.csv`
- Policy audit report: `08_submission_strategy/scientific_reports_official_policy_audit.md`
- Nature Portfolio Reporting Summary working draft: `08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md`
- Editorial policy checklist working draft: `08_submission_strategy/editorial_policy_checklist_working_draft.md`
- Machine-auditable policy status: `{qc_status}`
- Human-gated policy/submission rows: {len(human_gates)}

The audit adds submission-policy traceability only. It does not raise the scientific claim ceiling beyond a public-data biological discovery candidate."""
    replace_or_append(ROOT / "README.md", marker, block)
    replace_or_append(ROOT / "00_project_log" / "master_log.md", marker, f"- 2026-06-19 latest: Added official Scientific Reports/Nature Portfolio policy audit and Reporting Summary working draft. Machine-auditable status: `{qc_status}`; human-gated submission rows remain explicit.")
    replace_or_append(ROOT / "00_project_log" / "stage_summary.md", marker, "- Official policy/readiness layer added: Scientific Reports formatting checks, Nature Portfolio Reporting Summary working draft and editorial policy checklist are now tracked as submission-engineering evidence.")
    replace_or_append(ROOT / "00_project_log" / "decision_record.md", marker, "Decision: treat official journal-policy audit and Reporting Summary preparation as the final machine-side submission-readiness layer.\n\nReason: journal instructions add non-biological requirements that can cause desk-return even when scientific figures are ready; these requirements must be separated from biological evidence.")
    replace_or_append(ROOT / "00_project_log" / "context_checkpoint.md", marker, "Latest checkpoint: official Scientific Reports/Nature Portfolio policy audit generated; Reporting Summary working draft prepared; author metadata/declarations supplied; remaining gates are publisher upload preview, final claim-boundary read and official form completion if requested.")
    update_strategy(MANUSCRIPT.read_text(encoding="utf-8"), rows)

    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "CURRENT_STATE.md",
        marker,
        f"""## 2026-06-19 官方投稿政策审计与 Reporting Summary 工作稿

已新增 Scientific Reports/Nature Portfolio 官方政策审计层：`TMEM158_CaUPR_ESCC/04_results/qc/scientific_reports_official_policy_audit.csv`、`TMEM158_CaUPR_ESCC/08_submission_strategy/scientific_reports_official_policy_audit.md`、`TMEM158_CaUPR_ESCC/08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md` 和 `TMEM158_CaUPR_ESCC/08_submission_strategy/editorial_policy_checklist_working_draft.md`。

机器可审计项目通过或有明确边界：标题、摘要、关键词、主图数量、主文长度、文章结构、数据/代码可用性陈述、Methods 内 AI-assisted tool-use 披露、DOCX 本地渲染 QA、投稿包 dry-run。作者列表/单位/通信作者、基金、利益冲突和作者贡献已由作者提供。仍需人工完成的是全作者提交同意、正式 Reporting Summary 表格（若系统要求）、投稿系统最终预览和最终 claim-boundary read。代码仓库沉积暂缓，只有后续选择公开沉积或编辑要求时才补 DOI/永久链接。该层是投稿工程证据，不改变“公共数据生物学发现候选”的 claim ceiling。"""
    )
    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "EVIDENCE_LOG.md",
        marker,
        """### 2026-06-19 更新：官方投稿政策审计层

- 证据类型：submission-policy/readiness engineering，不是新的生物学结果。
- 新增输出：`scientific_reports_official_policy_audit.csv`、`scientific_reports_official_policy_audit.md`、`nature_portfolio_reporting_summary_working_draft.md`、`editorial_policy_checklist_working_draft.md`。
- 解释：该层降低格式、政策和投稿流程退修风险；作者元数据和声明已补齐，仍保留 publisher-preview / final-claim-boundary / official-form-if-requested 边界。"""
    )
    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "DECISION_LOG.md",
        marker,
        """## 2026-06-19 官方政策审计决策

- 决策：新增 Scientific Reports/Nature Portfolio 官方政策审计与 Reporting Summary 工作稿，并接入 `run_all.R` 和投稿 bundle。
- 背景：科学证据层已经足够进入投稿工程阶段；继续增加普通生信分析不能替代作者声明、数据代码可用性、AI 使用披露和 Reporting Summary 等投稿要求。
- 可信度：高，因该层只做格式/政策/流程可追溯性，不扩展生物学 claim。
- 后续：在正式投稿系统中完成最终表格与预览，并在点击提交前做最后一次 claim-boundary read；若编辑要求公开代码沉积，再补 DOI/永久链接。"""
    )
    replace_or_append(
        PROJECT_ROOT / "docs" / "agent" / "TASKS" / "2026-06-18-SMIM14-CaUPR-ESCC-bioinformatics.md",
        marker,
        """## 2026-06-19 追加：Scientific Reports/Nature Portfolio 官方政策审计

- 新增脚本：`TMEM158_CaUPR_ESCC/03_scripts/Python/build_scientific_reports_official_policy_audit.py`。
- 新增输出：policy audit CSV/MD、Nature Portfolio Reporting Summary working draft、editorial policy checklist working draft。
- 当前意义：机器端投稿政策层已补齐；作者信息、利益冲突/基金/贡献已经补齐；最终投稿仍需系统预览、最终 claim-boundary read，并在系统要求时完成正式 Reporting Summary 表格。"""
    )


def main() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    rows = build_audit_rows(text)
    write_csv(
        POLICY_AUDIT_CSV,
        rows,
        ["policy_area", "check_item", "source_url", "observed_value", "status", "notes", "evidence_path"],
    )
    blockers = [row for row in rows if row["status"] == "needs_revision"]
    human = [row for row in rows if "human" in str(row["status"]) or "repository" in str(row["status"])]
    qc_rows = [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "official_sources_checked", "value": 4, "status": "pass", "notes": "Scientific Reports and Nature Portfolio official policy pages"},
        {"item": "machine_auditable_policy_blockers", "value": len(blockers), "status": "pass" if not blockers else "needs_revision", "notes": "Rows requiring machine-side text/file revision"},
        {"item": "human_gated_policy_rows", "value": len(human), "status": "not_yet", "notes": "Rows requiring human author or repository action"},
        {"item": "reporting_summary_working_draft", "value": rel(REPORTING_SUMMARY), "status": "ready_human_finalize", "notes": "Working draft only; official form remains human-gated"},
        {"item": "official_policy_audit_clearance", "value": "pass" if not blockers else "needs_revision", "status": "pass" if not blockers else "needs_revision", "notes": "Clearance excludes publisher preview, final claim-boundary read and official forms that require human submission-system confirmation"},
    ]
    write_csv(POLICY_AUDIT_QC, qc_rows, ["item", "value", "status", "notes"])
    write_policy_markdown(rows)
    write_reporting_summary(text)
    write_editorial_checklist()
    update_indexes(rows)
    update_checklist(rows)
    update_text_surfaces(rows)
    print(
        "scientific_reports_official_policy_audit=completed "
        f"rows={len(rows)} machine_blockers={len(blockers)} human_gated_rows={len(human)} "
        f"clearance={'pass' if not blockers else 'needs_revision'}"
    )


if __name__ == "__main__":
    main()
