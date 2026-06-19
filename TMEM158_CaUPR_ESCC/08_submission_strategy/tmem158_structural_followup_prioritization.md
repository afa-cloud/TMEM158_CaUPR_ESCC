# TMEM158/TAC_high Structural Follow-up Prioritization

Generated: 2026-06-19 23:25:01

## Bottom Line

The strongest structure/assay follow-up candidates are ECM-integrin bridges, led by POSTN->ITGA5, followed by POSTN-integrins, FN1->ITGA5 and selected collagen-integrin pairs. MIF->CXCR4 is a secondary receptor-state candidate. These are priorities for defined-partner co-modelling and experimental validation, not evidence that physical communication or TMEM158 binding has occurred.

## Top Priorities

| Rank | Candidate | Tier | Score | Evidence | Recommended Follow-up |
|---|---|---|---|---|---|
| 1 | POSTN->ITGA5 | high | 1.0 | delta=0.921; pair FDR=0.033; CAF rho=0.885/FDR=5.24e-19; fibroblast-signature rho=0.853/FDR=4.37e-16; PERK-CAF ecology rho=0.501/FDR=5.43e-04 | defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays |
| 2 | FN1->ITGA5 | high | 0.9283 | delta=0.653; pair FDR=0.042; CAF rho=0.839/FDR=2.33e-15; fibroblast-signature rho=0.826/FDR=1.96e-14; PERK-CAF ecology rho=0.437/FDR=0.003 | defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays |
| 3 | POSTN->ITGB3 | high | 0.894 | delta=0.570; pair FDR=0.039; CAF rho=0.801/FDR=2.06e-13; fibroblast-signature rho=0.762/FDR=1.87e-11; PERK-CAF ecology rho=0.491/FDR=7.07e-04 | defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays |
| 4 | COL1A1->ITGA1 | high | 0.877 | delta=0.529; pair FDR=0.073; CAF rho=0.817/FDR=3.66e-14; fibroblast-signature rho=0.793/FDR=9.95e-13; PERK-CAF ecology rho=0.570/FDR=9.63e-05 | module-level structural follow-up; collagen multimer context makes biochemical and spatial validation more important than single-pair modelling |
| 5 | POSTN->ITGB1 | high | 0.8671 | delta=0.634; pair FDR=0.088; CAF rho=0.649/FDR=1.01e-07; fibroblast-signature rho=0.644/FDR=1.44e-07; PERK-CAF ecology rho=0.302/FDR=0.044 | defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays |
| 6 | COL3A1->ITGA1 | high | 0.8453 | delta=0.405; pair FDR=0.088; CAF rho=0.825/FDR=1.40e-14; fibroblast-signature rho=0.787/FDR=1.54e-12; PERK-CAF ecology rho=0.562/FDR=9.63e-05 | module-level structural follow-up; collagen multimer context makes biochemical and spatial validation more important than single-pair modelling |
| 7 | POSTN->ITGAV | high | 0.8334 | delta=0.480; pair FDR=0.039; CAF rho=0.680/FDR=1.59e-08; fibroblast-signature rho=0.646/FDR=1.36e-07; PERK-CAF ecology rho=0.417/FDR=0.004 | defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays |
| 8 | COL1A2->ITGA1 | high | 0.8321 | delta=0.373; pair FDR=0.083; CAF rho=0.811/FDR=6.32e-14; fibroblast-signature rho=0.792/FDR=9.95e-13; PERK-CAF ecology rho=0.502/FDR=5.43e-04 | module-level structural follow-up; collagen multimer context makes biochemical and spatial validation more important than single-pair modelling |
| 9 | FN1->ITGB3 | high | 0.8094 | delta=0.336; pair FDR=0.088; CAF rho=0.735/FDR=2.40e-10; fibroblast-signature rho=0.718/FDR=9.84e-10; PERK-CAF ecology rho=0.426/FDR=0.004 | defined-partner AlphaFold Server co-modelling or docking as a hypothesis generator; prioritize orthogonal proximity, spatial co-expression and integrin-activation assays |
| 10 | COL1A1->ITGB1 | high | 0.7776 | delta=0.271; pair FDR=0.092; CAF rho=0.712/FDR=1.47e-09; fibroblast-signature rho=0.722/FDR=7.52e-10; PERK-CAF ecology rho=0.354/FDR=0.020 | module-level structural follow-up; collagen multimer context makes biochemical and spatial validation more important than single-pair modelling |

## Axis Context

- `ECM_integrin`: delta=0.269, FDR=0.044, boundary=TAC_high_higher_FDR; CAF rho=0.727, fibroblast-signature rho=0.745.
- `MIF_SPP1_axis`: delta=0.304, FDR=0.090, boundary=TAC_high_higher_FDR; CAF rho=0.294, fibroblast-signature rho=0.293.
- `Growth_factor`: delta=-0.201, FDR=0.027, boundary=not_FDR_TAC_high_higher; CAF rho=-0.706, fibroblast-signature rho=-0.701.
- `IL6_family`: delta=-0.414, FDR=0.009, boundary=not_FDR_TAC_high_higher; CAF rho=-0.586, fibroblast-signature rho=-0.511.

## How To Use This Layer

- Use POSTN/FN1/collagen-integrin candidates as the primary ECM-CAF-to-epithelial structural follow-up set.
- Use AlphaFold Server or related defined-partner tools as hypothesis generators only; ECM multimerization, integrin activation state and membrane context require orthogonal assays.
- Pair modelling should be followed by spatial co-expression, ligand/receptor perturbation, proximity labelling, co-IP/crosslinking-MS where feasible, and epithelial Ca2/UPR/proteostasis readouts.
- TMEM158 remains a membrane-protein entry point for proximity/localization testing; it is not currently a demonstrated binding partner of ECM, integrins or Ca2/UPR proteins.

## Machine QC

- `generated_at`: 2026-06-19 23:25:01 (info) - Local system timestamp
- `input_files_missing`: 0 (pass) - All required LR, axis and topology-boundary files are present
- `ranked_lr_pairs`: 82 (pass) - Ligand-receptor pairs ranked for follow-up
- `tac_high_higher_fdr_pairs`: 12 (pass) - FDR-positive TAC_high-higher LR pairs retained from the upstream bridge module
- `high_priority_pairs`: 11 (pass) - Pairs prioritized for defined-partner structural or proximity follow-up
- `top_structural_followup_pair`: POSTN->ITGA5 (pass) - Top candidate should remain evidence-led by effect size and CAF/fibroblast coupling
- `protein_topology_claim_clearance`: pass (pass_boundary) - TMEM158 topology is used for assayability context, not interaction proof
- `direct_interaction_claim`: not_made (pass) - The report explicitly avoids physical-interaction and causality claims
- `machine_structural_followup_clearance`: pass (pass) - Pass means prioritization is complete and claim boundaries are explicit

## Claim Boundary

This prioritization does not upgrade the public-data manuscript into a physical-interaction or causal-signalling study. It does not prove direct ER localization, TMEM158-ECM binding, TMEM158-integrin binding, CAF-to-epithelial ligand causality, receptor activation, Ca2/UPR protein binding or treatment response.

Machine structural follow-up clearance: `pass`.
