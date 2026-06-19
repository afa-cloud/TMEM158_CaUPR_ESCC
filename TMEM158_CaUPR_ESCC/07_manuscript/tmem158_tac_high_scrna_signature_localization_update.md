# TAC_high Single-Cell Signature Localization

This module tested whether TAC_high whole-transcriptome meta-signatures localize to epithelial tumour cells, fibroblasts/CAF, T cells or myeloid cells in independent GSE160269 single-cell matrices.

## Signature Construction

- `TAC_high_positive_top50`: top 50 positive genes from TAC_high-vs-other bulk meta-analysis.
- `TAC_high_positive_top200`: top 200 positive genes from TAC_high-vs-other bulk meta-analysis.
- `Core_CAF_interaction_positive_top200`: top 200 positive genes from the core-high by CAF-high interaction model; exploratory because interaction single-gene FDR was negative.

## Key Results

Unique signature genes extracted from raw GSE160269 matrices: 392.
Tumour samples scored across compartments: 60.
- `Core_CAF_interaction_positive_top200`: dominant compartment `Fibroblast` (median score 0.390).
- `TAC_high_positive_top200`: dominant compartment `Fibroblast` (median score 1.130).
- `TAC_high_positive_top50`: dominant compartment `Fibroblast` (median score 1.386).
Number of paired Fibroblast-vs-other tests with Fibroblast higher at FDR<0.10: 9.
Strongest TAC_high-vs-other sample-state contrast was `TAC_high_positive_top50` in `Fibroblast` (FDR=0.003, delta=0.371).

## Interpretation Boundary

This independent single-cell layer localizes TAC_high meta-signatures to compartments but does not prove cell-cell causality or TMEM158-driven transcription. If TAC_high signatures are strongest in fibroblasts, the manuscript should emphasize a CAF/ECM-dominant stress ecology rather than a tumour-cell-intrinsic programme.
