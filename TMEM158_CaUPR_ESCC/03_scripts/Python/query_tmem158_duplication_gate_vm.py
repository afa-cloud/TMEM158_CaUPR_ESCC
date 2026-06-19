#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import shlex
import subprocess
from pathlib import Path


BRANCH = Path(__file__).resolve().parents[2]
LIT_DIR = BRANCH / "01_literature"
LOG_DIR = BRANCH / "logs"
STATUS = LIT_DIR / "tmem158_duplication_gate_status.csv"
COUNTS = LIT_DIR / "tmem158_pubmed_pmc_duplication_counts.csv"
RECORDS = LIT_DIR / "tmem158_pubmed_pmc_duplication_records.csv"
MANIFEST = LIT_DIR / "manual_download_manifest.csv"
INSTRUCTIONS = LIT_DIR / "manual_download_instructions.md"
DOWNLOADER = BRANCH / "03_scripts" / "Python" / "download_missing_fulltexts.py"
LOG = LOG_DIR / "tmem158_duplication_gate_vm.log"

VM_WORKSPACE = Path("/Users/gdbhcx/Documents/Codex/2026-05-20/tls-osdwan-ncbi-codex-ncbi-tls")
VM_KEY = VM_WORKSPACE / "vm" / "ncbi-ubuntu-bridged" / "keys" / "ncbi_vm_ed25519"
VM_HOST = "codex@192.168.64.3"

for directory in [LIT_DIR, LOG_DIR, DOWNLOADER.parent]:
    directory.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["item", "value"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


REMOTE = r'''
import json
import sys
import time
import urllib.parse
import urllib.request

base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

gene_alias = '(TMEM158[tiab] OR HBBP[tiab] OR p40BBp[tiab] OR p40BBP[tiab] OR "transmembrane protein 158"[tiab] OR ENSG00000249992[tiab])'
ris1_guarded = '(RIS1[tiab] AND (TMEM158[tiab] OR HBBP[tiab] OR p40BBp[tiab] OR p40BBP[tiab] OR "transmembrane protein 158"[tiab] OR Ras[tiab] OR senescence[tiab]))'
gene_all = '(' + gene_alias + ' OR ' + ris1_guarded + ')'
escc = '(ESCC[tiab] OR "esophageal squamous cell carcinoma"[tiab] OR "oesophageal squamous cell carcinoma"[tiab] OR "esophageal cancer"[tiab] OR "oesophageal cancer"[tiab] OR "esophageal carcinoma"[tiab] OR "oesophageal carcinoma"[tiab])'
caupr = '(calcium[tiab] OR Ca2[tiab] OR Ca2+[tiab] OR SOCE[tiab] OR STIM1[tiab] OR ORAI1[tiab] OR UPR[tiab] OR "unfolded protein response"[tiab] OR "endoplasmic reticulum stress"[tiab] OR "ER stress"[tiab] OR PERK[tiab] OR EIF2AK3[tiab] OR IRE1[tiab] OR ERN1[tiab] OR XBP1[tiab] OR ATF6[tiab])'
caf = '(CAF[tiab] OR "cancer-associated fibroblast"[tiab] OR fibroblast[tiab] OR fibroblasts[tiab] OR stromal[tiab] OR stroma[tiab] OR "tumor microenvironment"[tiab] OR "tumour microenvironment"[tiab] OR "extracellular matrix"[tiab] OR ECM[tiab])'
signature = '(prognosis[tiab] OR prognostic[tiab] OR survival[tiab] OR immune[tiab] OR infiltration[tiab] OR biomarker[tiab] OR diagnostic[tiab] OR "multi-omics"[tiab] OR multiomics[tiab] OR signature[tiab] OR "single-cell"[tiab] OR "single cell"[tiab] OR methylation[tiab] OR CNV[tiab] OR "drug sensitivity"[tiab] OR chemoresistance[tiab])'
cancer = '(cancer[tiab] OR cancers[tiab] OR tumor[tiab] OR tumour[tiab] OR carcinoma[tiab] OR neoplasm[tiab])'

pmc_gene_alias = '(TMEM158 OR HBBP OR p40BBp OR p40BBP OR "transmembrane protein 158" OR ENSG00000249992)'
pmc_ris1_guarded = '(RIS1 AND (TMEM158 OR HBBP OR p40BBp OR p40BBP OR "transmembrane protein 158" OR Ras OR senescence))'
pmc_gene_all = '(' + pmc_gene_alias + ' OR ' + pmc_ris1_guarded + ')'
pmc_escc = '(ESCC OR "esophageal squamous cell carcinoma" OR "oesophageal squamous cell carcinoma" OR "esophageal cancer" OR "oesophageal cancer" OR "esophageal carcinoma" OR "oesophageal carcinoma")'
pmc_caupr = '(calcium OR Ca2 OR SOCE OR UPR OR "unfolded protein response" OR "endoplasmic reticulum stress" OR "ER stress" OR PERK OR IRE1 OR XBP1 OR ATF6)'
pmc_caf = '(CAF OR "cancer-associated fibroblast" OR fibroblast OR stromal OR stroma OR "tumor microenvironment" OR "extracellular matrix" OR ECM)'
pmc_signature = '(prognosis OR prognostic OR survival OR immune OR infiltration OR biomarker OR diagnostic OR multiomics OR "multi-omics" OR signature OR supplement OR supplementary)'

queries = {
    "pubmed_alias_direct_escc": ("pubmed", gene_all + " AND " + escc),
    "pubmed_alias_escc_caupr": ("pubmed", gene_all + " AND " + escc + " AND " + caupr),
    "pubmed_alias_escc_caf": ("pubmed", gene_all + " AND " + escc + " AND " + caf),
    "pubmed_alias_escc_signature": ("pubmed", gene_all + " AND " + escc + " AND " + signature),
    "pubmed_alias_pan_cancer_signature": ("pubmed", gene_all + " AND " + cancer + " AND " + signature),
    "pubmed_alias_cancer_caupr": ("pubmed", gene_all + " AND " + cancer + " AND " + caupr),
    "pubmed_alias_cancer_caf": ("pubmed", gene_all + " AND " + cancer + " AND " + caf),
    "pubmed_tmem_review": ("pubmed", '(TMEM158[tiab] OR "transmembrane protein 158"[tiab]) AND (review[pt] OR review[tiab] OR "research progress"[tiab])'),
    "pubmed_ris1_broad_escc": ("pubmed", 'RIS1[tiab] AND ' + escc),
    "pmc_fulltext_exact_alias_escc": ("pmc", pmc_gene_alias + " AND " + pmc_escc),
    "pmc_fulltext_exact_alias_escc_caupr": ("pmc", pmc_gene_alias + " AND " + pmc_escc + " AND " + pmc_caupr),
    "pmc_fulltext_exact_alias_escc_caf": ("pmc", pmc_gene_alias + " AND " + pmc_escc + " AND " + pmc_caf),
    "pmc_fulltext_exact_alias_escc_signature": ("pmc", pmc_gene_alias + " AND " + pmc_escc + " AND " + pmc_signature),
    "pmc_fulltext_ris1_guarded_escc": ("pmc", pmc_ris1_guarded + " AND " + pmc_escc),
    "pmc_fulltext_ris1_guarded_escc_caupr": ("pmc", pmc_ris1_guarded + " AND " + pmc_escc + " AND " + pmc_caupr),
    "pmc_fulltext_ris1_guarded_escc_caf": ("pmc", pmc_ris1_guarded + " AND " + pmc_escc + " AND " + pmc_caf),
    "pmc_fulltext_alias_pan_cancer_signature": ("pmc", pmc_gene_all + " AND " + pmc_signature),
}


def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Codex-TMEM158-DuplicationGate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def esearch(db, term, retmax=20):
    params = {
        "db": db,
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "relevance",
        "tool": "codex_tmem158_duplication_gate",
        "email": "codex@example.com",
    }
    url = base + "esearch.fcgi?" + urllib.parse.urlencode(params)
    data = request_json(url)
    result = data.get("esearchresult", {})
    return int(result.get("count", 0)), result.get("idlist", [])


def esummary(db, ids):
    if not ids:
        return []
    params = {
        "db": db,
        "id": ",".join(ids),
        "retmode": "json",
        "tool": "codex_tmem158_duplication_gate",
        "email": "codex@example.com",
    }
    url = base + "esummary.fcgi?" + urllib.parse.urlencode(params)
    data = request_json(url)
    records = []
    result = data.get("result", {})
    for ident in ids:
        item = result.get(ident, {})
        if not item:
            continue
        articleids = item.get("articleids", []) or []
        doi = ""
        pmcid = ""
        for aid in articleids:
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
            if aid.get("idtype") in ("pmc", "pmcid"):
                pmcid = aid.get("value", "")
        records.append({
            "id": ident,
            "title": item.get("title", ""),
            "journal": item.get("fulljournalname", item.get("source", "")),
            "pubdate": item.get("pubdate", ""),
            "doi": doi,
            "pmcid": pmcid,
        })
    return records


count_rows = []
record_rows = []
for category, (db, term) in queries.items():
    try:
        count, ids = esearch(db, term)
        count_rows.append({
            "category": category,
            "database": db,
            "count": count,
            "top_ids": ";".join(ids),
            "query": term,
            "status": "ok",
        })
        for rank, rec in enumerate(esummary(db, ids[:10]), start=1):
            rec.update({"category": category, "database": db, "rank": rank})
            if db == "pubmed":
                rec["url"] = "https://pubmed.ncbi.nlm.nih.gov/" + rec["id"] + "/"
            else:
                rec["url"] = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC" + rec["id"] + "/"
            record_rows.append(rec)
    except Exception as exc:
        count_rows.append({
            "category": category,
            "database": db,
            "count": "NA",
            "top_ids": "",
            "query": term,
            "status": "error:" + str(exc),
        })
    time.sleep(0.34)

print(json.dumps({"counts": count_rows, "records": record_rows}, ensure_ascii=False))
'''


def run_vm_query() -> dict[str, list[dict[str, object]]]:
    if not VM_KEY.exists():
        raise FileNotFoundError(f"Missing VM key: {VM_KEY}")
    cmd = [
        "ssh",
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-i", str(VM_KEY),
        VM_HOST,
        "python3 -c " + shlex.quote(REMOTE),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=600)
    LOG.write_text(proc.stdout + "\nSTDERR:\n" + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"VM PubMed/PMC duplication gate failed: {proc.returncode}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def make_manual_manifest(records: list[dict[str, object]]) -> list[dict[str, object]]:
    risk_words = (
        "signature", "multi-omics", "multiomics", "pan-cancer", "pancancer", "prognos",
        "immune", "microenvironment", "stromal", "fibroblast", "caf", "chemoresistance",
        "drug resistance", "review", "single-cell", "single cell"
    )
    manifest: list[dict[str, object]] = []
    seen: set[str] = set()
    for rec in records:
        title = str(rec.get("title", ""))
        category = str(rec.get("category", ""))
        db = str(rec.get("database", ""))
        ident = str(rec.get("id", ""))
        doi = str(rec.get("doi", ""))
        pmcid = str(rec.get("pmcid", ""))
        text = (title + " " + category).lower()
        if db == "pmc" or any(word in text for word in risk_words) or "escc" in category or "esophageal" in text:
            key = db + ":" + ident
            if key in seen:
                continue
            seen.add(key)
            if db == "pubmed":
                url = str(rec.get("url", ""))
                if doi:
                    url = "https://doi.org/" + doi
            else:
                url = str(rec.get("url", ""))
            manifest.append({
                "item_id": f"DG{len(manifest) + 1:03d}",
                "source_article": title,
                "file_label": "full_text_and_supplementary_files",
                "url": url,
                "doi_or_pmid": doi or ident,
                "expected_filename": f"{db}_{ident}_fulltext_or_supplement",
                "target_relative_path": f"01_literature/fulltext_gate_files/{db}_{ident}/",
                "file_type": "html_pdf_xlsx_docx_zip_or_supplement",
                "required_for_gate": "yes",
                "download_status": "manual_required",
                "failure_reason": "publisher_fulltext_or_supplementary_tables_not_exhaustively_downloaded_by_eutils",
                "notes": "Search downloaded files for TMEM158, RIS1, HBBP, p40BBp, p40BBP, ENSG00000249992, TAC_high, Ca2, UPR, CAF and ESCC.",
            })
    return manifest[:40]


def write_downloader_script() -> None:
    DOWNLOADER.write_text(
        """#!/usr/bin/env python3
import argparse
import csv
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--manifest', default='TMEM158_CaUPR_ESCC/01_literature/manual_download_manifest.csv')
parser.add_argument('--force', action='store_true')
args = parser.parse_args()

manifest = Path(args.manifest)
project_root = Path.cwd()
failed = []

with manifest.open(newline='', encoding='utf-8') as handle:
    rows = list(csv.DictReader(handle))

for row in rows:
    url = row.get('url', '').strip()
    target_dir = project_root / 'TMEM158_CaUPR_ESCC' / row.get('target_relative_path', '').strip()
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = '.html'
    if url.lower().endswith('.pdf'):
        suffix = '.pdf'
    out = target_dir / (row.get('expected_filename', 'downloaded_file') + suffix)
    if out.exists() and out.stat().st_size > 0 and not args.force:
        print('skip existing', out)
        continue
    if not url:
        failed.append((row.get('item_id'), 'missing URL'))
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Codex manual fulltext downloader'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        out.write_bytes(data)
        print('downloaded', out, len(data), 'bytes')
    except Exception as exc:
        failed.append((row.get('item_id'), str(exc)))

if failed:
    print('\\nFailed items:')
    for item_id, reason in failed:
        print(item_id, reason)
    raise SystemExit(1)
""",
        encoding="utf-8",
    )


def write_instructions(manifest_rows: list[dict[str, object]]) -> None:
    INSTRUCTIONS.write_text(
        f"""# Manual Download Instructions For TMEM158 Duplication Gate

The automated VM PubMed/PMC gate completed, but final submission requires local full-text and supplementary-table inspection.

Manifest:

- `TMEM158_CaUPR_ESCC/01_literature/manual_download_manifest.csv`

Target folder:

- `TMEM158_CaUPR_ESCC/01_literature/fulltext_gate_files/`

Number of manual items:

- {len(manifest_rows)}

## How to run the fallback downloader

From the project root:

```sh
python3 TMEM158_CaUPR_ESCC/03_scripts/Python/download_missing_fulltexts.py
```

To retry existing items:

```sh
python3 TMEM158_CaUPR_ESCC/03_scripts/Python/download_missing_fulltexts.py --force
```

If publisher pages or supplementary files require browser/proxy access, manually download PDFs, HTML pages, XLS/XLSX/DOCX/ZIP supplements into the listed `target_relative_path` folders.

After downloading, tell Codex: `已下载，继续审查`.

Codex will then verify file sizes/readability and search the files for:

- TMEM158
- RIS1
- HBBP
- p40BBp / p40BBP
- ENSG00000249992
- TAC_high
- Ca2 / UPR / CAF / ESCC terms
""",
        encoding="utf-8",
    )


def main() -> None:
    data = run_vm_query()
    counts = data.get("counts", [])
    records = data.get("records", [])
    write_csv(COUNTS, counts, ["category", "database", "count", "top_ids", "query", "status"])
    write_csv(RECORDS, records, ["category", "database", "rank", "id", "title", "journal", "pubdate", "doi", "pmcid", "url"])

    manifest_rows = make_manual_manifest(records)
    write_csv(MANIFEST, manifest_rows, [
        "item_id", "source_article", "file_label", "url", "doi_or_pmid",
        "expected_filename", "target_relative_path", "file_type", "required_for_gate",
        "download_status", "failure_reason", "notes",
    ])
    write_downloader_script()
    write_instructions(manifest_rows)

    count_map = {row.get("category"): int(row.get("count", 0)) for row in counts if str(row.get("count", "")).isdigit()}
    direct_overlap = count_map.get("pubmed_alias_direct_escc", 0)
    exact_axis_overlap = max(
        count_map.get("pubmed_alias_escc_caupr", 0),
        count_map.get("pubmed_alias_escc_caf", 0),
        count_map.get("pmc_fulltext_exact_alias_escc_caupr", 0),
        count_map.get("pmc_fulltext_exact_alias_escc_caf", 0),
        count_map.get("pmc_fulltext_ris1_guarded_escc_caupr", 0),
        count_map.get("pmc_fulltext_ris1_guarded_escc_caf", 0),
    )
    decision = "conditional_go"
    if direct_overlap > 0 and exact_axis_overlap > 0:
        decision = "heightened_risk_conditional_go"
    if direct_overlap > 3 and exact_axis_overlap > 0:
        decision = "possible_no_go_needs_manual_review"

    write_csv(STATUS, [
        {"item": "module_status", "value": "completed"},
        {"item": "route", "value": "PubMed and PMC E-utilities via UTM VM"},
        {"item": "pubmed_alias_direct_escc_count", "value": direct_overlap},
        {"item": "pubmed_alias_escc_caupr_count", "value": count_map.get("pubmed_alias_escc_caupr", 0)},
        {"item": "pubmed_alias_escc_caf_count", "value": count_map.get("pubmed_alias_escc_caf", 0)},
        {"item": "pmc_fulltext_exact_alias_escc_count", "value": count_map.get("pmc_fulltext_exact_alias_escc", 0)},
        {"item": "pmc_fulltext_exact_alias_escc_caupr_count", "value": count_map.get("pmc_fulltext_exact_alias_escc_caupr", 0)},
        {"item": "pmc_fulltext_exact_alias_escc_caf_count", "value": count_map.get("pmc_fulltext_exact_alias_escc_caf", 0)},
        {"item": "pmc_fulltext_ris1_guarded_escc_count", "value": count_map.get("pmc_fulltext_ris1_guarded_escc", 0)},
        {"item": "pmc_fulltext_ris1_guarded_escc_caupr_count", "value": count_map.get("pmc_fulltext_ris1_guarded_escc_caupr", 0)},
        {"item": "pmc_fulltext_ris1_guarded_escc_caf_count", "value": count_map.get("pmc_fulltext_ris1_guarded_escc_caf", 0)},
        {"item": "manual_manifest_items", "value": len(manifest_rows)},
        {"item": "gate_decision", "value": decision},
        {"item": "final_submission_clearance", "value": "not_yet_manual_fulltext_supplement_scan_required"},
    ])


if __name__ == "__main__":
    main()
