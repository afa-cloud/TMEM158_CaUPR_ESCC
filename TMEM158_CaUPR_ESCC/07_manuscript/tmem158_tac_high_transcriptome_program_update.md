# TAC_high Data-Driven Transcriptome Program

This module tested whether TAC_high has a data-driven transcriptomic program beyond the pre-specified score panels.

## Models

- `TAC_high_vs_other`: limma differential expression within each bulk cohort, followed by signed Stouffer meta-analysis.
- `Core_CAF_interaction`: limma model for `core_high * caf_high`; the interaction term asks whether the TAC_high quadrant exceeds additive core-high and CAF-high components.

## Key Results

Matched expression/state matrix: 12380 genes across 238 tumour samples.
TAC_high vs other completed in 4 cohorts; core-by-CAF interaction completed in 3 cohorts.
Top TAC_high-vs-other meta gene: `POSTN` (combined z=10.560, meta FDR=<0.001).
Top core-by-CAF interaction gene: `ADORA3` (combined z=-4.283, meta FDR=0.125).
Top positive TAC_high-vs-other pathway: `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` (delta mean z=3.744, FDR=<0.001).
Top positive interaction pathway: `REACTOME_TRANSLATION` (delta mean z=0.766, FDR=<0.001).

## Interpretation Boundary

This is a transcriptome-level association layer. It can support a data-driven stress-ecology program if pathway and gene-level results align, but it does not prove TMEM158 causality, drug resistance, protein-level UPR activation, or clinical treatment response.
