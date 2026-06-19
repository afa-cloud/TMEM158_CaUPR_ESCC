# CAF-adjusted TAC_high Programme Update

This module tests whether the TAC_high programme is fully explained by continuous CAF abundance or whether axis-linked residual signals remain after stromal adjustment.

## Outputs

- `04_results/validation/tmem158_stromal_adjusted_score_contrasts.csv`
- `04_results/validation/tmem158_stromal_adjusted_score_meta.csv`
- `04_results/validation/tmem158_stromal_adjusted_score_models.csv`
- `04_results/transcriptome/tmem158_stromal_adjusted_meta_differential_genes.csv`
- `04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv`
- `05_figures/figure22_stromal_adjusted_tac_score_specificity.*`
- `05_figures/figure23_stromal_adjusted_tac_transcriptome.*`

## Key Interpretation

The CAF-adjusted limma model completed in 4 cohorts and tested 12380 genes across 238 tumour samples.

After adjustment for continuous CAF score, the transcriptome layer detected 1944 positive and 672 negative meta-FDR<0.10 genes. The top overall CAF-adjusted gene was `CHST7`, and the top positive gene was `CHST7`.

Custom ER proteostasis FDR=0.2897, drug-efflux/transport FDR=0.2544, and CAF/ECM FDR=0.3737 after CAF adjustment.

At the score level, TAC_high vs CAF_only after CAF residualization showed Proteostasis meta-FDR=0.4101 and Drug-efflux meta-FDR=0.3324.

Continuous core-axis effects adjusted for CAF showed Proteostasis meta-FDR=0.5265 and Drug-efflux meta-FDR=0.004347.

This layer should be written as a stromal-confounding stress test. It can support a CAF-coupled axis-state interpretation if residual signals remain, but it cannot prove tumour-cell-intrinsic causality.
