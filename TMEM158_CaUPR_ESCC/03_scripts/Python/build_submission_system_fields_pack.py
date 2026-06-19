#!/usr/bin/env python3
"""Build Scientific Reports submission-system field pack.

This script converts the current target-journal manuscript and submission
support files into copy-ready fields for an online submission system. It does
not invent author metadata. Human-gated fields are explicitly marked so the
final-upload blocker is narrow and auditable.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
PUBLIC_REPOSITORY_URL = "https://github.com/afa-cloud/TMEM158_CaUPR_ESCC"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)",
        re.S | re.M,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def clean_markdown(value: str) -> str:
    value = re.sub(r"\n{2,}", "\n\n", value.strip())
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    return value.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)?", text))


def title_from_manuscript(text: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    return match.group(1).strip() if match else ""


def keyword_list(raw: str) -> List[str]:
    raw = clean_markdown(raw)
    if not raw:
        return []
    pieces = []
    for chunk in re.split(r";|\n|,", raw):
        chunk = chunk.strip(" -\t")
        if chunk:
            pieces.append(chunk)
    return pieces


def line_after_heading(text: str, heading: str) -> str:
    content = section(text, heading)
    return clean_markdown(content)


def safe_excerpt(text: str, max_words: int) -> str:
    words = re.findall(r"\S+", clean_markdown(text))
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + " ..."


def cover_pitch(cover_letter: str) -> str:
    paragraphs = [p.strip() for p in cover_letter.split("\n\n") if p.strip()]
    for para in paragraphs:
        if "This manuscript reports" in para:
            return clean_markdown(para)
    return clean_markdown(paragraphs[1]) if len(paragraphs) > 1 else ""


def build_fields() -> List[Dict[str, object]]:
    manuscript_path = ROOT / "07_manuscript" / "manuscript_scientific_reports.md"
    cover_path = ROOT / "08_submission_strategy" / "scientific_reports_cover_letter_draft.md"
    metadata_path = ROOT / "08_submission_strategy" / "human_submission_metadata_template.md"

    manuscript = read_text(manuscript_path)
    cover = read_text(cover_path) if cover_path.exists() else ""
    metadata = read_text(metadata_path) if metadata_path.exists() else ""

    title = title_from_manuscript(manuscript)
    abstract = clean_markdown(section(manuscript, "Abstract"))
    keywords = keyword_list(section(manuscript, "Keywords"))
    data_availability = line_after_heading(manuscript, "Data availability")
    code_availability = line_after_heading(manuscript, "Code availability")
    ethics = line_after_heading(manuscript, "Ethics statement")
    funding = line_after_heading(manuscript, "Funding")
    author_contributions = line_after_heading(manuscript, "Author contributions")
    competing_interests = line_after_heading(manuscript, "Competing interests")
    ai_tool_use = line_after_heading(manuscript, "AI-assisted tool use")
    additional_info = line_after_heading(manuscript, "Additional information")
    limitations = safe_excerpt(section(manuscript, "Limitations"), 140)

    significance = (
        "This public-data study defines a reproducible TMEM158-associated TAC_high "
        "Ca2/UPR-CAF stress-ecology state in ESCC, with CAF/fibroblast localization, "
        "CAF-adjusted residual stress transcription and explicit negative boundaries "
        "for prognosis, causality, immune suppression and treatment resistance."
    )
    lay_summary = (
        "The study uses existing public cancer datasets to describe a stress-related "
        "tumour ecology pattern in esophageal squamous cell carcinoma. The findings "
        "suggest a testable biology state linked to fibroblast-rich tumour context, "
        "but they do not prove a treatment target or clinical biomarker."
    )
    claims_not_made = (
        "The manuscript does not claim that TMEM158 is a validated causal driver, "
        "a clinical prognostic biomarker, a cisplatin-resistance mechanism, a direct "
        "immune-suppression mechanism, a directly spatially validated programme or "
        "an experimentally validated ESCC protein/ER-localization finding."
    )

    fields: List[Dict[str, object]] = [
        {
            "field_group": "manuscript",
            "field_name": "article_type",
            "field_value": "Article",
            "status": "ready",
            "source": "target journal strategy",
            "notes": "First-pass target-journal format.",
        },
        {
            "field_group": "manuscript",
            "field_name": "title",
            "field_value": title,
            "status": "ready",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": f"{word_count(title)} words.",
        },
        {
            "field_group": "manuscript",
            "field_name": "running_title",
            "field_value": "TMEM158-associated TAC_high stress ecology in ESCC",
            "status": "ready",
            "source": "derived from title",
            "notes": "Short display title; human may adjust if the journal asks for a running title.",
        },
        {
            "field_group": "manuscript",
            "field_name": "abstract",
            "field_value": abstract,
            "status": "ready",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": f"{word_count(abstract)} words.",
        },
        {
            "field_group": "manuscript",
            "field_name": "keywords",
            "field_value": "; ".join(keywords),
            "status": "ready",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": f"{len(keywords)} keywords.",
        },
        {
            "field_group": "editorial",
            "field_name": "editor_significance_statement",
            "field_value": significance,
            "status": "ready_optional",
            "source": "derived from manuscript and reviewer-risk pack",
            "notes": "Use if the submission system requests significance, relevance or editor comments.",
        },
        {
            "field_group": "editorial",
            "field_name": "plain_language_summary",
            "field_value": lay_summary,
            "status": "ready_optional",
            "source": "derived from manuscript abstract and limitations",
            "notes": "Use only if requested by the journal system.",
        },
        {
            "field_group": "editorial",
            "field_name": "cover_letter_core_pitch",
            "field_value": cover_pitch(cover),
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/scientific_reports_cover_letter_draft.md",
            "notes": "Corresponding-author name, affiliation and email are filled.",
        },
        {
            "field_group": "author_metadata",
            "field_name": "author_list",
            "field_value": "Yang Haoshui; Ma Yuqing",
            "status": "ready",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Author order supplied by the submitting author.",
        },
        {
            "field_group": "author_metadata",
            "field_name": "affiliations",
            "field_value": "The First Affiliated Hospital of Xinjiang Medical University; Xinjiang Medical University",
            "status": "ready",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Department-level detail can be added if the journal system requires it.",
        },
        {
            "field_group": "author_metadata",
            "field_name": "corresponding_author",
            "field_value": "Ma Yuqing",
            "status": "ready",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Corresponding author supplied by the user.",
        },
        {
            "field_group": "author_metadata",
            "field_name": "corresponding_author_email",
            "field_value": "yuqingm0928@126.com",
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Corresponding-author email supplied by the user.",
        },
        {
            "field_group": "author_metadata",
            "field_name": "orcid",
            "field_value": "Yang Haoshui: 0009-0008-6805-3893; Ma Yuqing: not provided",
            "status": "ready_partial",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Ma Yuqing ORCID is optional unless the journal system requires it.",
        },
        {
            "field_group": "availability",
            "field_name": "data_availability",
            "field_value": data_availability,
            "status": "ready_public_repository",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": f"Processed outputs are deposited in the public GitHub repository: {PUBLIC_REPOSITORY_URL}.",
        },
        {
            "field_group": "availability",
            "field_name": "code_availability",
            "field_value": code_availability,
            "status": "ready_public_repository",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": f"Analysis code is deposited in the public GitHub repository: {PUBLIC_REPOSITORY_URL}.",
        },
        {
            "field_group": "declarations",
            "field_name": "ethics_statement",
            "field_value": ethics,
            "status": "ready",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": "Public de-identified secondary analysis only.",
        },
        {
            "field_group": "declarations",
            "field_name": "competing_interests",
            "field_value": competing_interests,
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "User confirmed no competing interests.",
        },
        {
            "field_group": "declarations",
            "field_name": "funding",
            "field_value": funding,
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "User confirmed no external funding.",
        },
        {
            "field_group": "declarations",
            "field_name": "author_contributions",
            "field_value": author_contributions,
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Roles supplied by the user and formatted for the manuscript.",
        },
        {
            "field_group": "declarations",
            "field_name": "acknowledgements",
            "field_value": additional_info,
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "Institutional acknowledgement and ORCID/correspondence note supplied by the user.",
        },
        {
            "field_group": "declarations",
            "field_name": "ai_assisted_tool_use",
            "field_value": ai_tool_use,
            "status": "ready_author_confirmed",
            "source": "08_submission_strategy/human_submission_metadata_template.md",
            "notes": "User approved AI-assisted tool disclosure.",
        },
        {
            "field_group": "repository",
            "field_name": "repository_doi_or_permanent_url",
            "field_value": PUBLIC_REPOSITORY_URL,
            "status": "ready_public_repository_url",
            "source": "08_submission_strategy/repository_deposit_manifest.csv",
            "notes": "Public GitHub repository created before submission; DOI can be minted later through Zenodo if required.",
        },
        {
            "field_group": "reviewer_metadata",
            "field_name": "suggested_reviewers",
            "field_value": "OPTIONAL_HUMAN_REQUIRED: add only if the journal requests suggested reviewers.",
            "status": "optional_human_required",
            "source": "human author decision",
            "notes": "Must avoid conflicts of interest.",
        },
        {
            "field_group": "reviewer_metadata",
            "field_name": "opposed_reviewers",
            "field_value": "OPTIONAL_HUMAN_REQUIRED: add only if necessary and journal allows exclusions.",
            "status": "optional_human_required",
            "source": "human author decision",
            "notes": "Must be justified and conflict-aware.",
        },
        {
            "field_group": "claim_boundary",
            "field_name": "public_data_boundary",
            "field_value": "This study used only publicly available datasets and did not involve newly collected human specimens, animal experiments or wet-lab experiments.",
            "status": "ready",
            "source": "Methods / ethics statement",
            "notes": "Keep this statement in submission metadata if a study-design field is requested.",
        },
        {
            "field_group": "claim_boundary",
            "field_name": "claims_not_made",
            "field_value": claims_not_made,
            "status": "ready",
            "source": "claim-boundary audit and reviewer-risk pack",
            "notes": "Use for cover letter, editor comments or reviewer response preparation.",
        },
        {
            "field_group": "claim_boundary",
            "field_name": "limitations_summary",
            "field_value": limitations,
            "status": "ready",
            "source": "07_manuscript/manuscript_scientific_reports.md",
            "notes": "Condensed from manuscript limitations.",
        },
    ]

    # Surface the presence of the existing metadata template in QC without using it as data.
    if not metadata:
        fields.append(
            {
                "field_group": "declarations",
                "field_name": "human_metadata_template_status",
                "field_value": "Missing human metadata template.",
                "status": "needs_revision",
                "source": "08_submission_strategy/human_submission_metadata_template.md",
                "notes": "Template should exist before final upload.",
            }
        )

    return fields


def build_human_tasks(fields: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for row in fields:
        if "human" not in str(row["status"]):
            continue
        tasks.append(
            {
                "task_id": f"human_{len(tasks) + 1:02d}",
                "field_name": row["field_name"],
                "required": "yes" if row["status"] == "human_required" else "optional",
                "current_status": row["status"],
                "action_needed": row["field_value"],
                "source": row["source"],
                "notes": row["notes"],
            }
        )
    tasks.extend(
        [
            {
                "task_id": f"human_{len(tasks) + 1:02d}",
                "field_name": "final_upload_preview",
                "required": "yes",
                "current_status": "human_required",
                "action_needed": "Inspect final manuscript DOCX/PDF and figure previews in the journal upload system.",
                "source": "08_submission_strategy/scientific_reports_submission_checklist.md",
                "notes": "Local render QA passed, but upload-system conversion can differ.",
            },
            {
                "task_id": f"human_{len(tasks) + 1:02d}",
                "field_name": "final_claim_boundary_read",
                "required": "yes",
                "current_status": "human_required",
                "action_needed": "Confirm no causal, prognostic, immune-suppression, spatial-validation or treatment-resistance claim was introduced during metadata editing.",
                "source": "08_submission_strategy/claim_boundary_text_audit.md",
                "notes": "Machine text audit passed on current files; edits after this point require reread.",
            },
        ]
    )
    return tasks


def qc_rows(fields: Sequence[Dict[str, object]], human_tasks: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    field_map = {row["field_name"]: row for row in fields}
    required_ready = [
        "article_type",
        "title",
        "abstract",
        "keywords",
        "data_availability",
        "code_availability",
        "ethics_statement",
        "public_data_boundary",
        "claims_not_made",
    ]
    missing = [name for name in required_ready if name not in field_map or not field_map[name]["field_value"]]
    title_words = word_count(str(field_map.get("title", {}).get("field_value", "")))
    abstract_words = word_count(str(field_map.get("abstract", {}).get("field_value", "")))
    keywords = keyword_list(str(field_map.get("keywords", {}).get("field_value", "")))
    human_required = [task for task in human_tasks if task["required"] == "yes"]
    machine_pass = not missing and title_words <= 20 and abstract_words <= 200 and len(keywords) <= 6
    return [
        {"item": "generated_at", "value": NOW, "status": "info", "notes": "Local system timestamp"},
        {"item": "submission_fields", "value": len(fields), "status": "pass", "notes": "Total submission-system field rows"},
        {"item": "required_machine_fields_missing", "value": len(missing), "status": "pass" if not missing else "needs_revision", "notes": ";".join(missing) if missing else "None"},
        {"item": "title_words", "value": title_words, "status": "pass" if title_words <= 20 else "needs_revision", "notes": "Scientific Reports first-pass title threshold <=20 words"},
        {"item": "abstract_words", "value": abstract_words, "status": "pass" if abstract_words <= 200 else "needs_revision", "notes": "Scientific Reports first-pass abstract threshold <=200 words"},
        {"item": "keywords", "value": len(keywords), "status": "pass" if len(keywords) <= 6 else "needs_revision", "notes": "Maximum six keywords/key phrases"},
        {"item": "human_required_tasks", "value": len(human_required), "status": "not_yet", "notes": "Publisher upload preview and final claim-boundary read remain human-gated"},
        {"item": "machine_submission_fields_clearance", "value": "pass" if machine_pass else "needs_revision", "status": "pass" if machine_pass else "needs_revision", "notes": "Pass requires copy-ready required machine fields and format thresholds"},
        {"item": "final_upload_clearance", "value": "not_yet", "status": "not_yet", "notes": "Publisher upload preview and final claim-boundary read remain human-gated"},
    ]


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


def write_markdown(fields: Sequence[Dict[str, object]], human_tasks: Sequence[Dict[str, object]], qc: Sequence[Dict[str, object]]) -> None:
    status_map = {row["item"]: row for row in qc}
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in fields:
        grouped.setdefault(str(row["field_group"]), []).append(row)

    lines = [
        "# Scientific Reports Submission-System Fields",
        "",
        f"Generated: {NOW}",
        "",
        "## Machine Summary",
        "",
        f"- Submission field rows: {status_map['submission_fields']['value']}",
        f"- Machine submission-fields clearance: `{status_map['machine_submission_fields_clearance']['value']}`",
        f"- Final upload clearance: `{status_map['final_upload_clearance']['value']}`",
        f"- Human-required tasks: {status_map['human_required_tasks']['value']}",
        "",
        "## Copy-Ready Fields",
        "",
    ]
    for group, rows in grouped.items():
        lines.extend([f"### {group.replace('_', ' ').title()}", ""])
        for row in rows:
            lines.append(f"#### {row['field_name']}")
            lines.append("")
            lines.append(f"Status: `{row['status']}`")
            lines.append("")
            lines.append(str(row["field_value"]).strip())
            lines.append("")
            lines.append(f"Source: `{row['source']}`")
            lines.append("")
            lines.append(f"Notes: {row['notes']}")
            lines.append("")

    lines.extend(["## Human-Gated Final Tasks", ""])
    for task in human_tasks:
        lines.append(f"- `{task['task_id']}` {task['field_name']} ({task['required']}): {task['action_needed']}")

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This file is a submission-engineering artifact. It does not upgrade the manuscript beyond a public-data, association-based and hypothesis-generating ESCC stress-ecology discovery study.",
            "",
        ]
    )
    out = ROOT / "08_submission_strategy" / "scientific_reports_submission_system_fields.md"
    out.write_text("\n".join(lines), encoding="utf-8")


def update_text_surfaces(fields: Sequence[Dict[str, object]], human_tasks: Sequence[Dict[str, object]], qc: Sequence[Dict[str, object]]) -> None:
    marker = "2026-06-19 scientific reports submission system fields"
    qc_map = {row["item"]: row for row in qc}
    machine_clearance = qc_map["machine_submission_fields_clearance"]["value"]
    human_required = qc_map["human_required_tasks"]["value"]
    addendum = f"""
Submission-system field pack:

- `08_submission_strategy/scientific_reports_submission_system_fields.md`
- `08_submission_strategy/scientific_reports_submission_system_fields.csv`
- `08_submission_strategy/scientific_reports_final_human_tasks.csv`
- `04_results/qc/scientific_reports_submission_system_fields_qc.csv`

Machine submission-fields clearance: `{machine_clearance}`.
Human-required final tasks: {human_required}.
Final upload clearance remains `not_yet` because publisher upload preview and final claim-boundary read require human confirmation.
"""
    replace_or_append(ROOT / "README.md", marker, addendum)
    replace_or_append(ROOT / "00_project_log" / "master_log.md", marker, f"- 2026-06-19 latest: Generated Scientific Reports submission-system field pack. Machine fields clearance: `{machine_clearance}`; human-required tasks: {human_required}. Author metadata/declarations supplied; public GitHub code repository listed as `{PUBLIC_REPOSITORY_URL}`.")
    replace_or_append(ROOT / "00_project_log" / "stage_summary.md", marker, "- Scientific Reports submission-system fields are now extracted into Markdown/CSV, with human-gated metadata isolated in a final task table.")
    replace_or_append(ROOT / "00_project_log" / "decision_record.md", marker, "Decision: after machine bundle clearance, add a submission-system fields pack so final blockers are explicit and not confused with missing analysis artifacts. After author metadata was supplied and the public GitHub code repository was created, the remaining required blockers are publisher upload preview and final claim-boundary read.")
    replace_or_append(ROOT / "00_project_log" / "context_checkpoint.md", marker, "Latest checkpoint: Scientific Reports online-submission fields are available in `08_submission_strategy/scientific_reports_submission_system_fields.md` and `.csv`; final human tasks are in `scientific_reports_final_human_tasks.csv`.")

    upsert_csv(
        ROOT / "04_results" / "result_index.csv",
        "result",
        [
            {"result": "scientific_reports_submission_system_fields_md", "path": "08_submission_strategy/scientific_reports_submission_system_fields.md"},
            {"result": "scientific_reports_submission_system_fields_csv", "path": "08_submission_strategy/scientific_reports_submission_system_fields.csv"},
            {"result": "scientific_reports_final_human_tasks", "path": "08_submission_strategy/scientific_reports_final_human_tasks.csv"},
            {"result": "scientific_reports_submission_system_fields_qc", "path": "04_results/qc/scientific_reports_submission_system_fields_qc.csv"},
        ],
        ["result", "path"],
    )
    upsert_csv(
        ROOT / "06_tables" / "scientific_reports_submission_file_manifest.csv",
        "file_role",
        [
            {"file_role": "scientific_reports_submission_system_fields_md", "path": "08_submission_strategy/scientific_reports_submission_system_fields.md", "status": "ready_not_final_upload_clear", "notes": "Copy-ready submission-system fields with human-gated fields marked"},
            {"file_role": "scientific_reports_submission_system_fields_csv", "path": "08_submission_strategy/scientific_reports_submission_system_fields.csv", "status": "ready_not_final_upload_clear", "notes": "CSV table of submission-system fields"},
            {"file_role": "scientific_reports_final_human_tasks", "path": "08_submission_strategy/scientific_reports_final_human_tasks.csv", "status": "human_required", "notes": "Publisher upload preview and final claim-boundary read tasks"},
            {"file_role": "scientific_reports_submission_system_fields_qc", "path": "04_results/qc/scientific_reports_submission_system_fields_qc.csv", "status": "ready_not_final_upload_clear", "notes": "QC for submission-system fields"},
        ],
        ["file_role", "path", "status", "notes"],
    )
    upsert_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_format_qc.csv",
        "item",
        [
            {"item": "submission_system_fields_pack", "value": "08_submission_strategy/scientific_reports_submission_system_fields.md", "status": "pass_not_final_upload_clear", "notes": "Copy-ready online-submission field pack generated"},
            {"item": "final_human_tasks_table", "value": "08_submission_strategy/scientific_reports_final_human_tasks.csv", "status": "not_yet", "notes": "Publisher upload preview and final claim-boundary read remain human-gated"},
        ],
        ["item", "value", "status", "notes"],
    )

    checklist = ROOT / "08_submission_strategy" / "scientific_reports_submission_checklist.md"
    text = checklist.read_text(encoding="utf-8")
    if "- [x] Submission-system field pack generated" not in text:
        text = text.replace(
            "- [x] Human metadata template created: `08_submission_strategy/human_submission_metadata_template.md`",
            "- [x] Human metadata template created: `08_submission_strategy/human_submission_metadata_template.md`\n- [x] Submission-system field pack generated",
        )
    text = text.replace(
        "source-data inventory, repository manifest and local upload dry-run bundle are ready",
        "source-data inventory, repository manifest, submission-system field pack and local upload dry-run bundle are ready",
    )
    checklist.write_text(text, encoding="utf-8")

    replace_or_append(
        ROOT / "08_submission_strategy" / "submission_readiness_audit.md",
        marker,
        f"""## Submission-System Fields Addendum

Generated: {NOW}

- Field pack Markdown: `08_submission_strategy/scientific_reports_submission_system_fields.md`
- Field pack CSV: `08_submission_strategy/scientific_reports_submission_system_fields.csv`
- Final human tasks: `08_submission_strategy/scientific_reports_final_human_tasks.csv`
- QC: `04_results/qc/scientific_reports_submission_system_fields_qc.csv`
- Machine submission-fields clearance: `{machine_clearance}`

Interpretation: online-submission copy-ready fields are prepared. Final upload remains not yet clear because publisher upload preview and final claim-boundary read require human confirmation. The public code repository is listed as `{PUBLIC_REPOSITORY_URL}`."""
    )

    project_root = ROOT.parent
    replace_or_append(
        project_root / "docs" / "agent" / "CURRENT_STATE.md",
        marker,
        f"""## 2026-06-19 Scientific Reports 投稿系统字段包完成

`TMEM158_CaUPR_ESCC/` 已新增投稿系统字段包：`08_submission_strategy/scientific_reports_submission_system_fields.md`、`scientific_reports_submission_system_fields.csv`、`scientific_reports_final_human_tasks.csv` 和 `04_results/qc/scientific_reports_submission_system_fields_qc.csv`。机器端 submission-fields clearance 为 `{machine_clearance}`。

该层把标题、摘要、关键词、cover-letter pitch、Data availability、Code availability、Ethics statement、作者贡献、基金、利益冲突、acknowledgements、AI disclosure、public-data boundary 和 claims-not-made 等字段整理为可复制格式。用户已改为初投前公开 GitHub 代码仓库：`{PUBLIC_REPOSITORY_URL}`；当前缺口收窄为投稿系统最终预览和最终 claim-boundary 复读，而不是生信分析不足。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "DECISION_LOG.md",
        marker,
        """## 2026-06-19 Scientific Reports 投稿系统字段包决策

- 决策：新增投稿系统字段包，并接入 `run_all.R` 与本地 submission bundle。
- 背景：机器端证据、图件、DOCX、查重、claim-boundary、reviewer-risk 和 bundle 已通过；剩余缺口需要从泛泛“人工确认”压缩成可执行字段。
- 依据：字段包从当前 Scientific Reports 稿件和 cover letter 抽取标题、摘要、关键词、availability、ethics、boundary 和 editor-facing pitch；不能机器决定的作者/声明/DOI/上传预览单独列入 human task table。
- 可信度：高。
- 后续待验证：人工补齐字段后重新跑 claim-boundary audit 或至少人工复读标题、摘要、cover letter 和投稿系统生成 PDF。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "EVIDENCE_LOG.md",
        marker,
        """### 2026-06-19 更新：Scientific Reports submission-system fields

- 新增证据类型：投稿工程证据。`scientific_reports_submission_system_fields.md/.csv` 证明当前稿件的核心投稿字段已能从正式稿件稳定抽取；`scientific_reports_final_human_tasks.csv` 证明剩余缺口集中在人工作者/声明/仓库/上传预览字段。
- 解释：该层不增加生物学证据，不改变 claim ceiling；它提高投稿可执行性和最终清单透明度。"""
    )
    replace_or_append(
        project_root / "docs" / "agent" / "TASKS" / "2026-06-18-SMIM14-CaUPR-ESCC-bioinformatics.md",
        marker,
        """## 2026-06-19 最新追加：Scientific Reports submission-system fields

- 新增脚本：`TMEM158_CaUPR_ESCC/03_scripts/Python/build_submission_system_fields_pack.py`，并接入 `TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R`。
- 新增输出：投稿系统字段 Markdown/CSV、最终人工事项表和字段 QC。
- 当前意义：机器端可交付范围进一步推进到在线投稿字段层；剩余缺口为人工作者信息、声明、仓库 DOI/永久链接和最终上传系统预览。"""
    )


def main() -> None:
    fields = build_fields()
    human_tasks = build_human_tasks(fields)
    qc = qc_rows(fields, human_tasks)
    write_csv(
        ROOT / "08_submission_strategy" / "scientific_reports_submission_system_fields.csv",
        fields,
        ["field_group", "field_name", "field_value", "status", "source", "notes"],
    )
    write_csv(
        ROOT / "08_submission_strategy" / "scientific_reports_final_human_tasks.csv",
        human_tasks,
        ["task_id", "field_name", "required", "current_status", "action_needed", "source", "notes"],
    )
    write_csv(
        ROOT / "04_results" / "qc" / "scientific_reports_submission_system_fields_qc.csv",
        qc,
        ["item", "value", "status", "notes"],
    )
    write_markdown(fields, human_tasks, qc)
    update_text_surfaces(fields, human_tasks, qc)
    qc_map = {row["item"]: row for row in qc}
    print(
        "submission_system_fields_pack=completed "
        f"fields={qc_map['submission_fields']['value']} "
        f"machine_submission_fields_clearance={qc_map['machine_submission_fields_clearance']['value']} "
        f"human_required_tasks={qc_map['human_required_tasks']['value']}"
    )


if __name__ == "__main__":
    main()
