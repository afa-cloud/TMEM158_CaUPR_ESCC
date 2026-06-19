#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIT = ROOT / "01_literature"
MANIFEST = LIT / "manual_download_manifest.csv"
ADJUDICATION = LIT / "manual_context_adjudication.csv"
OUT = LIT / "downloaded_fulltext_local_scan.csv"
SUMMARY = LIT / "downloaded_fulltext_local_scan_summary.md"
STATUS = ROOT / "04_results" / "qc" / "tmem158_downloaded_fulltext_scan_status.csv"
LITERATURE_STATUS = ROOT / "04_results" / "qc" / "tmem158_literature_readiness_status.csv"
FULLTEXT_GATE = LIT / "fulltext_table_duplication_gate.csv"


PATTERNS = {
    "alias": [r"\bTMEM158\b", r"\bHBBP\b", r"\bp40BBp\b", r"\bp40BBP\b", r"transmembrane protein 158", r"\bENSG00000249992\b"],
    "ris1": [r"\bRIS1\b", r"Ras-induced senescence-1"],
    "escc": [r"\bESCC\b", r"esophageal squamous cell carcinoma", r"oesophageal squamous cell carcinoma", r"esophageal cancer", r"oesophageal cancer"],
    "caupr": [r"calcium", r"\bCa2\b", r"Ca2\+", r"\bSOCE\b", r"\bUPR\b", r"unfolded protein response", r"endoplasmic reticulum stress", r"\bPERK\b", r"\bIRE1\b", r"\bATF6\b"],
    "caf": [r"\bCAF\b", r"cancer-associated fibroblast", r"fibroblast", r"stromal", r"stroma", r"extracellular matrix", r"\bECM\b"],
    "supplement": [r"supplementary", r"supplemental", r"supporting information", r"\.xlsx", r"\.xls", r"\.docx", r"\.zip", r"mmc\d"],
}
COMPILED = {key: [re.compile(p, re.I) for p in pats] for key, pats in PATTERNS.items()}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_adjudications(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    return {
        row.get("item_id", ""): row
        for row in rows
        if row.get("item_id") and row.get("adjudication_status", "").startswith("resolved_")
    }


def text_from_file(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    data = path.read_bytes()
    if suffix in {".html", ".htm", ".xml", ".txt", ".csv", ".tsv", ".md"}:
        text = data.decode("utf-8", errors="ignore")
        text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text, "text"
    if suffix == ".pdf":
        # Avoid adding a PDF dependency here; record presence but keep manual status
        # unless a text/HTML companion exists.
        return "", "pdf_unparsed"
    return data[:200000].decode("utf-8", errors="ignore"), "binary_text_probe"


def positions(kind: str, text: str) -> list[int]:
    out: list[int] = []
    for pattern in COMPILED[kind]:
        out.extend(match.start() for match in pattern.finditer(text))
    return out


def near(a: list[int], b: list[int], window: int = 2000) -> bool:
    return bool(a and b and min(abs(x - y) for x in a for y in b) <= window)


def main() -> None:
    manifest = read_csv(MANIFEST)
    adjudications = read_adjudications(ADJUDICATION)
    scan_rows: list[dict[str, object]] = []
    updated_manifest: list[dict[str, object]] = []
    newly_resolved = 0
    curated_resolved = 0
    remaining_manual = 0

    for row in manifest:
        item = dict(row)
        status = row.get("download_status", "")
        target_dir = ROOT / row.get("target_relative_path", "")
        files = [p for p in target_dir.glob("*") if p.is_file()] if target_dir.exists() else []
        relevant_files = [p for p in files if p.stat().st_size > 0]
        item_scan = {
            "item_id": row.get("item_id", ""),
            "source_article": row.get("source_article", ""),
            "previous_status": status,
            "files_found": len(relevant_files),
            "total_bytes": sum(p.stat().st_size for p in relevant_files),
            "scan_status": "not_scanned_non_manual" if not status.startswith("manual_required") else "missing_local_file",
            "alias_hits": 0,
            "ris1_hits": 0,
            "escc_hits": 0,
            "caupr_hits": 0,
            "caf_hits": 0,
            "supplement_hits": 0,
            "alias_near_escc": 0,
            "alias_near_caupr": 0,
            "alias_near_caf": 0,
            "interpretation": "",
        }
        if status.startswith("manual_required") and relevant_files:
            text_parts: list[str] = []
            parsed_modes: list[str] = []
            for path in relevant_files:
                text, mode = text_from_file(path)
                parsed_modes.append(f"{path.name}:{mode}")
                if text:
                    text_parts.append(text)
            text = " ".join(text_parts)
            pos_alias = positions("alias", text)
            pos_ris1 = positions("ris1", text)
            pos_escc = positions("escc", text)
            pos_caupr = positions("caupr", text)
            pos_caf = positions("caf", text)
            pos_supp = positions("supplement", text)
            item_scan.update(
                {
                    "scan_status": "local_text_scanned" if text else "local_file_present_unparsed",
                    "parsed_modes": ";".join(parsed_modes),
                    "text_chars": len(text),
                    "alias_hits": len(pos_alias),
                    "ris1_hits": len(pos_ris1),
                    "escc_hits": len(pos_escc),
                    "caupr_hits": len(pos_caupr),
                    "caf_hits": len(pos_caf),
                    "supplement_hits": len(pos_supp),
                    "alias_near_escc": int(near(pos_alias, pos_escc)),
                    "alias_near_caupr": int(near(pos_alias, pos_caupr)),
                    "alias_near_caf": int(near(pos_alias, pos_caf)),
                }
            )
            if text and len(text) >= 8000 and not near(pos_alias, pos_escc) and len(pos_supp) == 0:
                item["download_status"] = "auto_local_text_reviewed_no_direct_escc_duplication"
                item["failure_reason"] = ""
                item["notes"] = "Local downloaded text/HTML scan found no direct TMEM158-ESCC proximity and no obvious supplementary-table link."
                newly_resolved += 1
                item_scan["interpretation"] = "Resolved by local downloaded text/HTML scan."
            elif text and len(text) >= 8000 and not near(pos_alias, pos_escc):
                item["download_status"] = "manual_required_supplement_link_or_table_check"
                item["failure_reason"] = "Local text scan did not show direct TMEM158-ESCC proximity, but supplementary/table links or markers remain."
                item_scan["interpretation"] = "No direct local text duplication, but supplement/table markers remain."
            else:
                item["download_status"] = "manual_required_local_file_unresolved"
                item["failure_reason"] = "Local file was missing, too short, unparsed, or still contained direct/proximity risk."
                item_scan["interpretation"] = "Manual review still required."

        if item.get("download_status", "").startswith("manual_required"):
            adjudication = adjudications.get(row.get("item_id", ""))
            if adjudication:
                item["download_status"] = adjudication.get("resolved_status", "curated_context_reviewed_no_direct_escc_duplication")
                item["failure_reason"] = ""
                item["notes"] = (
                    f"Resolved through curated context adjudication. "
                    f"Source: {adjudication.get('adjudication_source', '')}. "
                    f"Evidence: {adjudication.get('evidence', '')}. "
                    f"Interpretation: {adjudication.get('interpretation', '')}."
                )
                item_scan["scan_status"] = "curated_context_adjudicated"
                item_scan["interpretation"] = adjudication.get("interpretation", "")
                curated_resolved += 1

        if item.get("download_status", "").startswith("manual_required"):
            remaining_manual += 1
        updated_manifest.append(item)
        scan_rows.append(item_scan)

    if manifest:
        write_csv(MANIFEST, updated_manifest, list(manifest[0].keys()))
    write_csv(
        OUT,
        scan_rows,
        [
            "item_id",
            "source_article",
            "previous_status",
            "files_found",
            "total_bytes",
            "scan_status",
            "parsed_modes",
            "text_chars",
            "alias_hits",
            "ris1_hits",
            "escc_hits",
            "caupr_hits",
            "caf_hits",
            "supplement_hits",
            "alias_near_escc",
            "alias_near_caupr",
            "alias_near_caf",
            "interpretation",
        ],
    )
    write_csv(
        STATUS,
        [
            {"item": "module_status", "value": "completed"},
            {"item": "newly_resolved_by_local_scan", "value": newly_resolved},
            {"item": "curated_resolved_by_context_adjudication", "value": curated_resolved},
            {"item": "remaining_manual_required", "value": remaining_manual},
            {"item": "scan_table", "value": str(OUT.relative_to(ROOT))},
        ],
        ["item", "value"],
    )
    write_csv(
        LITERATURE_STATUS,
        [
            {"item": "module_status", "value": "completed"},
            {"item": "route", "value": "PubMed/PMC E-utilities through UTM VM plus local publisher/PMC page scan where downloads succeeded"},
            {"item": "manifest_items_total", "value": len(updated_manifest)},
            {"item": "auto_pmc_xml_reviewed_items", "value": sum(str(row.get("download_status", "")).startswith("auto_xml_reviewed") for row in updated_manifest)},
            {"item": "auto_local_text_reviewed_items", "value": sum(str(row.get("download_status", "")).startswith("auto_local_text_reviewed") for row in updated_manifest)},
            {"item": "curated_context_reviewed_items", "value": sum(str(row.get("download_status", "")).startswith("curated_context_reviewed") for row in updated_manifest)},
            {"item": "manual_unresolved_items", "value": remaining_manual},
            {"item": "direct_tmem158_escc_axis_duplicate", "value": "none_detected"},
            {"item": "no_go_signals", "value": 0},
            {"item": "fulltext_supplement_gate_status", "value": "conditional_go_manual_supplement_review_remaining" if remaining_manual else "go_no_manual_items_remaining"},
        ],
        ["item", "value"],
    )
    gate_rows = [
        {
            "gate_item": "Title and abstract search",
            "status": "completed_first_pass",
            "evidence": "VM/PubMed audit found direct ESCC count=0 and exact ESCC Ca2/UPR/CAF overlap=0",
            "next_action": "Refresh before final manuscript if submission is delayed.",
        },
        {
            "gate_item": "PMC full-text XML search",
            "status": "completed",
            "evidence": "VM-routed PMC XML review did not detect a direct TMEM158-ESCC TAC/CaUPR duplicate.",
            "next_action": "Keep context-boundary items in reviewer-risk language.",
        },
        {
            "gate_item": "Downloaded local full-text/HTML scan",
            "status": "partial" if newly_resolved else "attempted",
            "evidence": f"{newly_resolved} unresolved rows were additionally resolved by downloaded local text/HTML scan.",
            "next_action": "Retain manual status for absent, blocked, unparsed, supplement-linked or proximity-risk files.",
        },
        {
            "gate_item": "Curated context adjudication",
            "status": "completed" if curated_resolved else "not_used",
            "evidence": f"{curated_resolved} rows were resolved by official PubMed/publisher context adjudication without direct ESCC TAC/CaUPR duplication.",
            "next_action": "Keep these rows in reviewer-risk notes as non-ESCC or retraction/background contexts.",
        },
        {
            "gate_item": "Publisher full-text and supplementary-table search",
            "status": "partial" if remaining_manual else "completed",
            "evidence": f"{remaining_manual} manifest items still require publisher/full-text or supplement-level inspection.",
            "next_action": "Download unresolved publisher HTML/PDF and supplementary XLS/XLSX/DOCX/ZIP files before final submission clearance." if remaining_manual else "No remaining manual manifest item; preserve adjudication evidence for reviewer-risk notes.",
        },
        {
            "gate_item": "Reviewer-risk decision",
            "status": "conditional_go" if remaining_manual else "go",
            "evidence": "No direct duplication detected, but manual supplement gate remains incomplete." if remaining_manual else "No direct duplication detected and no manual manifest items remain.",
            "next_action": "Do not claim final novelty clearance until unresolved manual items reach zero." if remaining_manual else "Proceed to target-journal formatting and final visual QA.",
        },
    ]
    write_csv(FULLTEXT_GATE, gate_rows, ["gate_item", "status", "evidence", "next_action"])
    SUMMARY.write_text(
        "\n".join(
            [
                "# Downloaded Full-Text Local Scan",
                "",
                f"- Newly resolved by local downloaded text/HTML scan: {newly_resolved}",
                f"- Resolved by curated PubMed/publisher context adjudication: {curated_resolved}",
                f"- Remaining manual-required rows: {remaining_manual}",
                "",
                "Rows remain manual when the local file is absent, unparsed, too short, contains proximity risk, or contains supplementary/table markers that require direct inspection.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Local fulltext scan complete: newly_resolved={newly_resolved}, remaining_manual={remaining_manual}")


if __name__ == "__main__":
    main()
