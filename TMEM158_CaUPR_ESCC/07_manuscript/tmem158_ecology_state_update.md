# TMEM158-CaUPR-CAF Ecology State Update

Date: 2026-06-19 23:09:15 CST

## Purpose

This module tests whether the TMEM158 signal is stronger as a composite Ca2/UPR-CAF ecology state than as a single-gene association.

## State Definitions

- `TMEM158_Ca2_PERK_core`: within-cohort z(TMEM158), z(Ca2 axis), and z(PERK-bias).
- `TMEM158_PERK_CAF_ecology`: within-cohort z(TMEM158), z(PERK-bias), and z(CAF).
- `TMEM158_CaUPR_CAF_full`: within-cohort z(TMEM158), z(Ca2 axis), z(PERK-bias), and z(CAF).

## Interpretation Rule

Only effects supported across cohorts or by signed meta-analysis should be promoted to Results. Single-cohort effects remain exploratory.

## Key Results

- state_high_vs_low: TMEM158_Ca2_PERK_core_high_vs_low -> CAF_score; signed z=3.858, meta FDR=0.00149, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_Ca2_PERK_core_high_vs_low -> Drug_efflux_score; signed z=3.936, meta FDR=0.00149, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_Ca2_PERK_core_high_vs_low -> Survival_score; signed z=2.543, meta FDR=0.0286, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_CaUPR_CAF_full_high_vs_low -> Drug_efflux_score; signed z=3.591, meta FDR=0.00214, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_CaUPR_CAF_full_high_vs_low -> Proteostasis_score; signed z=3.639, meta FDR=0.00214, positive FDR cohorts=2, call=replicated_positive.
- state_high_vs_low: TMEM158_CaUPR_CAF_full_high_vs_low -> Survival_score; signed z=2.919, meta FDR=0.0114, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_PERK_CAF_ecology_high_vs_low -> CAF_score; signed z=3.443, meta FDR=0.003, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_PERK_CAF_ecology_high_vs_low -> Drug_efflux_score; signed z=3.287, meta FDR=0.00439, positive FDR cohorts=1, call=meta_positive_boundary.
- state_high_vs_low: TMEM158_PERK_CAF_ecology_high_vs_low -> Proteostasis_score; signed z=2.128, meta FDR=0.067, positive FDR cohorts=1, call=meta_positive_boundary.
- rule_subtype_TAC_high: TAC_high_vs_all_other_rule_subtypes -> Drug_efflux_score; signed z=4.079, meta FDR=0.000226, positive FDR cohorts=1, call=meta_positive_boundary.
- rule_subtype_TAC_high: TAC_high_vs_all_other_rule_subtypes -> Proteostasis_score; signed z=2.841, meta FDR=0.0113, positive FDR cohorts=2, call=replicated_positive.
- rule_subtype_TAC_high: TAC_high_vs_all_other_rule_subtypes -> Survival_score; signed z=2.49, meta FDR=0.0213, positive FDR cohorts=2, call=replicated_positive.

## Survival Boundary

- TCGA state/subtype clinical OS terms with FDR<0.10: 0.
- Clinical survival remains secondary; the reproducible signal is proteostasis/survival-score biology, not OS prognosis.

## Current Boundary

The module is designed to protect against overclaiming: if Ca2 direction remains inconsistent, the manuscript should describe branch-state remodeling and CAF-coupled stress ecology rather than uniform Ca2 activation.

## Key Files

- `04_results/validation/tmem158_ecology_state_tests.csv`
- `04_results/validation/tmem158_ecology_state_reproducibility.csv`
- `04_results/validation/tmem158_rule_ecology_subtype_tests.csv`
- `04_results/validation/tmem158_rule_ecology_subtype_reproducibility.csv`
- `04_results/validation/tmem158_rule_ecology_subtype_profile.csv`
- `04_results/immune/tmem158_scrna_rule_state_counts.csv`
- `04_results/immune/tmem158_scrna_rule_state_immune_tests.csv`
- `04_results/validation/tmem158_tcga_ecology_subtypes.csv`
- `04_results/survival/tmem158_ecology_state_survival.csv`
- `04_results/qc/tmem158_submission_gap_after_subtype.csv`
- `05_figures/figure6_tmem158_ecology_state_validation.*`
- `05_figures/figure7_rule_tmem158_ecology_subtypes.*`
- `05_figures/figure8_tcga_kmeans_state_architecture.*`
- `05_figures/figure10_scrna_tac_high_immune_boundary.*`
