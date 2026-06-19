#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import math
from pathlib import Path

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


BRANCH = Path(__file__).resolve().parents[2]
PROJECT = BRANCH.parent
SOURCE_RAW = PROJECT / "SMIM14_CaUPR_ESCC" / "data" / "raw" / "scrna_gse160269"
OUT = BRANCH / "04_results" / "ligand_receptor"
LOGS = BRANCH / "logs"
OUT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOGS / "tmem158_tac_high_caf_epi_lr_extract.log"

FILES = {
    "Epithelial": {
        "matrix": SOURCE_RAW / "GSE160269_UMI_matrix_Epithelia.txt.gz",
        "cells": SOURCE_RAW / "GSE160269_CD45neg_cells.txt.gz",
    },
    "Fibroblast": {
        "matrix": SOURCE_RAW / "GSE160269_UMI_matrix_Fibroblast.txt.gz",
        "cells": SOURCE_RAW / "GSE160269_CD45neg_cells.txt.gz",
    },
}

TARGET_GENES = sorted({
    "POSTN", "COL1A1", "COL1A2", "COL3A1", "COL6A1", "COL6A2", "COL6A3",
    "FN1", "SPP1", "THBS1", "THBS2", "TNC", "LAMC1", "LAMB1", "LAMA4",
    "TGFB1", "TGFB2", "TGFB3", "INHBA", "IL6", "LIF", "OSM", "CXCL12",
    "CCL2", "MIF", "VEGFA", "HGF", "FGF2", "FGF7", "PDGFA", "PDGFB",
    "GAS6", "WNT5A", "JAG1",
    "ITGAV", "ITGB1", "ITGB3", "ITGA1", "ITGA2", "ITGA5", "ITGA6",
    "ITGA9", "ITGB4", "CD44", "CD47", "TGFBR1", "TGFBR2", "TGFBR3",
    "ACVR1B", "ACVR2A", "IL6R", "IL6ST", "LIFR", "OSMR", "CXCR4",
    "ACKR3", "CCR2", "CD74", "KDR", "FLT1", "NRP1", "MET", "FGFR1",
    "FGFR2", "PDGFRA", "PDGFRB", "AXL", "FZD2", "FZD5", "ROR2",
    "NOTCH1", "NOTCH2",
})


def log(*parts: object) -> None:
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_cell_metadata(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing GSE160269 cell metadata: {path}")
    out: dict[str, dict[str, str]] = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().strip().split()
        for line in handle:
            parts = line.strip().split()
            if len(parts) < len(header):
                continue
            row = dict(zip(header, parts))
            if "cell" in row:
                out[row["cell"]] = row
    return out


def split_gene_values(line: str) -> tuple[str, str]:
    if "\t" in line:
        gene, values = line.rstrip("\n").split("\t", 1)
    else:
        parts = line.rstrip("\n").split(maxsplit=1)
        gene = parts[0]
        values = parts[1] if len(parts) > 1 else ""
    return gene.strip().upper(), values


def parse_values(text: str):
    if np is not None:
        return np.fromstring(text.strip(), sep=" ", dtype=np.float32)
    return [float(x) for x in text.strip().split()]


def zeros(n: int):
    if np is not None:
        return np.zeros(n, dtype=np.float32)
    return [0.0] * n


def add_in_place(total, arr) -> None:
    if np is not None:
        total += arr
    else:
        for i, value in enumerate(arr):
            total[i] += value


def condition_from_sample(sample: str) -> str:
    if sample.endswith("N"):
        return "Adjacent_normal"
    if sample.endswith("T"):
        return "Tumor"
    return "Unknown"


def parse_compartment(compartment: str, meta_cache: dict[Path, dict[str, dict[str, str]]]):
    spec = FILES[compartment]
    matrix_path = spec["matrix"]
    cells_path = spec["cells"]
    if not matrix_path.exists():
        raise FileNotFoundError(f"Missing GSE160269 matrix: {matrix_path}")
    if not cells_path.exists():
        raise FileNotFoundError(f"Missing GSE160269 metadata: {cells_path}")
    if cells_path not in meta_cache:
        meta_cache[cells_path] = read_cell_metadata(cells_path)
    cell_meta = meta_cache[cells_path]

    with gzip.open(matrix_path, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n")
        cells = header.split("\t") if "\t" in header else header.split()
        n_cells = len(cells)
        lib_size = zeros(n_cells)
        target_counts = {gene: zeros(n_cells) for gene in TARGET_GENES}
        observed = {gene: False for gene in TARGET_GENES}
        rows = 0
        for line in handle:
            if not line.strip():
                continue
            gene, values = split_gene_values(line)
            arr = parse_values(values)
            if len(arr) != n_cells:
                log("skip row", compartment, gene, len(arr), "expected", n_cells)
                continue
            add_in_place(lib_size, arr)
            if gene in target_counts:
                target_counts[gene] = arr.copy() if np is not None else list(arr)
                observed[gene] = True
            rows += 1
            if rows % 5000 == 0:
                log(compartment, "processed rows", rows)
    log(compartment, "processed rows", rows, "cells", n_cells)

    samples = []
    for cell in cells:
        meta = cell_meta.get(cell, {})
        samples.append(meta.get("sample") or cell.split("-")[0])
    unique_samples = sorted(set(samples))
    sample_index = {sample: idx for idx, sample in enumerate(unique_samples)}

    if np is not None:
        codes = np.array([sample_index[s] for s in samples], dtype=np.int32)
        n_per_sample = np.bincount(codes, minlength=len(unique_samples)).astype(float)
        lib = lib_size.astype(np.float32)
    else:
        codes = [sample_index[s] for s in samples]
        n_per_sample = [0.0] * len(unique_samples)
        for code in codes:
            n_per_sample[code] += 1.0
        lib = lib_size

    mean_rows = []
    for gene in TARGET_GENES:
        counts = target_counts[gene]
        if np is not None:
            with np.errstate(divide="ignore", invalid="ignore"):
                logcpm = np.log1p(np.divide(counts, lib, out=np.zeros_like(counts), where=lib > 0) * 10000.0)
            sums = np.bincount(codes, weights=logcpm, minlength=len(unique_samples))
            positive = np.bincount(codes, weights=(counts > 0).astype(float), minlength=len(unique_samples))
            n_values = n_per_sample
        else:
            logcpm = [
                math.log1p((counts[i] / lib[i]) * 10000.0) if lib[i] > 0 else 0.0
                for i in range(n_cells)
            ]
            sums = [0.0] * len(unique_samples)
            positive = [0.0] * len(unique_samples)
            for i, code in enumerate(codes):
                sums[code] += logcpm[i]
                positive[code] += 1.0 if counts[i] > 0 else 0.0
            n_values = n_per_sample

        for idx, sample in enumerate(unique_samples):
            n = float(n_values[idx])
            mean_rows.append({
                "sample": sample,
                "condition": condition_from_sample(sample),
                "compartment": compartment,
                "n_cells": int(n),
                "gene": gene,
                "mean_log1p_cp10k": float(sums[idx]) / n if n > 0 else 0.0,
                "pct_positive": float(positive[idx]) / n if n > 0 else 0.0,
                "observed": bool(observed[gene]),
            })

    coverage_rows = [
        {"compartment": compartment, "gene": gene, "observed": bool(observed[gene])}
        for gene in TARGET_GENES
    ]
    status = {
        "compartment": compartment,
        "matrix": matrix_path.name,
        "cells": cells_path.name,
        "n_cells": n_cells,
        "n_samples": len(unique_samples),
        "n_tumor_samples": sum(1 for sample in unique_samples if condition_from_sample(sample) == "Tumor"),
        "n_normal_samples": sum(1 for sample in unique_samples if condition_from_sample(sample) == "Adjacent_normal"),
        "matrix_rows_processed": rows,
        "target_genes_requested": len(TARGET_GENES),
        "target_genes_observed": sum(1 for x in observed.values() if x),
    }
    return mean_rows, coverage_rows, status


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    meta_cache: dict[Path, dict[str, dict[str, str]]] = {}
    mean_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    status_rows: list[dict[str, object]] = []
    for compartment in ["Epithelial", "Fibroblast"]:
        comp_means, comp_cov, comp_status = parse_compartment(compartment, meta_cache)
        mean_rows.extend(comp_means)
        coverage_rows.extend(comp_cov)
        status_rows.append(comp_status)

    write_csv(
        OUT / "tmem158_tac_high_caf_epi_lr_gene_means.csv",
        mean_rows,
        ["sample", "condition", "compartment", "n_cells", "gene", "mean_log1p_cp10k", "pct_positive", "observed"],
    )
    write_csv(
        OUT / "tmem158_tac_high_caf_epi_lr_gene_coverage.csv",
        coverage_rows,
        ["compartment", "gene", "observed"],
    )
    write_csv(
        OUT / "tmem158_tac_high_caf_epi_lr_extract_status.csv",
        status_rows,
        ["compartment", "matrix", "cells", "n_cells", "n_samples", "n_tumor_samples",
         "n_normal_samples", "matrix_rows_processed", "target_genes_requested", "target_genes_observed"],
    )
    log("wrote", len(mean_rows), "gene mean rows")


if __name__ == "__main__":
    main()
