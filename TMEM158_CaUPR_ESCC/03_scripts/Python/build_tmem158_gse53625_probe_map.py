#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path


BRANCH = Path(__file__).resolve().parents[2]
WORKSPACE = BRANCH.parent
SOURCE = WORKSPACE / "SMIM14_CaUPR_ESCC"

RAW_AGILENT = SOURCE / "data" / "raw" / "GSM1296956_GSE53625_raw.txt.gz"
EXTERNAL_DIR = SOURCE / "data" / "external"
OUT_MAP = BRANCH / "02_data" / "processed" / "gse53625_tmem158_probe_gene_map.csv"
OUT_STATUS = BRANCH / "04_results" / "qc" / "tmem158_gse53625_probe_mapping_status.csv"

FASTA_SPECS = {
    "GENCODE_v19": (
        EXTERNAL_DIR / "gencode.v19.pc_transcripts.fa.gz",
        "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.pc_transcripts.fa.gz",
    ),
    "GENCODE_v36": (
        EXTERNAL_DIR / "gencode.v36.pc_transcripts.fa.gz",
        "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.pc_transcripts.fa.gz",
    ),
}

TARGET_GROUPS = {
    "lead_candidate": ["TMEM158"],
    "ca2_axis": ["STIM1", "ORAI1", "ATP2A2", "ITPR1", "ITPR2", "ITPR3"],
    "upr_perk": ["EIF2AK3", "ATF4", "DDIT3"],
    "upr_ire1_atf6": ["ERN1", "XBP1", "ATF6"],
    "caf_ecm": ["ACTA2", "FAP", "COL1A1", "COL1A2", "COL3A1", "COL5A1", "COL6A1", "CXCL12", "TAGLN", "PDPN", "DCN"],
    "proteostasis": ["HSPA5", "HSP90B1", "PDIA4", "DNAJB9", "HERPUD1"],
    "survival": ["BIRC5", "BCL2", "BCL2L1", "MCL1"],
    "drug_efflux": ["ABCC1", "ABCB1", "ABCG2", "ABCB6"],
    "ecm_integrin_bridge": [
        "POSTN", "COL6A3", "COL6A2", "SULF1", "FN1", "ITGA5", "ITGB1",
        "ITGAV", "ITGB3", "MIF", "CXCR4", "INHBA", "ACVR2A",
    ],
    "caf_adjusted_residual_stress": [
        "CHST7", "PTDSS1", "MAFG", "NFE2L2", "TALDO1", "OSGIN1", "TOMM22",
        "BDNF", "HK1", "SPRYD7", "WNT5A", "TUFT1", "DUSP14", "SCAMP1",
        "ADM", "GSTO1", "SLC3A2",
    ],
}


def target_genes() -> list[str]:
    seen: set[str] = set()
    genes: list[str] = []
    for values in TARGET_GROUPS.values():
        for gene in values:
            if gene not in seen:
                genes.append(gene)
                seen.add(gene)
    return genes


def gene_groups(gene: str) -> str:
    groups = [name for name, values in TARGET_GROUPS.items() if gene in values]
    return ";".join(groups)


def ensure_dirs() -> None:
    OUT_MAP.parent.mkdir(parents=True, exist_ok=True)
    OUT_STATUS.parent.mkdir(parents=True, exist_ok=True)
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)


def download_if_missing(path: Path, url: str) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    print(f"Downloading {url}", file=sys.stderr)
    urllib.request.urlretrieve(url, path)


def normalize_seq(seq: str) -> str:
    seq = re.sub(r"\s+", "", (seq or "").upper())
    if not seq or re.search(r"[^ACGT]", seq):
        return ""
    return seq


def revcomp(seq: str) -> str:
    return seq.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def parse_agilent_features(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing raw Agilent file: {path}")

    rows: list[dict[str, str]] = []
    with gzip.open(path, "rt", errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header: list[str] | None = None
        for parts in reader:
            if not parts:
                continue
            if parts[0] == "FEATURES":
                header = parts[1:]
                continue
            if header is None or parts[0] != "DATA":
                continue
            values = parts[1:]
            if len(values) < len(header):
                values += [""] * (len(header) - len(values))
            row = dict(zip(header, values))
            seq = normalize_seq(row.get("Sequence", ""))
            if len(seq) >= 25:
                row["Sequence"] = seq
                rows.append(row)
    return rows


def fasta_gene_symbol(header: str) -> str:
    text = header[1:] if header.startswith(">") else header
    parts = text.split("|")
    if len(parts) >= 6 and parts[5]:
        return parts[5].strip()
    match = re.search(r"(?:gene_name|gene_symbol)[:=]([A-Za-z0-9_.-]+)", text)
    if match:
        return match.group(1).strip()
    return ""


def iter_target_transcripts(path: Path, target_set: set[str]):
    with gzip.open(path, "rt") as handle:
        header = ""
        seq_parts: list[str] = []
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if header:
                    gene = fasta_gene_symbol(header)
                    if gene in target_set:
                        yield gene, "".join(seq_parts).upper()
                header = line
                seq_parts = []
            else:
                seq_parts.append(line.strip())
        if header:
            gene = fasta_gene_symbol(header)
            if gene in target_set:
                yield gene, "".join(seq_parts).upper()


def build_probe_lookup(features: list[dict[str, str]]):
    lookup: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(features):
        lookup[row["Sequence"]].append(idx)
    lengths = sorted({len(seq) for seq in lookup})
    return lookup, lengths


def match_fasta(version: str, fasta_path: Path, features: list[dict[str, str]], lookup, lengths):
    matches: dict[tuple[str, str], dict[str, set[str] | str]] = {}
    targets = set(target_genes())
    for gene, transcript in iter_target_transcripts(fasta_path, targets):
        transcript = normalize_seq(transcript)
        if not transcript:
            continue
        for orientation, seq in [("forward", transcript), ("reverse_complement", revcomp(transcript))]:
            n = len(seq)
            for k in lengths:
                if k > n:
                    continue
                seen_kmers: set[str] = set()
                for start in range(0, n - k + 1):
                    kmer = seq[start : start + k]
                    if kmer in seen_kmers:
                        continue
                    seen_kmers.add(kmer)
                    for feature_idx in lookup.get(kmer, []):
                        feature = features[feature_idx]
                        key = (feature["FeatureNum"], gene)
                        if key not in matches:
                            matches[key] = {
                                "FeatureNum": feature["FeatureNum"],
                                "gene_symbol": gene,
                                "target_groups": gene_groups(gene),
                                "annotation_versions": set(),
                                "orientations": set(),
                                "ProbeName": feature.get("ProbeName", ""),
                                "GeneName": feature.get("GeneName", ""),
                                "SystematicName": feature.get("SystematicName", ""),
                                "Sequence": feature.get("Sequence", ""),
                            }
                        matches[key]["annotation_versions"].add(version)  # type: ignore[index]
                        matches[key]["orientations"].add(orientation)  # type: ignore[index]
    return matches


def write_outputs(features: list[dict[str, str]], all_matches: dict[tuple[str, str], dict[str, set[str] | str]]) -> None:
    rows = []
    for key in sorted(all_matches):
        item = all_matches[key]
        rows.append(
            {
                "FeatureNum": item["FeatureNum"],
                "gene_symbol": item["gene_symbol"],
                "target_groups": item["target_groups"],
                "annotation_version": ";".join(sorted(item["annotation_versions"])),  # type: ignore[arg-type]
                "orientation": ";".join(sorted(item["orientations"])),  # type: ignore[arg-type]
                "ProbeName": item["ProbeName"],
                "GeneName": item["GeneName"],
                "SystematicName": item["SystematicName"],
                "Sequence": item["Sequence"],
            }
        )

    with OUT_MAP.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "FeatureNum",
                "gene_symbol",
                "target_groups",
                "annotation_version",
                "orientation",
                "ProbeName",
                "GeneName",
                "SystematicName",
                "Sequence",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    counts = defaultdict(int)
    versions = defaultdict(set)
    for row in rows:
        counts[row["gene_symbol"]] += 1
        for version in row["annotation_version"].split(";"):
            versions[row["gene_symbol"]].add(version)

    status_rows = []
    for gene in target_genes():
        status_rows.append(
            {
                "gene_symbol": gene,
                "target_groups": gene_groups(gene),
                "requested": "yes",
                "matched_probe_features": counts.get(gene, 0),
                "matched": "yes" if counts.get(gene, 0) > 0 else "no",
                "annotation_versions": ";".join(sorted(versions.get(gene, []))),
                "method": "probe_sequence_reannotation_with_GENCODE_v19_v36_pc_transcripts",
                "raw_probe_features_with_sequence": len(features),
                "source_raw_agilent_file": str(RAW_AGILENT),
            }
        )

    with OUT_STATUS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(status_rows[0].keys()))
        writer.writeheader()
        writer.writerows(status_rows)


def main() -> int:
    ensure_dirs()
    if not RAW_AGILENT.exists():
        raise FileNotFoundError(f"GSE53625 raw Agilent sample is required: {RAW_AGILENT}")

    for path, url in FASTA_SPECS.values():
        download_if_missing(path, url)

    features = parse_agilent_features(RAW_AGILENT)
    lookup, lengths = build_probe_lookup(features)

    all_matches: dict[tuple[str, str], dict[str, set[str] | str]] = {}
    for version, (path, _url) in FASTA_SPECS.items():
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Missing FASTA after download attempt: {path}")
        version_matches = match_fasta(version, path, features, lookup, lengths)
        for key, value in version_matches.items():
            if key not in all_matches:
                all_matches[key] = value
            else:
                all_matches[key]["annotation_versions"].update(value["annotation_versions"])  # type: ignore[index,union-attr]
                all_matches[key]["orientations"].update(value["orientations"])  # type: ignore[index,union-attr]

    write_outputs(features, all_matches)
    print(f"Wrote {OUT_MAP} with {len(all_matches)} probe-gene links")
    print(f"Wrote {OUT_STATUS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
