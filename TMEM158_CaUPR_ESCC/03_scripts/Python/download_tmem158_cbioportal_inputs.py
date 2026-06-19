#!/usr/bin/env python3
"""Download targeted cBioPortal TCGA-ESCA inputs for TMEM158."""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
RAW = PROJECT / "02_data" / "raw" / "cbioportal_tmem158"
RAW.mkdir(parents=True, exist_ok=True)

API = "https://www.cbioportal.org/api"
STUDY = "esca_tcga_pan_can_atlas_2018"
GENE_SYMBOL = "TMEM158"
GENE_ALIASES = {"TMEM158"}

PROFILES = {
    "gistic": ("esca_tcga_pan_can_atlas_2018_gistic", "esca_tcga_pan_can_atlas_2018_cna"),
    "log2CNA": ("esca_tcga_pan_can_atlas_2018_log2CNA", "esca_tcga_pan_can_atlas_2018_log2CNA"),
    "rna": ("esca_tcga_pan_can_atlas_2018_rna_seq_v2_mrna", "esca_tcga_pan_can_atlas_2018_rna_seq_v2_mrna"),
}
MUTATION_PROFILE = "esca_tcga_pan_can_atlas_2018_mutations"
MUTATION_SAMPLE_LIST = "esca_tcga_pan_can_atlas_2018_sequenced"
METHYLATION_PROFILE = "esca_tcga_pan_can_atlas_2018_methylation_hm450"
METHYLATION_SAMPLE_LIST = "esca_tcga_pan_can_atlas_2018_methylation_hm450"


def request_json(url: str, payload: dict | None = None, timeout: int = 120):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json", "User-Agent": "Codex-public-data-audit/1.0"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    method = "POST" if payload is not None else "GET"
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as handle:
                return json.loads(handle.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"Failed request after retries: {url} ({last_error})")


def write_rows(path: Path, rows: list[dict], fieldnames: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def get_gene_id() -> int:
    cache = RAW / "cbioportal_tmem158_gene.json"
    if cache.exists() and cache.stat().st_size > 0:
        data = json.loads(cache.read_text(encoding="utf-8"))
    else:
        data = request_json(f"{API}/genes/{GENE_SYMBOL}?projection=DETAILED", timeout=30)
        cache.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return int(data["entrezGeneId"])


def fetch_molecular_data(entrez_gene_id: int):
    for label, (profile_id, sample_list_id) in PROFILES.items():
        path = RAW / f"cbioportal_{STUDY}_{label}_{GENE_SYMBOL}.csv"
        if path.exists() and path.stat().st_size > 0:
            continue
        payload = {"entrezGeneIds": [entrez_gene_id], "sampleListId": sample_list_id}
        data = request_json(f"{API}/molecular-profiles/{profile_id}/molecular-data/fetch?projection=DETAILED", payload)
        rows = []
        for item in data:
            gene = item.get("gene") or {}
            rows.append(
                {
                    "source": "cBioPortal",
                    "studyId": item.get("studyId", STUDY),
                    "profile_label": label,
                    "molecularProfileId": item.get("molecularProfileId", profile_id),
                    "sampleId": item.get("sampleId", ""),
                    "patientId": item.get("patientId", ""),
                    "entrezGeneId": item.get("entrezGeneId", entrez_gene_id),
                    "hugoGeneSymbol": gene.get("hugoGeneSymbol", GENE_SYMBOL),
                    "value": item.get("value", ""),
                }
            )
        write_rows(
            path,
            rows,
            ["source", "studyId", "profile_label", "molecularProfileId", "sampleId", "patientId", "entrezGeneId", "hugoGeneSymbol", "value"],
        )


def fetch_mutations(entrez_gene_id: int):
    path = RAW / f"cbioportal_{STUDY}_mutations_{GENE_SYMBOL}.csv"
    if path.exists() and path.stat().st_size > 0:
        return
    payload = {"entrezGeneIds": [entrez_gene_id], "sampleListId": MUTATION_SAMPLE_LIST}
    data = request_json(f"{API}/molecular-profiles/{MUTATION_PROFILE}/mutations/fetch?projection=DETAILED", payload, timeout=60)
    rows = []
    for item in data:
        rows.append(
            {
                "source": "cBioPortal",
                "studyId": item.get("studyId", STUDY),
                "molecularProfileId": item.get("molecularProfileId", MUTATION_PROFILE),
                "sampleId": item.get("sampleId", ""),
                "patientId": item.get("patientId", ""),
                "entrezGeneId": item.get("entrezGeneId", entrez_gene_id),
                "hugoGeneSymbol": GENE_SYMBOL,
                "mutationType": item.get("mutationType", ""),
                "proteinChange": item.get("proteinChange", ""),
                "variantType": item.get("variantType", ""),
                "keyword": item.get("keyword", ""),
            }
        )
    write_rows(
        path,
        rows,
        ["source", "studyId", "molecularProfileId", "sampleId", "patientId", "entrezGeneId", "hugoGeneSymbol", "mutationType", "proteinChange", "variantType", "keyword"],
    )


def fetch_methylation_meta() -> list[dict]:
    cache = RAW / f"cbioportal_{STUDY}_methylation_hm450_meta.json"
    if cache.exists() and cache.stat().st_size > 0:
        data = json.loads(cache.read_text(encoding="utf-8"))
    else:
        data = request_json(f"{API}/generic-assay-meta/{METHYLATION_PROFILE}?projection=DETAILED", timeout=240)
        cache.write_text(json.dumps(data), encoding="utf-8")
    rows = []
    for item in data:
        props = item.get("genericEntityMetaProperties") or {}
        name = props.get("NAME", "")
        desc = props.get("DESCRIPTION", "")
        transcript = props.get("TRANSCRIPT_ID", "")
        text = ";".join([name, desc, transcript]).upper()
        if any(alias in text for alias in GENE_ALIASES):
            rows.append(
                {
                    "stableId": item.get("stableId", ""),
                    "name": name,
                    "description": desc,
                    "transcript_id": transcript,
                    "is_tss_probe": str(("TSS200" in desc.upper()) or ("TSS1500" in desc.upper())),
                    "alias_hit": ";".join(sorted(alias for alias in GENE_ALIASES if alias in text)),
                }
            )
    write_rows(
        RAW / f"cbioportal_{STUDY}_methylation_hm450_{GENE_SYMBOL}_probe_metadata.csv",
        rows,
        ["stableId", "name", "description", "transcript_id", "is_tss_probe", "alias_hit"],
    )
    return rows


def fetch_methylation_data(probe_rows: list[dict]):
    path = RAW / f"cbioportal_{STUDY}_methylation_hm450_{GENE_SYMBOL}_probes.csv"
    if path.exists() and path.stat().st_size > 0:
        return
    stable_ids = [row["stableId"] for row in probe_rows if row.get("stableId")]
    all_rows = []
    for i in range(0, len(stable_ids), 20):
        chunk = stable_ids[i : i + 20]
        payload = {"sampleListId": METHYLATION_SAMPLE_LIST, "genericAssayStableIds": chunk}
        data = request_json(f"{API}/generic_assay_data/{METHYLATION_PROFILE}/fetch?projection=DETAILED", payload, timeout=120)
        for item in data:
            all_rows.append(
                {
                    "source": "cBioPortal",
                    "studyId": item.get("studyId", STUDY),
                    "molecularProfileId": item.get("molecularProfileId", METHYLATION_PROFILE),
                    "sampleId": item.get("sampleId", ""),
                    "patientId": item.get("patientId", ""),
                    "stableId": item.get("stableId", item.get("genericAssayStableId", "")),
                    "genericAssayStableId": item.get("genericAssayStableId", item.get("stableId", "")),
                    "value": item.get("value", ""),
                }
            )
    write_rows(path, all_rows, ["source", "studyId", "molecularProfileId", "sampleId", "patientId", "stableId", "genericAssayStableId", "value"])


def write_manifest(entrez_gene_id: int, probe_rows: list[dict]):
    manifest = [
        {"item": "study", "value": STUDY},
        {"item": "gene", "value": GENE_SYMBOL},
        {"item": "entrezGeneId", "value": str(entrez_gene_id)},
        {"item": "molecular_profiles", "value": ";".join(profile for profile, _ in PROFILES.values())},
        {"item": "mutation_profile", "value": MUTATION_PROFILE},
        {"item": "methylation_profile", "value": METHYLATION_PROFILE},
        {"item": "methylation_probe_count", "value": str(len(probe_rows))},
        {"item": "source_api", "value": API},
    ]
    write_rows(RAW / "tmem158_cbioportal_download_manifest.csv", manifest, ["item", "value"])


def main():
    entrez_gene_id = get_gene_id()
    fetch_molecular_data(entrez_gene_id)
    fetch_mutations(entrez_gene_id)
    probe_rows = fetch_methylation_meta()
    fetch_methylation_data(probe_rows)
    write_manifest(entrez_gene_id, probe_rows)
    print(f"Downloaded targeted TCGA/cBioPortal inputs for {GENE_SYMBOL}; methylation probes={len(probe_rows)}")


if __name__ == "__main__":
    main()
