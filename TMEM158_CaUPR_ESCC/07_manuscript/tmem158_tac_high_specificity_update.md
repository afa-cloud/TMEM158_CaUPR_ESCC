# TAC_high State Specificity Update

This module tested whether the TAC_high signal exceeds component-only and random-state explanations.

## Outputs

- `04_results/validation/tmem158_tac_high_component_specificity_tests.csv`
- `04_results/validation/tmem158_tac_high_component_specificity_meta.csv`
- `04_results/validation/tmem158_tac_high_interaction_models.csv`
- `04_results/validation/tmem158_tac_high_permutation_summary.csv`
- `05_figures/figure12_tac_high_state_specificity.*`

## Key Interpretation

TAC_high was evaluated against cohort-preserving random labels with the same TAC_high sample counts in each dataset. This provides a statistical specificity layer for the rule-defined state and helps distinguish TAC_high from a generic TMEM158-only or CAF-only biomarker framing.

Permutation testing showed the strongest TAC_high specificity for `Drug_efflux_score` (observed weighted median delta=0.5426, empirical two-sided P=0.003498, empirical FDR=0.01049).

`Proteostasis_score` showed a directional but not FDR-confirmed specificity trend (delta=0.3494, empirical two-sided P=0.08146, empirical FDR=0.1222).

`Survival_score` was not random-label specific (delta=0.1472, empirical two-sided P=0.4343).

This updates the manuscript boundary: TAC_high is strongest as a transport/efflux-proteostasis transcriptional adaptation state. It should not be written as a validated clinical-survival subtype or therapy-resistance mechanism.

The module remains association-based and does not prove causal TMEM158 activity.
