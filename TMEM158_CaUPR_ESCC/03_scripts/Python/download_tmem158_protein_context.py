#!/usr/bin/env python3

import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "02_data" / "raw" / "protein_context"
VALIDATION_DIR = ROOT / "04_results" / "validation"
QC_DIR = ROOT / "04_results" / "qc"

for directory in (RAW_DIR, VALIDATION_DIR, QC_DIR):
    directory.mkdir(parents=True, exist_ok=True)

FORCE = os.environ.get("TMEM158_PROTEIN_REFRESH", "0") == "1"


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fieldnames is None:
        keys = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ["item", "value"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fetch(url, path, binary=False):
    if path.exists() and path.stat().st_size > 0 and not FORCE:
        return {"status": "cached", "bytes": path.stat().st_size, "error": ""}
    request = urllib.request.Request(url, headers={"User-Agent": "Codex public-data workflow"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        mode = "wb" if binary else "w"
        if binary:
            path.write_bytes(payload)
        else:
            path.write_text(payload.decode("utf-8"), encoding="utf-8")
        time.sleep(0.2)
        return {"status": "downloaded", "bytes": path.stat().st_size, "error": ""}
    except Exception as exc:
        return {"status": "failed", "bytes": path.stat().st_size if path.exists() else 0, "error": str(exc)}


def read_json(path):
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def flatten_value(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(flatten_value(v) for v in value if flatten_value(v))
    if isinstance(value, dict):
        return "; ".join(f"{k}: {flatten_value(v)}" for k, v in value.items() if flatten_value(v))
    return str(value)


def first_value(value, default=""):
    if value is None:
        return default
    if isinstance(value, list):
        return first_value(value[0], default) if value else default
    return value


def get_prop(ref, key):
    for prop in ref.get("properties", []) or []:
        if prop.get("key") == key:
            return prop.get("value", "")
    return ""


uniprot_url = "https://rest.uniprot.org/uniprotkb/search?" + urllib.parse.urlencode({
    "query": "gene_exact:TMEM158 AND organism_id:9606",
    "format": "json",
    "fields": "accession,id,gene_names,protein_name,organism_name,xref_ensembl,xref_hpa,cc_subcellular_location,go_c,sequence",
})
uniprot_path = RAW_DIR / "TMEM158_uniprot_search.json"

download_status = []
status = fetch(uniprot_url, uniprot_path)
download_status.append({
    "source": "UniProt",
    "url": uniprot_url,
    "local_path": str(uniprot_path),
    **status,
})

uniprot = read_json(uniprot_path) or {}
results = uniprot.get("results", []) or []
reviewed = None
for result in results:
    if "reviewed" in result.get("entryType", "").lower():
        reviewed = result
        break
if reviewed is None and results:
    reviewed = results[0]

accession = reviewed.get("primaryAccession", "") if reviewed else ""
entry_id = reviewed.get("uniProtkbId", "") if reviewed else ""
entry_type = reviewed.get("entryType", "") if reviewed else ""
protein_name = ""
gene_name = "TMEM158"
synonyms = []
sequence_length = ""
sequence_mass = ""
subcellular_location = ""
topology = ""
subcellular_evidence = ""
ensembl_gene = ""
hpa_ensembl = ""

if reviewed:
    protein_name = (((reviewed.get("proteinDescription", {}) or {}).get("recommendedName", {}) or {})
                    .get("fullName", {}) or {}).get("value", "")
    genes = reviewed.get("genes", []) or []
    if genes:
        gene_name = ((genes[0].get("geneName", {}) or {}).get("value", "")) or gene_name
        synonyms = [(syn.get("value", "") or "") for syn in genes[0].get("synonyms", []) or []]
    sequence = reviewed.get("sequence", {}) or {}
    sequence_length = sequence.get("length", "")
    sequence_mass = sequence.get("molWeight", "")
    for comment in reviewed.get("comments", []) or []:
        if comment.get("commentType") == "SUBCELLULAR LOCATION":
            locations = comment.get("subcellularLocations", []) or []
            if locations:
                loc = locations[0]
                subcellular_location = ((loc.get("location", {}) or {}).get("value", "")) or ""
                topology = ((loc.get("topology", {}) or {}).get("value", "")) or ""
                evidences = ((loc.get("location", {}) or {}).get("evidences", []) or []) + ((loc.get("topology", {}) or {}).get("evidences", []) or [])
                subcellular_evidence = "; ".join(sorted(set(e.get("evidenceCode", "") for e in evidences if e.get("evidenceCode"))))
    for ref in reviewed.get("uniProtKBCrossReferences", []) or []:
        if ref.get("database") == "Ensembl" and not ensembl_gene:
            ensembl_gene = get_prop(ref, "GeneId").split(".")[0]
        if ref.get("database") == "HPA" and not hpa_ensembl:
            hpa_ensembl = ref.get("id", "")

hpa_search_url = "https://www.proteinatlas.org/search/TMEM158?format=json"
hpa_search_path = RAW_DIR / "TMEM158_hpa_search.json"
status = fetch(hpa_search_url, hpa_search_path)
download_status.append({
    "source": "Human Protein Atlas search",
    "url": hpa_search_url,
    "local_path": str(hpa_search_path),
    **status,
})

hpa_search = read_json(hpa_search_path) or []
if not hpa_ensembl and isinstance(hpa_search, list) and hpa_search:
    hpa_ensembl = hpa_search[0].get("Ensembl", "")

hpa_json = {}
if hpa_ensembl:
    hpa_json_url = f"https://www.proteinatlas.org/{hpa_ensembl}.json"
    hpa_tsv_url = f"https://www.proteinatlas.org/{hpa_ensembl}.tsv"
    hpa_json_path = RAW_DIR / f"TMEM158_HPA_{hpa_ensembl}.json"
    hpa_tsv_path = RAW_DIR / f"TMEM158_HPA_{hpa_ensembl}.tsv"
    for source, url, path in [
        ("Human Protein Atlas JSON", hpa_json_url, hpa_json_path),
        ("Human Protein Atlas TSV", hpa_tsv_url, hpa_tsv_path),
    ]:
        status = fetch(url, path)
        download_status.append({"source": source, "url": url, "local_path": str(path), **status})
    hpa_json = read_json(hpa_json_path) or {}
    if isinstance(hpa_json, list) and hpa_json:
        hpa_json = hpa_json[0]

quickgo_rows = []
if accession:
    quickgo_url = "https://www.ebi.ac.uk/QuickGO/services/annotation/search?" + urllib.parse.urlencode({
        "geneProductId": f"UniProtKB:{accession}",
        "aspect": "cellular_component",
        "limit": "100",
    })
    quickgo_path = RAW_DIR / "TMEM158_quickgo_cellular_component.json"
    status = fetch(quickgo_url, quickgo_path)
    download_status.append({
        "source": "QuickGO cellular component",
        "url": quickgo_url,
        "local_path": str(quickgo_path),
        **status,
    })
    quickgo = read_json(quickgo_path) or {}
    for result in quickgo.get("results", []) or []:
        quickgo_rows.append({
            "source": "QuickGO",
            "term_id": result.get("goId", ""),
            "term_name": result.get("goName", "") or "",
            "aspect": result.get("aspect", "") or "cellular_component",
            "evidence": result.get("goEvidence", ""),
            "assigned_by": result.get("assignedBy", ""),
            "reference": flatten_value(result.get("reference", "")),
        })

uniprot_go_rows = []
if reviewed:
    for ref in reviewed.get("uniProtKBCrossReferences", []) or []:
        if ref.get("database") != "GO":
            continue
        go_term = get_prop(ref, "GoTerm")
        if not go_term.startswith("C:"):
            continue
        uniprot_go_rows.append({
            "source": "UniProt",
            "term_id": ref.get("id", ""),
            "term_name": go_term.replace("C:", "", 1),
            "aspect": "cellular_component",
            "evidence": get_prop(ref, "GoEvidenceType"),
            "assigned_by": "UniProt",
            "reference": "",
        })

localization_rows = uniprot_go_rows + quickgo_rows
write_csv(
    VALIDATION_DIR / "tmem158_uniprot_quickgo_localization.csv",
    localization_rows,
    ["source", "term_id", "term_name", "aspect", "evidence", "assigned_by", "reference"],
)

hpa_summary_fields = [
    "Gene", "Gene synonym", "Ensembl", "Gene description", "Uniprot", "Protein class",
    "Evidence", "HPA evidence", "UniProt evidence", "NeXtProt evidence",
    "RNA tissue specificity", "RNA tissue distribution", "RNA single cell type specificity",
    "RNA single cell type distribution", "RNA cancer specificity", "RNA cancer distribution",
    "Protein tissue specificity", "Protein tissue distribution", "Antibody",
    "Reliability (IH)", "Reliability (IF)", "Subcellular location", "Subcellular main location",
]
hpa_summary = [{"field": field, "value": flatten_value(hpa_json.get(field, ""))} for field in hpa_summary_fields]
hnsc = hpa_json.get("Cancer prognostics - Head and Neck Squamous Cell Carcinoma (TCGA)", {}) if isinstance(hpa_json, dict) else {}
if hnsc:
    hpa_summary.append({"field": "HNSC TCGA prognostic context", "value": flatten_value(hnsc)})
write_csv(VALIDATION_DIR / "tmem158_hpa_context_summary.csv", hpa_summary, ["field", "value"])

sc = hpa_json.get("RNA single cell type specific nCPM", {}) if isinstance(hpa_json, dict) else {}
sc_rows = []
if isinstance(sc, dict):
    for cell_type, value in sc.items():
        try:
            numeric = float(value)
        except Exception:
            numeric = ""
        sc_rows.append({"cell_type": cell_type, "nCPM": numeric})
sc_rows.sort(key=lambda row: float(row["nCPM"]) if row["nCPM"] != "" else -1, reverse=True)
for idx, row in enumerate(sc_rows, start=1):
    row["rank"] = idx
write_csv(VALIDATION_DIR / "tmem158_hpa_single_cell_context.csv", sc_rows, ["rank", "cell_type", "nCPM"])

summary_rows = [
    {"source": "UniProt", "item": "reviewed_accession", "value": accession, "evidence_level": entry_type, "interpretation": "reviewed protein entry"},
    {"source": "UniProt", "item": "protein_name", "value": protein_name, "evidence_level": entry_type, "interpretation": "lead protein identity"},
    {"source": "UniProt", "item": "gene_synonyms", "value": "; ".join(synonyms), "evidence_level": entry_type, "interpretation": "alias audit for literature search"},
    {"source": "UniProt", "item": "sequence_length_aa", "value": sequence_length, "evidence_level": entry_type, "interpretation": "protein measurability context"},
    {"source": "UniProt", "item": "subcellular_location", "value": subcellular_location, "evidence_level": subcellular_evidence, "interpretation": "membrane plausibility, not ESCC-specific localization"},
    {"source": "UniProt", "item": "topology", "value": topology, "evidence_level": subcellular_evidence, "interpretation": "transmembrane topology plausibility"},
    {"source": "QuickGO/UniProt", "item": "cellular_component_terms", "value": "; ".join(sorted(set(row.get("term_name", "") or row.get("term_id", "") for row in localization_rows))), "evidence_level": "; ".join(sorted(set(row.get("evidence", "") for row in localization_rows if row.get("evidence")))), "interpretation": "knowledgebase localization terms"},
    {"source": "HPA", "item": "ensembl_id", "value": hpa_ensembl, "evidence_level": "HPA entry", "interpretation": "public protein atlas identity"},
    {"source": "HPA", "item": "protein_class", "value": flatten_value(hpa_json.get("Protein class", "")), "evidence_level": flatten_value(hpa_json.get("Evidence", "")), "interpretation": "public membrane-protein class"},
    {"source": "HPA", "item": "antibody", "value": flatten_value(hpa_json.get("Antibody", "")), "evidence_level": flatten_value(hpa_json.get("Reliability (IH)", "")), "interpretation": "public antibody/IHC context, not new IHC validation"},
    {"source": "HPA", "item": "subcellular_location", "value": flatten_value(hpa_json.get("Subcellular main location", "")), "evidence_level": flatten_value(hpa_json.get("Reliability (IF)", "")), "interpretation": "subcellular IF availability boundary"},
    {"source": "HPA", "item": "protein_tissue_distribution", "value": flatten_value(hpa_json.get("Protein tissue distribution", "")), "evidence_level": flatten_value(hpa_json.get("Protein tissue specificity", "")), "interpretation": "protein-level tissue boundary"},
    {"source": "HPA", "item": "rna_single_cell_context", "value": "; ".join(f"{row['cell_type']}={row['nCPM']}" for row in sc_rows[:8]), "evidence_level": flatten_value(hpa_json.get("RNA single cell type specificity", "")), "interpretation": "broad public single-cell RNA context, not ESCC tumour microenvironment proof"},
    {"source": "HPA", "item": "hnsc_tcga_prognostic_context", "value": flatten_value(hnsc), "evidence_level": "HPA TCGA prognostic context", "interpretation": "adjacent squamous cancer context, not ESCC survival proof"},
]
write_csv(
    VALIDATION_DIR / "tmem158_public_protein_knowledgebase_summary.csv",
    summary_rows,
    ["source", "item", "value", "evidence_level", "interpretation"],
)

module_status = "completed" if reviewed and hpa_json else "partial_completed"
membrane_support = int("membrane" in (subcellular_location + " " + topology + " " + flatten_value(hpa_json.get("Protein class", ""))).lower())
er_direct_support = int("endoplasmic" in (subcellular_location + " " + flatten_value(localization_rows)).lower())
hpa_subcellular_available = int(bool(flatten_value(hpa_json.get("Subcellular main location", ""))))
hpa_ih_approved = int("approved" in flatten_value(hpa_json.get("Reliability (IH)", "")).lower())

status_rows = [
    {"item": "module_status", "value": module_status},
    {"item": "uniprot_results", "value": len(results)},
    {"item": "uniprot_reviewed_accession", "value": accession},
    {"item": "hpa_ensembl", "value": hpa_ensembl},
    {"item": "quickgo_cellular_component_rows", "value": len(quickgo_rows)},
    {"item": "uniprot_cellular_component_rows", "value": len(uniprot_go_rows)},
    {"item": "hpa_single_cell_rows", "value": len(sc_rows)},
    {"item": "membrane_support", "value": membrane_support},
    {"item": "er_direct_support", "value": er_direct_support},
    {"item": "hpa_subcellular_available", "value": hpa_subcellular_available},
    {"item": "hpa_ih_approved", "value": hpa_ih_approved},
    {"item": "interpretation", "value": "public_membrane_protein_context_not_escc_localization_or_causal_proof"},
]
write_csv(QC_DIR / "tmem158_public_protein_context_status.csv", status_rows, ["item", "value"])
write_csv(QC_DIR / "tmem158_public_protein_context_download_status.csv", download_status,
          ["source", "url", "local_path", "status", "bytes", "error"])

failed = [row for row in download_status if row.get("status") == "failed"]
if failed:
    print("Some protein-context downloads failed; cached/partial outputs were written.", file=sys.stderr)
sys.exit(0)
