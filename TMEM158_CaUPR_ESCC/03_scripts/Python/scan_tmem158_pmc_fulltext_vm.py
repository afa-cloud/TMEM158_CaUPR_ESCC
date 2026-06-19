#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import shlex
import subprocess
from pathlib import Path


BRANCH = Path(__file__).resolve().parents[2]
LIT_DIR = BRANCH / "01_literature"
LOG_DIR = BRANCH / "logs"
RECORDS = LIT_DIR / "tmem158_pubmed_pmc_duplication_records.csv"
SCAN = LIT_DIR / "tmem158_pmc_fulltext_term_scan.csv"
CONTEXT = LIT_DIR / "tmem158_pmc_fulltext_context_hits.csv"
STATUS = LIT_DIR / "tmem158_pmc_fulltext_scan_status.csv"
LOG = LOG_DIR / "tmem158_pmc_fulltext_scan_vm.log"

VM_WORKSPACE = Path("/Users/gdbhcx/Documents/Codex/2026-05-20/tls-osdwan-ncbi-codex-ncbi-tls")
VM_KEY = VM_WORKSPACE / "vm" / "ncbi-ubuntu-bridged" / "keys" / "ncbi_vm_ed25519"
VM_HOST = "codex@192.168.64.3"

LOG_DIR.mkdir(parents=True, exist_ok=True)


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


def collect_pmc_records(limit: int = 80) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    if not RECORDS.exists():
        raise FileNotFoundError(RECORDS)
    with RECORDS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pmc_id = ""
            if row.get("database") == "pmc":
                pmc_id = str(row.get("id", "")).strip()
            elif "PMC" in str(row.get("pmcid", "")):
                match = re.search(r"PMC(\d+)", str(row.get("pmcid", "")))
                if match:
                    pmc_id = match.group(1)
            if not pmc_id or pmc_id in seen:
                continue
            seen.add(pmc_id)
            rows.append({
                "pmc_id": pmc_id,
                "title": str(row.get("title", "")),
                "category": str(row.get("category", "")),
                "url": str(row.get("url", "")) or f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/",
            })
            if len(rows) >= limit:
                break
    return rows


REMOTE_TEMPLATE = r'''
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

records = __RECORDS__
base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

alias_patterns = [
    r"\bTMEM158\b",
    r"\bHBBP\b",
    r"\bp40BBp\b",
    r"\bp40BBP\b",
    r"transmembrane protein 158",
    r"\bENSG00000249992\b",
]
ris1_patterns = [r"\bRIS1\b", r"Ras-induced senescence-1"]
escc_patterns = [
    r"\bESCC\b",
    r"esophageal squamous cell carcinoma",
    r"oesophageal squamous cell carcinoma",
    r"esophageal cancer",
    r"oesophageal cancer",
    r"esophageal carcinoma",
    r"oesophageal carcinoma",
]
caupr_patterns = [
    r"calcium", r"\bCa2\b", r"Ca2\+", r"\bSOCE\b", r"\bSTIM1\b", r"\bORAI1\b",
    r"\bUPR\b", r"unfolded protein response", r"endoplasmic reticulum stress",
    r"\bER stress\b", r"\bPERK\b", r"\bEIF2AK3\b", r"\bIRE1\b", r"\bERN1\b",
    r"\bXBP1\b", r"\bATF6\b"
]
caf_patterns = [
    r"\bCAF\b", r"cancer-associated fibroblast", r"fibroblast", r"fibroblasts",
    r"stromal", r"stroma", r"tumor microenvironment", r"tumour microenvironment",
    r"extracellular matrix", r"\bECM\b"
]
signature_patterns = [
    r"prognos", r"survival", r"immune", r"infiltration", r"biomarker",
    r"diagnostic", r"multi-omics", r"multiomics", r"signature", r"single-cell",
    r"single cell", r"supplement", r"supplementary"
]

compiled = {
    "alias": [re.compile(p, re.I) for p in alias_patterns],
    "ris1": [re.compile(p, re.I) for p in ris1_patterns],
    "escc": [re.compile(p, re.I) for p in escc_patterns],
    "caupr": [re.compile(p, re.I) for p in caupr_patterns],
    "caf": [re.compile(p, re.I) for p in caf_patterns],
    "signature": [re.compile(p, re.I) for p in signature_patterns],
}


def fetch_text(pmc_id):
    params = {
        "db": "pmc",
        "id": pmc_id,
        "retmode": "xml",
        "tool": "codex_tmem158_fulltext_scan",
        "email": "codex@example.com",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Codex-TMEM158-FulltextScan/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read()
    try:
        root = ET.fromstring(raw)
        text = " ".join(part.strip() for part in root.itertext() if part and part.strip())
    except Exception:
        text = raw.decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def positions(patterns, text):
    pos = []
    terms = []
    for pat in patterns:
        for match in pat.finditer(text):
            pos.append(match.start())
            terms.append(match.group(0))
    return sorted(pos), sorted(set(terms), key=str.lower)


def near(a, b, window=2000):
    return bool(a and b and min(abs(x - y) for x in a for y in b) <= window)


scan_rows = []
context_rows = []
for rec in records:
    pmc_id = rec["pmc_id"]
    row = {
        "pmc_id": pmc_id,
        "title": rec.get("title", ""),
        "category": rec.get("category", ""),
        "url": rec.get("url", "") or ("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC" + pmc_id + "/"),
        "fetch_status": "ok",
    }
    try:
        text = fetch_text(pmc_id)
        pos_alias, terms_alias = positions(compiled["alias"], text)
        pos_ris1, terms_ris1 = positions(compiled["ris1"], text)
        pos_escc, terms_escc = positions(compiled["escc"], text)
        pos_caupr, terms_caupr = positions(compiled["caupr"], text)
        pos_caf, terms_caf = positions(compiled["caf"], text)
        pos_sig, terms_sig = positions(compiled["signature"], text)
        row.update({
            "text_chars": len(text),
            "exact_alias_hits": len(pos_alias),
            "ris1_hits": len(pos_ris1),
            "escc_hits": len(pos_escc),
            "caupr_hits": len(pos_caupr),
            "caf_hits": len(pos_caf),
            "signature_hits": len(pos_sig),
            "alias_terms": ";".join(terms_alias),
            "ris1_terms": ";".join(terms_ris1),
            "escc_terms": ";".join(terms_escc),
            "caupr_terms": ";".join(terms_caupr[:20]),
            "caf_terms": ";".join(terms_caf[:20]),
            "alias_near_escc": int(near(pos_alias, pos_escc)),
            "alias_near_caupr": int(near(pos_alias, pos_caupr)),
            "alias_near_caf": int(near(pos_alias, pos_caf)),
            "alias_near_signature": int(near(pos_alias, pos_sig)),
            "ris1_near_escc": int(near(pos_ris1, pos_escc)),
        })
        if pos_alias and near(pos_alias, pos_escc) and (near(pos_alias, pos_caupr) or near(pos_alias, pos_caf) or near(pos_alias, pos_sig)):
            risk = "manual_high_priority_exact_alias_escc_context"
        elif pos_alias and near(pos_alias, pos_escc):
            risk = "manual_priority_exact_alias_escc_context"
        elif pos_alias and pos_escc:
            risk = "exact_alias_and_escc_in_same_article_not_near"
        elif pos_alias:
            risk = "exact_alias_non_escc_or_review_context"
        elif pos_ris1:
            risk = "ris1_only_noise_or_legacy_context"
        else:
            risk = "no_alias_after_xml_fetch"
        row["risk_class"] = risk
        for label, positions_list in [("exact_alias", pos_alias[:5]), ("ris1", pos_ris1[:3])]:
            for p in positions_list:
                start = max(0, p - 220)
                end = min(len(text), p + 220)
                snippet = text[start:end]
                context_rows.append({
                    "pmc_id": pmc_id,
                    "title": rec.get("title", ""),
                    "hit_type": label,
                    "risk_class": risk,
                    "context": snippet,
                })
    except Exception as exc:
        row.update({
            "fetch_status": "error:" + str(exc),
            "text_chars": 0,
            "exact_alias_hits": 0,
            "ris1_hits": 0,
            "escc_hits": 0,
            "caupr_hits": 0,
            "caf_hits": 0,
            "signature_hits": 0,
            "risk_class": "fetch_failed_manual_required",
        })
    scan_rows.append(row)
    time.sleep(0.34)

print(json.dumps({"scan": scan_rows, "contexts": context_rows}, ensure_ascii=False))
'''


def run_vm(records: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    if not VM_KEY.exists():
        raise FileNotFoundError(f"Missing VM key: {VM_KEY}")
    remote = REMOTE_TEMPLATE.replace("__RECORDS__", json.dumps(records, ensure_ascii=False))
    cmd = [
        "ssh",
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-i", str(VM_KEY),
        VM_HOST,
        "python3 -c " + shlex.quote(remote),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=1800)
    LOG.write_text(proc.stdout + "\nSTDERR:\n" + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"VM PMC fulltext scan failed: {proc.returncode}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> None:
    records = collect_pmc_records()
    data = run_vm(records)
    scan_rows = data.get("scan", [])
    context_rows = data.get("contexts", [])
    write_csv(SCAN, scan_rows)
    write_csv(CONTEXT, context_rows, ["pmc_id", "title", "hit_type", "risk_class", "context"])
    risk_counts: dict[str, int] = {}
    for row in scan_rows:
        risk = str(row.get("risk_class", "unknown"))
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    status_rows = [
        {"item": "module_status", "value": "completed"},
        {"item": "route", "value": "PMC EFetch full-text XML via UTM VM"},
        {"item": "pmc_records_scanned", "value": len(scan_rows)},
        {"item": "exact_alias_records", "value": sum(int(row.get("exact_alias_hits", 0) or 0) > 0 for row in scan_rows)},
        {"item": "exact_alias_and_escc_anywhere_records", "value": sum((int(row.get("exact_alias_hits", 0) or 0) > 0 and int(row.get("escc_hits", 0) or 0) > 0) for row in scan_rows)},
        {"item": "exact_alias_near_escc_records", "value": sum(int(row.get("alias_near_escc", 0) or 0) > 0 for row in scan_rows)},
        {"item": "manual_high_priority_exact_alias_escc_context", "value": risk_counts.get("manual_high_priority_exact_alias_escc_context", 0)},
        {"item": "manual_priority_exact_alias_escc_context", "value": risk_counts.get("manual_priority_exact_alias_escc_context", 0)},
        {"item": "exact_alias_and_escc_in_same_article_not_near", "value": risk_counts.get("exact_alias_and_escc_in_same_article_not_near", 0)},
        {"item": "ris1_only_noise_or_legacy_context", "value": risk_counts.get("ris1_only_noise_or_legacy_context", 0)},
        {"item": "no_alias_after_xml_fetch", "value": risk_counts.get("no_alias_after_xml_fetch", 0)},
    ]
    write_csv(STATUS, status_rows)


if __name__ == "__main__":
    main()
