# Spatial Progression Source-Data Context Update

## Summary

A public Nature Communications 2023 ESCC spatial whole-transcriptome study was added as a source-data calibration layer. The available Source Data XLSX contains published graph-level DSP cell-deconvolution values, IF quantification and selected ROI marker genes, but not the complete WTA matrix. Therefore, this module does not directly rescore TMEM158 or TAC_high in spatial ROIs.

## Key Results

- Source data extraction completed from `natcomm2023_escc_spatial_source_data.xlsx`.
- Full WTA matrix in the public Source Data: FALSE; direct TAC_high spatial scoring: FALSE.
- ROI marker source table stage count: 1; it was retained for provenance but not used as a spatial progression validation panel.
- Fibroblast source-data delta ESCC-minus-NE: 3.297; stage-trend rho: 0.789; FDR: <0.001.
- alpha-SMA fibroblast IF delta ESCC-minus-NE: 13.891; stage-trend rho: 0.639; FDR: <0.001.
- M2 macrophage score delta ESCC-minus-NE: 0.018; stage-trend rho: 0.271; FDR: 0.080.

## Interpretation Boundary

This layer supports the broader biological plausibility of a fibroblast/CAF-rich ESCC progression context that is consistent with the TAC_high CAF/ECM interpretation. It is not a direct spatial validation of TMEM158, TAC_high, Ca2/UPR activation or ligand-receptor causality because the complete spatial WTA matrix is restricted and absent from the public Source Data.

