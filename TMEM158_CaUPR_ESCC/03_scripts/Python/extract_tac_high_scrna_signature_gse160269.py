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
TRANSCRIPTOME = BRANCH / "04_results" / "transcriptome" / "tmem158_tac_high_meta_differential_genes.csv"
OUT = BRANCH / "04_results" / "scrna_signature"
LOGS = BRANCH / "logs"
OUT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOGS / "tmem158_tac_high_scrna_signature_extract.log"

FILES = {
    "Epithelial": {
        "matrix": SOURCE_RAW / "GSE160269_UMI_matrix_Epithelia.txt.gz",
        "cells": SOURCE_RAW / "GSE160269_CD45neg_cells.txt.gz",
    },
    "Fibroblast": {
        "matrix": SOURCE_RAW / "GSE160269_UMI_matrix_Fibroblast.txt.gz",
        "cells": SOURCE_RAW / "GSE160269_CD45neg_cells.txt.gz",
    },
    "Tcell": {
        "matrix": SOURCE_RAW / "GSE160269_UMI_matrix_Tcell.txt.gz",
        "cells": SOURCE_RAW / "GSE160269_CD45pos_cells.txt.gz",
    },
    "Myeloid": {
        "matrix": SOURCE_RAW / "GSE160269_UMI_matrix_Myeloid.txt.gz",
        "cells": SOURCE_RAW / "GSE160269_CD45pos_cells.txt.gz",
    },
}


def log(*parts: object) -> None:
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_signature_map() -> list[dict[str, object]]:
    if not TRANSCRIPTOME.exists():
        raise FileNotFoundError(f"Missing transcriptome meta table: {TRANSCRIPTOME}")
    with TRANSCRIPTOME.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    def select(model: str, signature: str, n: int) -> list[dict[str, object]]:
        kept = []
        for row in rows:
            try:
                z = float(row.get("combined_z", "nan"))
                p = float(row.get("meta_p", "nan"))
            except ValueError:
                continue
            if row.get("model") == model and math.isfinite(z) and z > 0 and math.isfinite(p):
                kept.append(row)
        kept.sort(key=lambda r: float(r["meta_p"]))
        out_rows = []
        for rank, row in enumerate(kept[:n], start=1):
            out_rows.append({
                "signature": signature,
                "model": model,
                "rank": rank,
                "gene": row["gene"].upper(),
                "weight": float(row["combined_z"]),
                "meta_p": row["meta_p"],
                "meta_FDR": row["meta_FDR"],
            })
        return out_rows

    sig_rows = []
    sig_rows.extend(select("TAC_high_vs_other", "TAC_high_positive_top50", 50))
    sig_rows.extend(select("TAC_high_vs_other", "TAC_high_positive_top200", 200))
    sig_rows.extend(select("Core_CAF_interaction", "Core_CAF_interaction_positive_top200", 200))
    if not sig_rows:
        raise RuntimeError("No positive TAC_high signature genes selected")
    return sig_rows


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


def to_list(arr) -> list[float]:
    if np is not None:
        return [float(x) for x in arr.tolist()]
    return [float(x) for x in arr]


def condition_from_sample(sample: str) -> str:
    if sample.endswith("N"):
        return "Adjacent_normal"
    if sample.endswith("T"):
        return "Tumor"
    return "Unknown"


def parse_compartment(compartment: str, target_genes: list[str], meta_cache: dict[Path, dict[str, dict[str, str]]]):
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
        target_counts = {gene: zeros(n_cells) for gene in target_genes}
        observed = {gene: False for gene in target_genes}
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
    for gene in target_genes:
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
        for gene in target_genes
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
        "target_genes_requested": len(target_genes),
        "target_genes_observed": sum(1 for x in observed.values() if x),
    }
    return mean_rows, coverage_rows, status


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    LOG_PATH.write_text("", encoding="utf-8")
    sig_rows = read_signature_map()
    sig_path = OUT / "tmem158_tac_high_scrna_signature_gene_map.csv"
    write_csv(sig_path, sig_rows, ["signature", "model", "rank", "gene", "weight", "meta_p", "meta_FDR"])
    target_genes = sorted({str(row["gene"]).upper() for row in sig_rows})
    log("selected signatures", len(sig_rows), "rows", len(target_genes), "unique genes")

    meta_cache: dict[Path, dict[str, dict[str, str]]] = {}
    all_means: list[dict[str, object]] = []
    all_cov: list[dict[str, object]] = []
    all_status: list[dict[str, object]] = []
    for compartment in ["Epithelial", "Fibroblast", "Tcell", "Myeloid"]:
        means, cov, status = parse_compartment(compartment, target_genes, meta_cache)
        all_means.extend(means)
        all_cov.extend(cov)
        all_status.append(status)

    write_csv(
        OUT / "tmem158_tac_high_scrna_signature_gene_means.csv",
        all_means,
        ["sample", "condition", "compartment", "n_cells", "gene", "mean_log1p_cp10k", "pct_positive", "observed"],
    )
    write_csv(
        OUT / "tmem158_tac_high_scrna_signature_gene_coverage.csv",
        all_cov,
        ["compartment", "gene", "observed"],
    )
    write_csv(
        OUT / "tmem158_tac_high_scrna_signature_extract_status.csv",
        all_status,
        ["compartment", "matrix", "cells", "n_cells", "n_samples", "n_tumor_samples",
         "n_normal_samples", "matrix_rows_processed", "target_genes_requested", "target_genes_observed"],
    )
    log("wrote outputs to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
