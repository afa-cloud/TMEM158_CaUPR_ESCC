#!/usr/bin/env python3
"""Extract TMEM158/TAC_high target pseudobulk summaries from GSE221561."""
from __future__ import annotations

import csv
import gzip
import io
import math
import mmap
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
SOURCE_PROJECT = PROJECT.parent / "SMIM14_CaUPR_ESCC"
RAW = SOURCE_PROJECT / "data" / "raw" / "gse221561"
PROCESSED = PROJECT / "02_data" / "processed"
TABLES = PROJECT / "04_results" / "gse221561"
LOGS = PROJECT / "logs"
for path in [PROCESSED, TABLES, LOGS]:
    path.mkdir(parents=True, exist_ok=True)

LOG_PATH = LOGS / "tmem158_gse221561_tac_target_extract.log"
GEO_FTP = "ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE221nnn/GSE221561/suppl"
RAW_TAR = RAW / "GSE221561_RAW.tar"
FILELIST = RAW / "filelist.txt"
METADATA_GZ = RAW / "GSE221561_metadata_celltype.csv.gz"
MIN_RAW_BYTES = 900_000_000
MIN_META_BYTES = 2_000_000
MIN_FILELIST_BYTES = 1_000

TARGET_GROUPS = {
    "lead_candidate": ["TMEM158", "CORO1C", "ATP2B4", "TMEM132A", "ABCC1"],
    "ca2_core": ["STIM1", "ORAI1", "ATP2A2", "ITPR1", "ITPR2", "ITPR3"],
    "upr": ["EIF2AK3", "ATF4", "DDIT3", "ERN1", "XBP1", "ATF6"],
    "proteostasis_biogenesis": ["HSPA5", "HSP90B1", "CANX", "CALR", "PDIA3", "PDIA4", "DNAJB9", "HERPUD1", "PPP1R15A", "SEL1L", "EDEM1", "SYVN1", "DERL3", "SEC61A1", "SRP54", "RPLP0", "RPS3", "NPM1", "MYC"],
    "transport_efflux": ["ABCC1", "ABCC2", "ABCC3", "ABCG2", "ABCB1", "SLC7A11", "GCLC", "GCLM", "GSR", "GPX1", "GPX8", "NQO1", "HMOX1", "TXN", "TXNRD1", "SOD2", "GSTP1"],
    "tac_high_meta_ecm": ["POSTN", "COL6A3", "COL1A2", "CHST7", "COL3A1", "FAP", "SULF1", "COL1A1", "COL6A2", "SPRY2", "MMP2", "MMP11", "ACTA2", "FN1", "VIM", "TAGLN", "LUM", "DCN", "COL5A1", "COL5A2"],
    "caf_ecm": ["COL1A1", "COL1A2", "COL3A1", "COL6A2", "COL6A3", "POSTN", "FAP", "ACTA2", "FN1", "TAGLN", "LUM", "DCN", "MMP2", "MMP11", "CXCL12", "TGFB1", "IL6"],
    "lr_bridge_ligand": ["POSTN", "COL1A1", "COL1A2", "COL3A1", "FN1", "MIF", "SPP1", "INHBA", "TGFB1", "CXCL12", "IL6", "VEGFA", "HGF", "FGF2", "PDGFA", "PDGFB", "WNT5A"],
    "lr_bridge_receptor": ["ITGA1", "ITGA2", "ITGA3", "ITGA5", "ITGAV", "ITGB1", "ITGB3", "CXCR4", "CD44", "CD74", "ACVR2A", "TGFBR1", "TGFBR2", "IL6R", "IL6ST", "KDR", "MET", "FGFR1", "PDGFRA", "FZD2", "FZD5"],
    "immune_boundary": ["PDCD1", "LAG3", "HAVCR2", "TOX", "TIGIT", "CTLA4", "CD8A", "CD8B", "GZMB", "PRF1", "NKG7", "IFNG", "FOXP3", "IL2RA", "CD163", "MRC1", "APOE", "CCL18", "IL10"],
}

ALIASES = {}


def log(*parts: object) -> None:
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def gzip_ok(path: Path) -> bool:
    gzip_bin = shutil.which("gzip")
    if gzip_bin is None:
        return True
    status = subprocess.call([gzip_bin, "-t", str(path)])
    log("gzip check", path.name, "status", status)
    return status == 0


def ensure_download(name: str, dest: Path, min_bytes: int, gzipped: bool = False) -> Path:
    if dest.exists() and dest.stat().st_size >= min_bytes and (not gzipped or gzip_ok(dest)):
        log("cached", dest.name, dest.stat().st_size)
        return dest
    curl = shutil.which("curl")
    if curl is None:
        raise RuntimeError("curl is required for GSE221561 downloads")
    url = f"{GEO_FTP}/{name}"
    for attempt in range(1, 11):
        status = subprocess.call([
            curl, "-L", "--fail", "--retry", "3", "-C", "-", "--ftp-pasv",
            "--connect-timeout", "20", "--speed-limit", "1024", "--speed-time", "180",
            "-o", str(dest), url,
        ])
        size = dest.stat().st_size if dest.exists() else 0
        ok = size >= min_bytes and (not gzipped or gzip_ok(dest))
        log("download", name, "attempt", attempt, "status", status, "bytes", size, "ok", ok)
        if ok:
            return dest
    raise RuntimeError(f"failed to download {name}")


def target_genes() -> list[str]:
    genes: set[str] = set()
    for members in TARGET_GROUPS.values():
        genes.update(g.upper() for g in members)
    genes.update(ALIASES.keys())
    genes.update(ALIASES.values())
    return sorted(genes)


def canonical_gene(symbol: str) -> str:
    up = symbol.strip().upper()
    return ALIASES.get(up, up)


def read_metadata(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    metadata: dict[str, dict[str, str]] = {}
    counts = defaultdict(int)
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cell_id = row.get("", "") or row.get("cell", "") or row.get("Cell", "")
            if not cell_id:
                continue
            row["cell_id"] = cell_id
            row["is_singlet"] = "TRUE" if row.get("scDblFinder.class", "").lower() in {"", "singlet"} else "FALSE"
            metadata[cell_id] = row
            counts["cells_total"] += 1
            counts[f"celltype_{row.get('Cell_type', 'Unknown')}"] += 1
            counts[f"library_{row.get('library_name', 'Unknown')}"] += 1
            counts[f"tissue_{row.get('Tissue_type', 'Unknown')}"] += 1
            counts[f"neoadjuvant_{row.get('Neoadjuvant', 'Unknown')}"] += 1
            if row["is_singlet"] == "TRUE":
                counts["singlet_cells"] += 1
    return metadata, dict(counts)


def read_gzip_lines_from_member(archive: mmap.mmap, member: dict[str, object]) -> list[str]:
    start = int(member["start"])
    end = int(member["end"])
    with gzip.GzipFile(fileobj=io.BytesIO(archive[start:end])) as gz:
        return [line.decode("utf-8", errors="replace").rstrip("\n") for line in gz]


def read_features(archive: mmap.mmap, member: dict[str, object], targets: set[str]) -> tuple[dict[int, str], dict[str, str]]:
    row_to_gene: dict[int, str] = {}
    observed: dict[str, str] = {}
    lines = read_gzip_lines_from_member(archive, member)
    for idx, line in enumerate(lines, start=1):
        parts = line.split("\t")
        candidates = []
        if len(parts) >= 2:
            candidates.append(parts[1])
        if parts:
            candidates.append(parts[0])
        for cand in candidates:
            gene = canonical_gene(cand)
            if gene in targets:
                row_to_gene[idx] = gene
                observed[gene] = cand
                break
    return row_to_gene, observed


def parse_matrix_targets(archive: mmap.mmap, member: dict[str, object], row_to_gene: dict[int, str], n_cells: int) -> dict[str, list[float]]:
    counts = {gene: [0.0] * n_cells for gene in sorted(set(row_to_gene.values()))}
    start = int(member["start"])
    end = int(member["end"])
    member_name = str(member["name"])
    with gzip.GzipFile(fileobj=io.BytesIO(archive[start:end])) as gz:
        dims_seen = False
        entries = 0
        target_entries = 0
        for raw in gz:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line or line.startswith("%"):
                continue
            if not dims_seen:
                dims_seen = True
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            row = int(parts[0])
            gene = row_to_gene.get(row)
            if gene is None:
                entries += 1
                continue
            col = int(parts[1]) - 1
            if 0 <= col < n_cells:
                counts[gene][col] += float(parts[2])
                target_entries += 1
            entries += 1
            if entries % 2_000_000 == 0:
                log(member_name, "entries", entries, "target_entries", target_entries)
    log(member_name, "target_entries", target_entries)
    return counts


def parse_members_from_filelist(archive: mmap.mmap) -> dict[str, dict[str, dict[str, object]]]:
    entries: list[dict[str, object]] = []
    with FILELIST.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.startswith("File\t"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            name = parts[1]
            hit = archive.find(name.encode("utf-8"))
            if hit < 0:
                log("filelist member not found in archive", name)
                continue
            entries.append({"name": name, "offset": hit, "listed_size": int(parts[3])})
    entries.sort(key=lambda x: int(x["offset"]))
    for i, entry in enumerate(entries):
        entry["start"] = int(entry["offset"]) + 512
        entry["end"] = int(entries[i + 1]["offset"]) if i + 1 < len(entries) else len(archive)
        entry["chunk_size"] = int(entry["end"]) - int(entry["start"])

    sample_members: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    pat = re.compile(r"(?P<gsm>GSM\d+)_(?P<library>[^_]+)_(?P<kind>barcodes|features|matrix)\.(?:tsv|mtx)\.gz$")
    for member in entries:
        name = Path(str(member["name"])).name
        m = pat.search(name)
        if not m:
            continue
        sample_members[m.group("library")][m.group("kind")] = member
    return dict(sample_members)


def add_group_cell(group_cells: dict[tuple[str, str, str], list[int]], row: dict[str, str], idx: int) -> None:
    library = row.get("library_name", "")
    cell_type = row.get("Cell_type", "Unknown") or "Unknown"
    cell_sub = row.get("Cell_type_sub", "Unknown") or "Unknown"
    group_cells[("Cell_type", library, cell_type)].append(idx)
    group_cells[("Cell_type_sub", library, cell_sub)].append(idx)


def group_meta_from_cells(rows: list[dict[str, str]]) -> dict[str, str]:
    def first(field: str) -> str:
        vals = [r.get(field, "") for r in rows if r.get(field, "")]
        return vals[0] if vals else ""

    return {
        "library_name": first("library_name"),
        "Tissue_type": first("Tissue_type"),
        "Neoadjuvant": first("Neoadjuvant"),
        "differentiation": first("differentiation"),
        "T_stage": first("T_stage"),
        "N_stage": first("N_stage"),
        "M_stage": first("M_stage"),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    ensure_download("GSE221561_metadata_celltype.csv.gz", METADATA_GZ, MIN_META_BYTES, gzipped=True)
    ensure_download("GSE221561_RAW.tar", RAW_TAR, MIN_RAW_BYTES, gzipped=False)

    metadata, meta_counts = read_metadata(METADATA_GZ)
    targets = set(target_genes())
    log("metadata cells", len(metadata), "targets", len(targets))

    long_rows: list[dict[str, object]] = []
    group_rows: list[dict[str, object]] = []
    coverage_counts = {gene: 0 for gene in sorted(targets)}
    coverage_observed_symbols: dict[str, set[str]] = defaultdict(set)
    sample_status: list[dict[str, object]] = []

    ensure_download("filelist.txt", FILELIST, MIN_FILELIST_BYTES, gzipped=False)

    with RAW_TAR.open("rb") as raw_handle:
        archive = mmap.mmap(raw_handle.fileno(), 0, access=mmap.ACCESS_READ)
        members = parse_members_from_filelist(archive)
        for library in sorted(members):
            trio = members[library]
            if not all(k in trio for k in ("barcodes", "features", "matrix")):
                sample_status.append({"library_name": library, "status": "missing_member", "cells": 0, "singlet_metadata_cells": 0, "groups": 0, "target_genes": 0, "note": "barcodes/features/matrix member missing"})
                continue
            try:
                barcodes = read_gzip_lines_from_member(archive, trio["barcodes"])
                cell_ids = [f"{library}_{barcode}" for barcode in barcodes]
                cell_meta = [metadata.get(cid) for cid in cell_ids]
                valid_indices = [i for i, row in enumerate(cell_meta) if row is not None and row.get("is_singlet") == "TRUE"]
                group_cells: dict[tuple[str, str, str], list[int]] = defaultdict(list)
                for idx in valid_indices:
                    add_group_cell(group_cells, cell_meta[idx], idx)  # type: ignore[arg-type]

                row_to_gene, observed = read_features(archive, trio["features"], targets)
                counts = parse_matrix_targets(archive, trio["matrix"], row_to_gene, len(barcodes))
            except Exception as exc:
                sample_status.append({
                    "library_name": library,
                    "status": "failed_member_parse",
                    "cells": 0,
                    "singlet_metadata_cells": 0,
                    "groups": 0,
                    "target_genes": 0,
                    "note": f"{type(exc).__name__}: {exc}",
                })
                log("sample", library, "failed", type(exc).__name__, exc)
                continue

            for gene, symbol in observed.items():
                coverage_counts[gene] += 1
                coverage_observed_symbols[gene].add(symbol)
            sample_status.append({
                "library_name": library,
                "status": "parsed",
                "cells": len(barcodes),
                "singlet_metadata_cells": len(valid_indices),
                "groups": len(group_cells),
                "target_genes": len(counts),
                "note": "",
            })
            log("sample", library, "cells", len(barcodes), "singlets", len(valid_indices), "groups", len(group_cells), "target_genes", len(counts))

            for (level, sample, group_name), indices in sorted(group_cells.items()):
                if not indices:
                    continue
                rows_for_group = [cell_meta[i] for i in indices if cell_meta[i] is not None]  # type: ignore[list-item]
                gm = group_meta_from_cells(rows_for_group)  # type: ignore[arg-type]
                cell_type = group_name if level == "Cell_type" else rows_for_group[0].get("Cell_type", "Unknown")  # type: ignore[index]
                cell_sub = group_name if level == "Cell_type_sub" else ""
                group_id = f"{level}|{sample}|{group_name}"
                group_rows.append({
                    "group_id": group_id,
                    "group_level": level,
                    "library_name": sample,
                    "group_name": group_name,
                    "Cell_type": cell_type,
                    "Cell_type_sub": cell_sub,
                    "n_cells": len(indices),
                    **gm,
                })
                for gene in sorted(targets):
                    arr = counts.get(gene)
                    if arr is None:
                        mean_counts = 0.0
                        mean_log1p = 0.0
                        detected = 0.0
                    else:
                        vals = [arr[i] for i in indices]
                        mean_counts = sum(vals) / len(vals)
                        mean_log1p = sum(math.log1p(v) for v in vals) / len(vals)
                        detected = sum(1 for v in vals if v > 0) / len(vals)
                    long_rows.append({
                        "group_id": group_id,
                        "group_level": level,
                        "library_name": sample,
                        "group_name": group_name,
                        "Cell_type": cell_type,
                        "Cell_type_sub": cell_sub,
                        "Tissue_type": gm["Tissue_type"],
                        "Neoadjuvant": gm["Neoadjuvant"],
                        "n_cells": len(indices),
                        "gene": gene,
                        "mean_log1p": f"{mean_log1p:.8f}",
                        "mean_counts": f"{mean_counts:.8f}",
                        "detection_fraction": f"{detected:.8f}",
                    })
        archive.close()

    long_fields = [
        "group_id", "group_level", "library_name", "group_name", "Cell_type", "Cell_type_sub",
        "Tissue_type", "Neoadjuvant", "n_cells", "gene", "mean_log1p", "mean_counts", "detection_fraction",
    ]
    group_fields = [
        "group_id", "group_level", "library_name", "group_name", "Cell_type", "Cell_type_sub", "n_cells",
        "Tissue_type", "Neoadjuvant", "differentiation", "T_stage", "N_stage", "M_stage",
    ]
    coverage_rows = []
    for group, genes in TARGET_GROUPS.items():
        for raw_gene in genes:
            gene = canonical_gene(raw_gene)
            coverage_rows.append({
                "requested_gene": raw_gene,
                "canonical_gene": gene,
                "target_group": group,
                "samples_with_feature": coverage_counts.get(gene, 0),
                "observed_symbols": ";".join(sorted(coverage_observed_symbols.get(gene, set()))),
                "covered": coverage_counts.get(gene, 0) > 0,
            })
    parsed_libraries = sum(1 for row in sample_status if row.get("status") == "parsed")
    failed_libraries = sum(1 for row in sample_status if row.get("status") != "parsed")
    status_rows = [
        {"item": "module_status", "value": "completed" if failed_libraries == 0 else "partial_completed"},
        {"item": "metadata_cells_total", "value": meta_counts.get("cells_total", 0)},
        {"item": "metadata_singlet_cells", "value": meta_counts.get("singlet_cells", 0)},
        {"item": "raw_tar_bytes", "value": RAW_TAR.stat().st_size if RAW_TAR.exists() else 0},
        {"item": "libraries_in_filelist", "value": len(sample_status)},
        {"item": "libraries_parsed", "value": parsed_libraries},
        {"item": "libraries_failed", "value": failed_libraries},
        {"item": "pseudobulk_groups", "value": len(group_rows)},
        {"item": "long_rows", "value": len(long_rows)},
    ]
    for key, value in sorted(meta_counts.items()):
        if key.startswith(("celltype_", "tissue_", "neoadjuvant_")):
            status_rows.append({"item": key, "value": value})

    write_csv(PROCESSED / "tmem158_gse221561_tac_target_pseudobulk_expression.csv", long_rows, long_fields)
    write_csv(PROCESSED / "tmem158_gse221561_tac_group_metadata.csv", group_rows, group_fields)
    write_csv(TABLES / "tmem158_gse221561_tac_target_gene_coverage.csv", coverage_rows, ["requested_gene", "canonical_gene", "target_group", "samples_with_feature", "observed_symbols", "covered"])
    write_csv(TABLES / "tmem158_gse221561_tac_extract_sample_status.csv", sample_status, ["library_name", "status", "cells", "singlet_metadata_cells", "groups", "target_genes", "note"])
    write_csv(TABLES / "tmem158_gse221561_tac_extract_status.csv", status_rows, ["item", "value"])
    log("wrote", len(long_rows), "long rows and", len(group_rows), "groups")


if __name__ == "__main__":
    main()
