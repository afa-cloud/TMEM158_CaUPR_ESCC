# TMEM158 Multi-Omics Regulation Context

Date: 2026-06-19 23:09:16 CST

## Purpose

This public-data layer checks whether TMEM158 expression or TAC_high state can be trivially explained by TCGA/cBioPortal CNV, methylation, or mutation context.

## Status

- Matched TCGA samples: 184.
- CNV values: 181.
- Methylation probes: 7.
- Mutation records: 0.

## Boundary

This layer is regulatory context only. It does not prove TMEM158 causality or protein-level mechanism.

## Key Files

- `04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv`
- `04_results/mutation_cnv_methylation/tmem158_cbioportal_cnv_counts.csv`
- `04_results/mutation_cnv_methylation/tmem158_cbioportal_methylation_probe_correlations.csv`
- `04_results/qc/tmem158_multiomics_regulation_status.csv`
- `05_figures/figure9_tmem158_multiomics_regulation.*`
